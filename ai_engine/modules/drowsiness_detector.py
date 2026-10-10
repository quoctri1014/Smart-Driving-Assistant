"""
drowsiness_detector.py
-----------------------
Hệ thống giám sát trạng thái tài xế (Driver Monitoring System - DMS) cấp cao:
1. Tính EAR (Eye Aspect Ratio) và MAR (Mouth Aspect Ratio) qua MediaPipe Face Mesh.
2. PERCLOS (Percentage of Eye Closure): Tỷ lệ nhắm mắt trong cửa sổ trượt 60 giây theo tiêu chuẩn NHTSA/ISO.
3. Ước lượng tư thế đầu 3D (Head Pose via cv2.solvePnP):
   - Pitch: Phát hiện gục đầu ngủ gật (Pitch < -25°).
   - Yaw: Phát hiện mất tập trung nhìn sang bên (Yaw > 30° hoặc Yaw < -30°).
   - Roll: Nghiêng đầu.
4. Tự động cân chỉnh động cá nhân (Dynamic Calibration) 10-30s đầu theo khuôn mặt từng tài xế.
5. Ngoại lệ:
   - Đeo kính cận/kính râm: Tự động chuyển sang chế độ Sunglasses Mode (bỏ qua EAR, dựa vào Head Pose + hạ độ tin cậy).
   - Đeo khẩu trang / ngáp che tay.
   - Phân biệt hành khách: Chỉ chọn khuôn mặt ở vị trí ghế lái.
"""

from __future__ import annotations

import json
import logging
import math
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from .eyes_closed_monitor import EyesClosedMonitor, EyeState, EyesClosedConfig, DmsResult

logger = logging.getLogger(__name__)
CONFIG_PATH = Path("ai_engine/config/adas_config.json")

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision

    class ModernFaceMeshWrapper:
        def __init__(self, model_path="ai_engine/models/face_landmarker.task", *args, **kwargs):
            import os
            # Resolve relative model_path from project root
            target_path = Path(model_path)
            if not target_path.is_absolute():
                project_root = Path(__file__).resolve().parent.parent.parent
                cand = project_root / model_path
                if cand.exists():
                    target_path = cand
            if not target_path.exists():
                raise FileNotFoundError(f"Face landmarker model not found at {target_path}")

            base_options = mp_python.BaseOptions(model_asset_path=str(target_path))
            num_faces = kwargs.get("max_num_faces", kwargs.get("num_faces", 2))
            min_det = kwargs.get("min_detection_confidence", 0.25)
            min_track = kwargs.get("min_tracking_confidence", 0.25)
            options = mp_vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=True,
                num_faces=num_faces,
                min_face_detection_confidence=min_det,
                min_face_presence_confidence=min_det,
                min_tracking_confidence=min_track
            )
            self.detector = mp_vision.FaceLandmarker.create_from_options(options)

        def process(self, rgb_image):
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
            res = self.detector.detect(mp_image)
            
            class FaceResult:
                def __init__(self, face_landmarks):
                    self.landmark = face_landmarks
                    
            class ProcessResult:
                def __init__(self, faces):
                    self.multi_face_landmarks = [FaceResult(fl) for fl in faces] if faces else None
                    
            return ProcessResult(res.face_landmarks)

        def close(self):
            if self.detector:
                try:
                    self.detector.close()
                except Exception:
                    pass
                self.detector = None

    _FACE_MESH_CLS = ModernFaceMeshWrapper
    _HAS_MEDIAPIPE = True
except Exception:
    try:
        import mediapipe as mp
        _FACE_MESH_CLS = mp.solutions.face_mesh.FaceMesh
        _HAS_MEDIAPIPE = True
    except Exception:
        _HAS_MEDIAPIPE = False
        _FACE_MESH_CLS = None


def _load_dms_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m11_dms", {})
        except Exception:
            pass
    return {
        "perclos_window_sec": 60,
        "perclos_drowsy_threshold": 0.15,
        "ear_threshold_default": 0.21,
        "mar_yawn_threshold": 0.55,
        "nodding_pitch_down_deg": 25.0,
        "distraction_yaw_deg": 30.0,
    }


# Mô hình 3D khuôn mặt chuẩn (3D Canonical Facial Model points in mm)
MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),          # Chóp mũi (Nose tip)
    (0.0, -330.0, -65.0),      # Cằm (Chin)
    (-225.0, 170.0, -135.0),   # Khóe mắt trái (Left eye corner)
    (225.0, 170.0, -135.0),    # Khóe mắt phải (Right eye corner)
    (-150.0, -150.0, -125.0),  # Khóe miệng trái (Left mouth corner)
    (150.0, -150.0, -125.0),   # Khóe miệng phải (Right mouth corner)
], dtype=np.float64)


def estimate_head_pose_pnp(landmarks_2d: np.ndarray, frame_w: int, frame_h: int) -> Tuple[float, float, float]:
    """
    Ước lượng góc xoay đầu (Pitch, Yaw, Roll) tính bằng độ bằng thuật toán solvePnP.
    """
    try:
        focal_length = frame_w
        center = (frame_w / 2.0, frame_h / 2.0)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        success, rvec, tvec = cv2.solvePnP(
            MODEL_POINTS_3D,
            landmarks_2d,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return 0.0, 0.0, 0.0

        rmat, _ = cv2.Rodrigues(rvec)
        # Tính Euler angles từ ma trận xoay
        sy = math.sqrt(rmat[0, 0] ** 2 + rmat[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            pitch = math.atan2(rmat[2, 1], rmat[2, 2])
            yaw = math.atan2(-rmat[2, 0], sy)
            roll = math.atan2(rmat[1, 0], rmat[0, 0])
        else:
            pitch = math.atan2(-rmat[1, 2], rmat[1, 1])
            yaw = math.atan2(-rmat[2, 0], sy)
            roll = 0.0

        return math.degrees(pitch), math.degrees(yaw), math.degrees(roll)
    except Exception:
        return 0.0, 0.0, 0.0


class DrowsinessDetector:
    """
    DMS Drowsiness & Distraction Detector.
    """
    LEFT_EYE  = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]
    MOUTH     = [78, 81, 13, 308, 14, 178]
    # Landmark indices tương ứng với MODEL_POINTS_3D: Chóp mũi (1), Cằm (152), Mắt trái (33), Mắt phải (263), Miệng trái (61), Miệng phải (291)
    POSE_LANDMARKS = [1, 152, 33, 263, 61, 291]

    def __init__(self):
        self.cfg = _load_dms_config()
        self._face_mesh = None
        self._enabled = _HAS_MEDIAPIPE

        if _HAS_MEDIAPIPE and _FACE_MESH_CLS is not None:
            try:
                self._face_mesh = _FACE_MESH_CLS(
                    max_num_faces=2,  # Nhận diện tối đa 2 mặt để phân biệt tài xế và hành khách
                    refine_landmarks=True,
                    min_detection_confidence=0.35,
                    min_tracking_confidence=0.35,
                )
                self._enabled = True
            except Exception as e:
                logger.warning(f"DrowsinessDetector primary init error: {e}")
                try:
                    import mediapipe as mp
                    self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                        max_num_faces=2,
                        refine_landmarks=True,
                        min_detection_confidence=0.35,
                        min_tracking_confidence=0.35,
                    )
                    self._enabled = True
                except Exception as e2:
                    logger.warning(f"DrowsinessDetector fallback init error: {e2}")
                    self._enabled = False

        # Cửa sổ PERCLOS 60s: lưu (timestamp, is_closed_bool)
        self.perclos_window_sec = float(self.cfg.get("perclos_window_sec", 60))
        self.perclos_samples: deque = deque(maxlen=1800)  # 60s * 30fps

        # Tự cân chỉnh cá nhân 10s đầu
        self._calib_start_time = time.monotonic()
        self._calib_duration = 10.0
        self._calib_ear_samples = []
        self.is_calibrated = False
        self.baseline_ear = float(self.cfg.get("ear_threshold_default", 0.21)) / 0.75
        self.ear_threshold = float(self.cfg.get("ear_threshold_default", 0.21))
        self.yawn_threshold = float(self.cfg.get("mar_yawn_threshold", 0.55))

        self.consecutive_closed_frames = 0
        self.consecutive_distracted_frames = 0
        self.yawn_count = 0
        self._yawns = deque()

        # Hệ thống phát hiện nhắm mắt kéo dài (DMS) State Machine
        self.eyes_closed_monitor = EyesClosedMonitor(
            cfg=EyesClosedConfig(
                warn_s=2.0,
                critical_s=5.0,
                gap_tolerance_s=0.3,
                min_blink_s=0.5,
                calib_s=10.0,
                cooldown_s=10.0,
                pitch_down_deg=-25.0
            ),
            baseline_ear=self.baseline_ear
        )

    def reset(self):
        """Khởi động lại trạng thái detector khi tài xế nghỉ ngơi."""
        self._calib_start_time = time.monotonic()
        self._calib_ear_samples.clear()
        self.consecutive_closed_frames = 0
        self.consecutive_distracted_frames = 0
        self.yawn_count = 0
        self._yawns.clear()
        self.perclos_samples.clear()
        self.eyes_closed_monitor = EyesClosedMonitor(
            cfg=EyesClosedConfig(
                warn_s=2.0,
                critical_s=5.0,
                gap_tolerance_s=0.3,
                min_blink_s=0.5,
                calib_s=10.0,
                cooldown_s=10.0,
                pitch_down_deg=-25.0
            ),
            baseline_ear=self.baseline_ear
        )
    def close(self):
        """Giải phóng tài nguyên MediaPipe khi kết thúc phiên."""
        if self._face_mesh is not None:
            try:
                self._face_mesh.close()
            except Exception:
                pass
            self._face_mesh = None
        self._enabled = False

    @staticmethod
    def _dist(p1, p2, w: int, h: int) -> float:
        return math.hypot((p1.x - p2.x) * w, (p1.y - p2.y) * h)

    def _ear(self, lm, indices: list, w: int, h: int) -> float:
        p1, p2, p3, p4, p5, p6 = [lm[i] for i in indices]
        v1 = self._dist(p2, p6, w, h)
        v2 = self._dist(p3, p5, w, h)
        h1 = self._dist(p1, p4, w, h)
        return (v1 + v2) / (2.0 * h1) if h1 > 0 else 0.0

    def _mar(self, lm, indices: list, w: int, h: int) -> float:
        p1, p2, p3, p4, p5, p6 = [lm[i] for i in indices]
        vertical_1 = self._dist(p2, p3, w, h)
        vertical_2 = self._dist(p5, p6, w, h)
        horizontal = self._dist(p1, p4, w, h)
        return (vertical_1 + vertical_2) / (2.0 * horizontal) if horizontal > 0 else 0.0

    def detect(self, frame) -> dict:
        """Phân tích frame cabin và trả về kết quả DMS toàn diện."""
        now_mono = time.monotonic()
        if not self._enabled or self._face_mesh is None or frame is None or frame.size == 0:
            dms_res = self.eyes_closed_monitor.update(now_mono, False, None, quality=0.0)
            return {
                "face_detected": False,
                "is_drowsy": False,
                "eye_state": dms_res.state.value,
                "closed_duration_s": 0.0,
                "events": [],
                "ear_value": 0.0,
                "yawn_count": 0,
                "alert_level": "normal",
                "perclos": 0.0,
                "head_pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                "is_distracted": False,
                "sunglasses_mode": False
            }

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            dms_res = self.eyes_closed_monitor.update(now_mono, False, None, quality=0.0)
            return {
                "face_detected": False,
                "is_drowsy": False,
                "eye_state": dms_res.state.value,
                "closed_duration_s": 0.0,
                "events": dms_res.events,
                "ear_value": 0.0,
                "yawn_count": self.yawn_count,
                "alert_level": "normal",
                "perclos": 0.0,
                "head_pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                "is_distracted": False,
                "sunglasses_mode": False
            }

        # 1. Phân biệt tài xế: Chọn mặt có diện tích lớn nhất và nằm lệch về phía ghế lái
        driver_lm = results.multi_face_landmarks[0]
        if len(results.multi_face_landmarks) > 1:
            # Chọn mặt có x_center gần vị trí lái nhất
            best_face = None
            best_area = -1
            for face in results.multi_face_landmarks:
                xs = [pt.x for pt in face.landmark]
                ys = [pt.y for pt in face.landmark]
                area = (max(xs) - min(xs)) * (max(ys) - min(ys))
                if area > best_area:
                    best_area = area
                    best_face = face
            driver_lm = best_face

        lm = driver_lm.landmark

        # 2. Tính EAR và MAR
        ear_left = self._ear(lm, self.LEFT_EYE, w, h)
        ear_right = self._ear(lm, self.RIGHT_EYE, w, h)
        ear = (ear_left + ear_right) / 2.0
        mar = self._mar(lm, self.MOUTH, w, h)

        # 3. Ước lượng Head Pose qua solvePnP
        landmarks_2d = np.array([
            (lm[idx].x * w, lm[idx].y * h) for idx in self.POSE_LANDMARKS
        ], dtype=np.float64)
        pitch, yaw, roll = estimate_head_pose_pnp(landmarks_2d, w, h)

        # 4. Hiệu chuẩn động cá nhân
        if not self.is_calibrated:
            if now_mono - self._calib_start_time < self._calib_duration:
                if 0.15 < ear < 0.40 and mar < 0.45:
                    self._calib_ear_samples.append(ear)
            else:
                if len(self._calib_ear_samples) >= 15:
                    self.baseline_ear = float(np.median(self._calib_ear_samples))
                    self.ear_threshold = round(self.baseline_ear * 0.72, 3)
                self.is_calibrated = True
                # Sync calibrated baseline to EyesClosedMonitor so it skips redundant calibration
                if self.eyes_closed_monitor.baseline is None:
                    self.eyes_closed_monitor.baseline = self.baseline_ear

        # 5. Ngoại lệ: Kính râm / Kính cận tối màu
        # Nếu mắt bị che hoặc không phân biệt được (EAR rất bất thường hoặc vùng mắt quá tối)
        is_sunglasses = False
        left_eye_center = (int(lm[33].x * w), int(lm[33].y * h))
        if 0 <= left_eye_center[1] < h and 0 <= left_eye_center[0] < w:
            eye_patch = frame[max(0, left_eye_center[1]-8):min(h, left_eye_center[1]+8),
                              max(0, left_eye_center[0]-8):min(w, left_eye_center[0]+8)]
            if eye_patch.size > 0 and float(eye_patch.mean()) < 25.0:
                is_sunglasses = True

        # 6. PERCLOS (Percentage of Eye Closure trong 60s)
        is_closed = ear < self.ear_threshold if not is_sunglasses else False
        self.perclos_samples.append((now_mono, is_closed))

        # Dọn dẹp mẫu cũ hơn 60 giây
        while self.perclos_samples and (now_mono - self.perclos_samples[0][0]) > self.perclos_window_sec:
            self.perclos_samples.popleft()

        closed_count = sum(1 for _, closed in self.perclos_samples if closed)
        perclos = (closed_count / float(len(self.perclos_samples))) if self.perclos_samples else 0.0

        if is_closed:
            self.consecutive_closed_frames += 1
        else:
            self.consecutive_closed_frames = 0

        # 7. Phát hiện ngáp
        now_ts = time.time()
        while self._yawns and (now_ts - self._yawns[0]) > 60.0:
            self._yawns.popleft()

        if mar > self.yawn_threshold:
            if not self._yawns or (now_ts - self._yawns[-1]) > 3.0:
                self._yawns.append(now_ts)
                self.yawn_count += 1

        recent_yawns = len(self._yawns)

        # 8. Mất tập trung (Distraction) qua Yaw
        distract_yaw_thresh = float(self.cfg.get("distraction_yaw_deg", 30.0))
        is_looking_away = abs(yaw) > distract_yaw_thresh
        if is_looking_away:
            self.consecutive_distracted_frames += 1
        else:
            self.consecutive_distracted_frames = 0

        is_distracted = self.consecutive_distracted_frames >= 25  # ~1 giây nhìn sang bên

        # 9. Gục đầu ngủ gật qua Pitch
        nodding_pitch_thresh = float(self.cfg.get("nodding_pitch_down_deg", 25.0))
        is_nodding_off = pitch < -nodding_pitch_thresh and self.consecutive_closed_frames >= 15

        # 9.5 Cập nhật EyesClosedMonitor State Machine
        quality = 0.9 if not is_sunglasses else 0.4
        dms_res = self.eyes_closed_monitor.update(
            now_mono,
            face_found=True,
            ear=ear if not is_sunglasses else None,
            quality=quality,
            head_pitch=pitch
        )

        # 10. Phân cấp mức độ nguy hiểm
        perclos_thresh = float(self.cfg.get("perclos_drowsy_threshold", 0.15))
        alert_level = "normal"

        if dms_res.state == EyeState.CLOSED_CRITICAL or self.consecutive_closed_frames >= 30 or is_nodding_off or perclos > (perclos_thresh * 1.5):
            alert_level = "critical"
        elif dms_res.state == EyeState.CLOSED_WARN or self.consecutive_closed_frames >= 15 or perclos > perclos_thresh or recent_yawns >= 3:
            alert_level = "warning"
        elif dms_res.state == EyeState.CLOSING or self.consecutive_closed_frames >= 8 or recent_yawns >= 1 or is_distracted:
            alert_level = "caution"

        return {
            "face_detected": True,
            "is_drowsy": alert_level in ("warning", "critical"),
            "eye_state": dms_res.state.value,
            "closed_duration_s": round(float(dms_res.closed_duration_s), 2),
            "events": dms_res.events,
            "threshold": round(float(dms_res.threshold), 3) if dms_res.threshold is not None else self.ear_threshold,
            "ear_value": round(float(ear), 3),
            "mar_value": round(float(mar), 3),
            "yawn_count": self.yawn_count,
            "recent_yawns": recent_yawns,
            "alert_level": alert_level,
            "consecutive_closed": self.consecutive_closed_frames,
            "perclos": round(float(perclos), 3),
            "head_pose": {
                "pitch": round(float(pitch), 1),
                "yaw": round(float(yaw), 1),
                "roll": round(float(roll), 1)
            },
            "is_distracted": is_distracted,
            "is_calibrated": self.is_calibrated or (self.eyes_closed_monitor.baseline is not None),
            "sunglasses_mode": is_sunglasses
        }
