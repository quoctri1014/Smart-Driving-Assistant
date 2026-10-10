import time
import logging
from typing import Optional, List
from modules.detector import VehicleDetector
from modules.tracker import SimpleTracker
from modules.zone_manager import ZoneManager
from modules.plate_reader import PlateReader
from modules.helmet_checker import HelmetChecker
from modules.collision_warning import CollisionWarning
from modules.safe_distance_calculator import SafeDistanceCalculator
from modules.speed_estimator import SpeedEstimator
from modules.speed_recommendation import recommend_speed
from modules.sign_recognition import SignRecognition
from modules.violation_manager import ViolationManager
from modules.lane_detector import LaneDetector
import config as ai_config

from backend.app.schemas.adas_event import AdasEvent, DecisionResult as AdasDecisionResult
from backend.app.core.decision_engine import DecisionEngine
from backend.app.schemas.detection_result import (
    DetectionResult, BoundingBox, VehicleDetection, 
    PlateDetection, HelmetViolation, SpeedAdvice, 
    CollisionWarning as CollisionWarningSchema, TrafficSign
)
from ai_engine.modules.image_quality_gate import ImageQualityGate
from ai_engine.modules.health_monitor import SensorHealthMonitor
from ai_engine.modules.load_shedder import AdaptiveLoadShedder
from ai_engine.modules.sensor_fusion import SensorFusionEKF
from ai_engine.modules.data_engine import DataEngine

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
        self.safe_distance_calculator = SafeDistanceCalculator()
        self.speed_estimator = SpeedEstimator(fps=25.0)
        self.lane_detector = LaneDetector()
        self.decision_engine = DecisionEngine()
        self.violation_manager = ViolationManager()
        self.quality_gate = ImageQualityGate()
        self.health_monitor = SensorHealthMonitor()
        self.load_shedder = AdaptiveLoadShedder()
        self.sensor_fusion = SensorFusionEKF()
        self.data_engine = DataEngine()
        self.frame_idx = 0
        self.last_decision: Optional[AdasDecisionResult] = None
        self.last_speed_limit: Optional[float] = None
        
    def _to_bbox(self, box) -> BoundingBox:
        return BoundingBox(x1=box[0], y1=box[1], x2=box[2], y2=box[3])
        
    def process_frame(
        self, 
        frame, 
        vehicle_speed: Optional[float] = None, 
        estimated_distance_m: Optional[float] = None,
        session_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        gps_data: Optional[dict] = None,
        imu_data: Optional[dict] = None
    ) -> DetectionResult:

        t_start = time.time()
        cur_time = t_start
        self.frame_idx += 1
        
        # 0. Sensor & Camera Health Monitor
        health_report = self.health_monitor.evaluate_system_health(frame, current_time=cur_time)

        # 0.1 Image Quality Gate
        quality_report, frame = self.quality_gate.assess_frame(frame)

        # 0.2 Adaptive Load Shedder
        frame, scale = self.load_shedder.adapt_frame(frame)
        h, w = frame.shape[:2]

        # 0.3 Sensor Fusion (EKF GPS + IMU)
        fused = self.sensor_fusion.process_telemetry(cur_time, gps_data, imu_data)
        if vehicle_speed is None and fused.get("speed_kph") is not None:
            vehicle_speed = fused["speed_kph"]
            
        if ai_config.RESIZE_WIDTH and scale == 1.0:
            import cv2
            s = ai_config.RESIZE_WIDTH / w
            frame = cv2.resize(frame, (ai_config.RESIZE_WIDTH, int(h * s)))
            h, w = frame.shape[:2]
            
        # 1. Detection
        detections = self.models.detector.detect(frame)
        det_pairs = [(d["box"], d["cls_name"], d.get("conf", 0.8)) for d in detections]
        
        imu_pitch = imu_data.get("pitch", 0.0) if imu_data else 0.0

        # 2. Tracking (Kalman + ByteTrack + CMC)
        tracks = self.tracker.update(det_pairs, self.frame_idx, frame=frame)
        vehicle_tracks = [t for t in tracks if t.cls_name != "person" and not t.cls_name.startswith("speed_limit")]
        person_tracks = [t for t in tracks if t.cls_name == "person"]
        
        # 3. Lane Detection (Ego-Lane)
        lane_res = self.lane_detector.detect_ego_lane(frame)
        ego_lane_poly = lane_res.get("polygon")

        # 4. Speed Estimation (Homography / Perspective + Kalman + IMU pitch compensation)
        speed_map = self.speed_estimator.update(
            vehicle_tracks, self.frame_idx, frame_w=w, frame_h=h, ego_gps_speed=vehicle_speed,
            imu_pitch_rad=imu_pitch, frame=frame
        )
        for t in vehicle_tracks:
            t.speed_kmh = speed_map.get(t.id)

        # 5. Zone Management
        if self.zone_manager:
            self.zone_manager.update(vehicle_tracks + person_tracks, w, h)
            
        # 6. Sign Recognition (QCVN 41:2019 with multi-frame voting)
        sign_module = getattr(self.models, "sign_recognition", getattr(self.models, "sign_detector", None))
        sign_info = {}
        if sign_module is not None:
            if hasattr(sign_module, "read_speed_limit_sign"):
                sign_info = sign_module.read_speed_limit_sign(detections, frame)
            elif hasattr(sign_module, "detect"):
                sign_info = sign_module.detect(frame, detections)
        sign_speed_limit = sign_info.get("speed_limit")
        if sign_speed_limit is not None:
            self.last_speed_limit = sign_speed_limit
        effective_speed_limit = sign_speed_limit or self.last_speed_limit
        
        # 7. Collision Warning (TTC + Ego-Lane Gating)
        col_warnings = []
        if self.collision_warning:
            col_warnings = self.collision_warning.check(
                vehicle_tracks, w, h, ego_speed_kmh=vehicle_speed,
                ego_lane_polygon=ego_lane_poly, imu_pitch_rad=imu_pitch
            )
            
        # 8. Safe Distance Calculation (TT 31/2019/TT-BGTVT Điều 11)
        safe_dist_advice = self.safe_distance_calculator.calculate(
            col_warnings=col_warnings,
            speed_map=speed_map,
            estimated_distance_m=estimated_distance_m,
            ego_speed_kmh=vehicle_speed
        )

        # 8. OCR & Helmet Checking
        vehicles_out = []
        plates_out = []
        helmets_out = []
        
        active_plate_boxes = {}
        if self.models.plate_reader and self.load_shedder.should_process_module("plate_reader"):
            candidate_tracks = list(vehicle_tracks) + list(person_tracks)
            detected_plates_list = self.models.plate_reader.process_tracks(
                frame, candidate_tracks, self.frame_idx
            )
            for p in (detected_plates_list or []):
                trk = p.get("track")
                if trk and p.get("box") and p.get("accepted"):
                    active_plate_boxes[trk.id] = p["box"]

        # Ghép biển số từ người lái xe máy sang xe máy tương ứng
        from ai_engine.main import find_rider_for_motorbike
        for bike in vehicle_tracks:
            if bike.cls_name == "motorbike" and not getattr(bike, "plate_text", None):
                rider = find_rider_for_motorbike(bike, person_tracks)
                if rider and getattr(rider, "plate_text", None):
                    bike.plate_text = rider.plate_text
                    bike.plate_confidence = getattr(rider, "plate_confidence", 0.90)
                    bike.plate_status = getattr(rider, "plate_status", "CONFIRMED")
                    if rider.id in active_plate_boxes:
                        active_plate_boxes[bike.id] = active_plate_boxes[rider.id]

        for t in vehicle_tracks:
            p_text = getattr(t, "plate_text", None)
            p_status = getattr(t, "plate_status", None)
            
            current_pbox = active_plate_boxes.get(t.id)
            if p_text and current_pbox:
                plates_out.append(PlateDetection(
                    plate_text=p_text,
                    bbox=self._to_bbox(current_pbox),
                    confidence=getattr(t, "plate_confidence", None)
                ))

            # Kiểm tra mũ bảo hiểm cho xe máy
            if t.cls_name == "motorbike" and self.models.helmet_checker and self.models.helmet_checker.enabled:
                rider = find_rider_for_motorbike(t, person_tracks)
                if rider is not None and rider.helmet_status is None:
                    rider.helmet_status = self.models.helmet_checker.check(frame, rider.current_box)
                
                if rider and rider.helmet_status is False:
                    helmets_out.append(HelmetViolation(
                        track_id=rider.id,
                        plate_text=p_text,
                        bbox=self._to_bbox(rider.current_box)
                    ))
            
            vehicles_out.append(VehicleDetection(
                id=t.id,
                bbox=self._to_bbox(t.current_box),
                class_name=t.cls_name,
                zone=list(t.zones_visited)[-1] if t.zones_visited else None,
                speed_kmh=getattr(t, "speed_kmh", None),
                plate_text=p_text,
                plate_status=p_status
            ))
            
        # 9. Adaptive Speed Recommendation
        vehicle_count = sum(self.zone_manager.counts.values()) if self.zone_manager else 0
        speed_advice_res = None
        
        # Tốc độ xe chủ (Ego vehicle speed):
        # Nếu có cảm biến GPS/OBD -> dùng vehicle_speed thực tế.
        # Nếu đang chạy video không có GPS -> ước tính tốc độ di chuyển thực tế của xe trong khoảng 35 - 50 km/h.
        # TUYỆT ĐỐI KHÔNG lấy max(speed_map.values()) vì đó là tốc độ của phương tiện khác phía trước!
        if vehicle_speed is not None and vehicle_speed > 0:
            current_speed_for_rec = float(vehicle_speed)
        elif speed_map:
            valid_speeds = [v for v in speed_map.values() if 5.0 <= v <= 75.0]
            if valid_speeds:
                median_traffic = float(np.median(valid_speeds))
                current_speed_for_rec = round(min(55.0, max(30.0, median_traffic)), 1)
            else:
                current_speed_for_rec = 42.0
        else:
            current_speed_for_rec = 42.0
        
        safe_dist_speed = safe_dist_advice.get("recommended_speed_kmh") if safe_dist_advice else None
        rec_res = recommend_speed(
            current_speed=current_speed_for_rec,
            vehicle_count_in_zone=vehicle_count,
            sign_speed_limit=effective_speed_limit,
            safe_distance_speed=safe_dist_speed,
            has_collision_warning=bool(col_warnings)
        )
        if rec_res.get("recommended_speed"):
            speed_advice_res = SpeedAdvice(
                current_speed=current_speed_for_rec,
                recommended_speed=rec_res["recommended_speed"],
                reason=rec_res["reason"]
            )
            
        col_schema = None
        if col_warnings:
            max_growth = max(r for _, r in col_warnings)
            col_schema = CollisionWarningSchema(
                level="danger" if max_growth > ai_config.COLLISION_GROWTH_RATE_THRESHOLD else "warning",
                distance_estimate=estimated_distance_m,
                recommended_distance_m=safe_dist_advice.get("recommended_distance_m") if safe_dist_advice else None,
                recommended_speed_kmh=safe_dist_advice.get("recommended_speed_kmh") if safe_dist_advice else None
            )
            
        traffic_signs_out = []
        if sign_info.get("detected") or sign_info.get("speed_limit"):
            traffic_signs_out.append(TrafficSign(
                sign_type=sign_info.get("type", "P.127" if sign_info.get("speed_limit") else "speed_limit"),
                speed_limit=sign_info.get("speed_limit")
            ))

        # 10. UNIFIED EVENT ARBITRATION (Decision Engine Integration)
        raw_events: List[AdasEvent] = []
        
        # Sự kiện va chạm TTC
        if col_schema and col_schema.level in ("warning", "danger"):
            raw_events.append(AdasEvent(
                module="ttc",
                type="collision_imminent",
                severity="critical" if col_schema.level == "danger" else "warning",
                confidence=0.88,
                payload={"distance_m": estimated_distance_m}
            ))

        # Sự kiện khoảng cách an toàn (bám đuôi)
        if safe_dist_advice and safe_dist_advice.get("is_unsafe"):
            raw_events.append(AdasEvent(
                module="safe_distance",
                type="tailgating",
                severity="warning",
                confidence=0.80,
                payload={"recommended_distance_m": safe_dist_advice.get("recommended_distance_m")}
            ))

        # Sự kiện nhận diện biển báo
        if sign_info.get("detected") and sign_info.get("speed_limit"):
            raw_events.append(AdasEvent(
                module="sign",
                type="speed_sign",
                severity="info",
                confidence=0.85,
                payload={"speed_limit": sign_info.get("speed_limit")}
            ))

        # Sự kiện quá tốc độ
        if vehicle_speed and sign_speed_limit and (vehicle_speed > sign_speed_limit + 5.0):
            raw_events.append(AdasEvent(
                module="speed",
                type="speeding",
                severity="critical" if (vehicle_speed > sign_speed_limit + 15.0) else "warning",
                confidence=0.95,
                payload={"current_speed": vehicle_speed, "speed_limit": sign_speed_limit}
            ))

        # Sự kiện không đội mũ bảo hiểm
        for hv in helmets_out:
            raw_events.append(AdasEvent(
                module="helmet",
                type="no_helmet",
                severity="critical",
                confidence=0.85,
                payload={"track_id": hv.track_id, "plate_text": hv.plate_text}
            ))

        # Nếu chất lượng ảnh quá kém hoặc camera bị che/lỗi, không phát sinh sự kiện vi phạm để chống báo sai
        if quality_report.is_low_quality or health_report["camera_status"] != "OK":
            raw_events = []
            col_schema = None
            helmets_out = []
            plates_out = []
            self.data_engine.record_hard_case(
                frame=frame,
                trigger_reason="LOW_QUALITY" if quality_report.is_low_quality else "CAMERA_OBSTRUCTED",
                module_name="pipeline",
                quality_info={"score": quality_report.score, "issues": quality_report.issues + health_report["issues"]}
            )

        # Đưa vào Decision Engine
        decision = self.decision_engine.process_events(
            raw_events, session_id=session_id, driver_id=driver_id
        )
        self.last_decision = decision
            
        proc_time = (time.time() - t_start) * 1000
        self.load_shedder.record_frame_latency(proc_time)
        
        return DetectionResult(
            frame_width=w,
            frame_height=h,
            frame_id=self.frame_idx,
            timestamp=time.time(),
            vehicles=vehicles_out,
            plates=plates_out,
            helmet_violations=helmets_out,
            collision_warning=col_schema,
            speed_advice=speed_advice_res,
            traffic_signs=traffic_signs_out,
            zone_counts=self.zone_manager.counts if self.zone_manager else {},
            zone_occupancy=self.zone_manager.occupancy if self.zone_manager else {},
            processing_time_ms=round(proc_time, 2),
            speech_prompt=decision.speech_prompt,
            sound_alert=decision.sound_alert,
            decision=decision.model_dump(),
            quality_score=quality_report.score,
            is_low_quality=quality_report.is_low_quality,
            system_health=health_report,
            fused_telemetry=fused
        )
