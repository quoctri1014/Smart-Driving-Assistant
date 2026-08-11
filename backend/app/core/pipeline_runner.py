import time
import logging
from typing import Optional
from modules.detector import VehicleDetector
from modules.tracker import SimpleTracker
from modules.zone_manager import ZoneManager
from modules.plate_reader import PlateReader
from modules.helmet_checker import HelmetChecker
from modules.collision_warning import CollisionWarning
from modules.speed_advisor import suggest_speed
from modules.sign_recognition import SignRecognition
import config as ai_config
from backend.app.schemas.detection_result import (
    DetectionResult, BoundingBox, VehicleDetection, 
    PlateDetection, HelmetViolation, SpeedAdvice, 
    CollisionWarning as CollisionWarningSchema, TrafficSign
)

logger = logging.getLogger(__name__)

class SharedAIModels:
    """Singleton pattern to load heavy stateless AI models only once."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedAIModels, cls).__new__(cls)
            logger.info("Loading Shared AI Models...")
            cls._instance.detector = VehicleDetector()
            cls._instance.plate_reader = PlateReader() if ai_config.ENABLE_LICENSE_PLATE else None
            cls._instance.helmet_checker = HelmetChecker() if ai_config.ENABLE_HELMET_CHECK else None
            cls._instance.sign_recognition = SignRecognition()
            logger.info("Shared AI Models loaded successfully.")
        return cls._instance

class PipelineSession:
    """Per-connection stateful pipeline session."""
    def __init__(self):
        self.models = SharedAIModels()
        self.tracker = SimpleTracker()
        self.zone_manager = ZoneManager() if ai_config.ENABLE_ZONE_COUNTING else None
        self.collision_warning = CollisionWarning() if ai_config.ENABLE_COLLISION_WARNING else None
        self.frame_idx = 0
        
    def _to_bbox(self, box) -> BoundingBox:
        return BoundingBox(x1=box[0], y1=box[1], x2=box[2], y2=box[3])
        
    def process_frame(self, frame, vehicle_speed: Optional[float] = None) -> DetectionResult:
        t_start = time.time()
        self.frame_idx += 1
        
        h, w = frame.shape[:2]
        if ai_config.RESIZE_WIDTH:
            import cv2
            scale = ai_config.RESIZE_WIDTH / w
            frame = cv2.resize(frame, (ai_config.RESIZE_WIDTH, int(h * scale)))
            h, w = frame.shape[:2]
            
        # 1. Detection
        detections = self.models.detector.detect(frame)
        det_pairs = [(d["box"], d["cls_name"]) for d in detections]
        
        # 2. Tracking
        tracks = self.tracker.update(det_pairs, self.frame_idx)
        vehicle_tracks = [t for t in tracks if t.cls_name != "person"]
        person_tracks = [t for t in tracks if t.cls_name == "person"]
        
        # 3. Zone Management
        if self.zone_manager:
            self.zone_manager.update(vehicle_tracks + person_tracks, w, h)
            
        # 4. Sign Recognition
        sign_info = self.models.sign_recognition.read_speed_limit_sign(detections)
        sign_speed_limit = sign_info.get("speed_limit")
        
        # 5. Collision Warning
        col_warnings = []
        if self.collision_warning:
            col_warnings = self.collision_warning.check(vehicle_tracks, w, h)
            
        # 6. OCR & Helmet
        vehicles_out = []
        plates_out = []
        helmets_out = []
        
        for t in vehicle_tracks:
            if self.models.plate_reader and (t.plate_text is None) and (self.frame_idx % ai_config.PLATE_OCR_INTERVAL == 0):
                plate = self.models.plate_reader.read_plate(frame, t.current_box)
                if plate:
                    t.plate_text = plate
            
            if t.plate_text:
                plates_out.append(PlateDetection(
                    plate_text=t.plate_text,
                    bbox=self._to_bbox(t.current_box),
                    confidence=None
                ))
            
            if t.cls_name == "motorbike" and self.models.helmet_checker and self.models.helmet_checker.enabled:
                from ai_engine.main import find_rider_for_motorbike
                rider = find_rider_for_motorbike(t, person_tracks)
                if rider is not None and rider.helmet_status is None:
                    rider.helmet_status = self.models.helmet_checker.check(frame, rider.current_box)
                
                if rider and rider.helmet_status is False:
                    helmets_out.append(HelmetViolation(
                        track_id=rider.id,
                        plate_text=t.plate_text,
                        bbox=self._to_bbox(rider.current_box)
                    ))
            
            vehicles_out.append(VehicleDetection(
                id=t.id,
                bbox=self._to_bbox(t.current_box),
                class_name=t.cls_name,
                zone=list(t.zones_visited)[-1] if t.zones_visited else None
            ))
            
        # 7. Speed Advisor
        vehicle_count = sum(self.zone_manager.counts.values()) if self.zone_manager else 0
        speed_advice_res = None
        if vehicle_speed is not None:
            advice = suggest_speed(
                current_speed=vehicle_speed,
                vehicle_count_in_zone=vehicle_count,
                sign_speed_limit=sign_speed_limit,
                safe_distance_speed=None
            )
            speed_advice_res = SpeedAdvice(
                current_speed=vehicle_speed,
                recommended_speed=advice["recommended_speed"],
                reason=advice["reason"]
            )
            
        col_schema = None
        if col_warnings:
            col_schema = CollisionWarningSchema(
                level="danger" if max(r for _, r in col_warnings) > ai_config.COLLISION_GROWTH_RATE_THRESHOLD else "warning",
                distance_estimate=None
            )
            
        traffic_signs_out = []
        if sign_info.get("detected"):
            traffic_signs_out.append(TrafficSign(
                sign_type=sign_info.get("type"),
                speed_limit=sign_info.get("speed_limit")
            ))
            
        proc_time = (time.time() - t_start) * 1000
        
        return DetectionResult(
            frame_id=self.frame_idx,
            timestamp=time.time(),
            vehicles=vehicles_out,
            plates=plates_out,
            helmet_violations=helmets_out,
            collision_warning=col_schema,
            speed_advice=speed_advice_res,
            traffic_signs=traffic_signs_out,
            processing_time_ms=proc_time
        )
