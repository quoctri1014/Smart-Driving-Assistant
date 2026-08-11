import os
import cv2
import time
import math
import logging
import mediapipe as mp
from collections import deque
from ultralytics import YOLO
from ai_engine import config

logger = logging.getLogger(__name__)

class DrowsinessDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.ear_history = deque(maxlen=15) 
        self.yawn_count = 0
        self.is_yawning = False

    def calculate_distance(self, p1, p2, frame_w, frame_h):
        return math.hypot((p1.x - p2.x) * frame_w, (p1.y - p2.y) * frame_h)

    def calculate_ear(self, landmarks, eye_indices, w, h):
        p1 = landmarks[eye_indices[0]]
        p2 = landmarks[eye_indices[1]]
        p3 = landmarks[eye_indices[2]]
        p4 = landmarks[eye_indices[3]]
        p5 = landmarks[eye_indices[4]]
        p6 = landmarks[eye_indices[5]]
        
        v1 = self.calculate_distance(p2, p6, w, h)
        v2 = self.calculate_distance(p3, p5, w, h)
        h1 = self.calculate_distance(p1, p4, w, h)
        
        if h1 == 0:
            return 0
        return (v1 + v2) / (2.0 * h1)
        
    def calculate_mar(self, landmarks, mouth_indices, w, h):
        p1 = landmarks[mouth_indices[0]] 
        p4 = landmarks[mouth_indices[3]] 
        p2 = landmarks[mouth_indices[1]] 
        p6 = landmarks[mouth_indices[5]] 
        p3 = landmarks[mouth_indices[2]] 
        p5 = landmarks[mouth_indices[4]] 
        
        v1 = self.calculate_distance(p2, p6, w, h)
        v2 = self.calculate_distance(p3, p5, w, h)
        h1 = self.calculate_distance(p1, p4, w, h)
        
        if h1 == 0:
            return 0
        return (v1 + v2) / (2.0 * h1)

    def detect_drowsiness(self, frame):
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        status = {
            "is_drowsy": False,
            "ear_value": 0.0,
            "yawn_count": self.yawn_count,
            "alert_level": "normal"
        }

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            left_eye_indices = [33, 160, 158, 133, 153, 144]
            right_eye_indices = [362, 385, 387, 263, 373, 380]
            mouth_indices = [78, 81, 13, 308, 14, 178] 
            
            left_ear = self.calculate_ear(landmarks, left_eye_indices, w, h)
            right_ear = self.calculate_ear(landmarks, right_eye_indices, w, h)
            ear = (left_ear + right_ear) / 2.0
            
            mar = self.calculate_mar(landmarks, mouth_indices, w, h)
            
            self.ear_history.append(ear)
            
            avg_ear = sum(self.ear_history) / len(self.ear_history) if self.ear_history else ear
            status["ear_value"] = avg_ear
            
            if avg_ear < config.EAR_THRESHOLD:
                if len(self.ear_history) == self.ear_history.maxlen and all(e < config.EAR_THRESHOLD for e in self.ear_history):
                    status["is_drowsy"] = True
                    status["alert_level"] = "critical"
                else:
                    status["alert_level"] = "warning"
                    
            if mar > config.YAWN_THRESHOLD:
                if not self.is_yawning:
                    self.is_yawning = True
                    self.yawn_count += 1
            else:
                self.is_yawning = False
                
            status["yawn_count"] = self.yawn_count
            
        return status

class SeatbeltDetector:
    def __init__(self, model_path="models/seatbelt.pt"):
        self.model_path = model_path
        self.model = None
        
        if os.path.exists(self.model_path):
            self.model = YOLO(self.model_path)
        else:
            logger.warning(f"Seatbelt model not found at {self.model_path}. Running in MOCK mode.")

    def detect_seatbelt(self, frame):
        status = {
            "seatbelt_on": True, 
            "confidence": 1.0
        }
        
        if self.model:
            results = self.model(frame, verbose=False)
            if results and len(results[0].boxes) > 0:
                boxes = results[0].boxes
                best_conf = float(boxes.conf[0])
                cls = int(boxes.cls[0])
                
                status["seatbelt_on"] = (cls == 0)
                status["confidence"] = best_conf
                
        return status

class DrivingTimeTracker:
    def __init__(self):
        self.start_time = time.time()
        self.last_break_time = time.time()
        
    def update(self):
        current_time = time.time()
        continuous_seconds = current_time - self.last_break_time
        continuous_minutes = continuous_seconds / 60.0
        
        should_rest = continuous_minutes >= config.MAX_CONTINUOUS_DRIVING_MINUTES
        message = "Lái xe an toàn."
        
        if should_rest:
            message = f"CẢNH BÁO: Đã lái xe liên tục quá {config.MAX_CONTINUOUS_DRIVING_MINUTES} phút. Hãy nghỉ ngơi!"
        elif continuous_minutes >= config.MAX_CONTINUOUS_DRIVING_MINUTES - config.REST_REMINDER_INTERVAL:
            message = "Nhắc nhở: Sắp tới thời gian nghỉ ngơi khuyên dùng."
            
        return {
            "continuous_minutes": continuous_minutes,
            "should_rest": should_rest,
            "message": message
        }
        
    def reset_after_break(self):
        self.last_break_time = time.time()

class DriverPipelineSession:
    def __init__(self):
        self.drowsiness_detector = DrowsinessDetector()
        self.seatbelt_detector = SeatbeltDetector()
        self.time_tracker = DrivingTimeTracker()
        self.frame_idx = 0
        
    def process_driver_frame(self, frame):
        t_start = time.time()
        self.frame_idx += 1
        
        drowsiness_res = self.drowsiness_detector.detect_drowsiness(frame)
        seatbelt_res = self.seatbelt_detector.detect_seatbelt(frame)
        time_res = self.time_tracker.update()
        
        proc_time = (time.time() - t_start) * 1000
        
        return {
            "frame_id": self.frame_idx,
            "timestamp": time.time(),
            "drowsiness": drowsiness_res,
            "seatbelt": seatbelt_res,
            "driving_time": time_res,
            "processing_time_ms": proc_time
        }
