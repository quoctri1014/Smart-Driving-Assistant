"""
health_monitor.py
-----------------
0.6 Sensor & Camera Health Monitor (Giám sát sức khỏe cảm biến & camera):
- Phát hiện camera bị che khuất (bàn tay, băng dính, vải che).
- Phát hiện đóng băng khung hình (Frame Freeze - camera treo/đứng hình).
- Phát hiện mất tín hiệu luồng video (Signal loss / timeout).
- Phát hiện camera bị xoay lệch / lệch góc nghiêm trọng.
- Phát hiện mất tín hiệu GPS / định vị không hợp lệ.
- Cơ chế suy giảm an toàn (Graceful degradation): Tạm tắt các module phụ thuộc
  và báo động lên hệ thống, tránh phát cảnh báo sai khi thiết bị gặp sự cố.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np


class SensorHealthMonitor:
    def __init__(
        self,
        frame_timeout_sec: float = 2.0,
        dark_threshold: float = 12.0,
        low_variance_threshold: float = 15.0,
        freeze_duration_threshold_sec: float = 1.5
    ):
        self.frame_timeout_sec = frame_timeout_sec
        self.dark_threshold = dark_threshold
        self.low_variance_threshold = low_variance_threshold
        self.freeze_duration_thresh = freeze_duration_threshold_sec

        self.last_frame_time: Optional[float] = None
        self.prev_gray_sample: Optional[np.ndarray] = None
        self.freeze_start_time: Optional[float] = None
        self.last_healthy_state: bool = True

    def check_camera_health(self, frame: Optional[np.ndarray], current_time: float) -> Tuple[str, List[str]]:
        """
        Kiểm tra trạng thái camera. Trả về (camera_status, issues).
        camera_status: 'OK', 'OBSTRUCTED', 'FROZEN', 'DISCONNECTED'
        """
        issues = []

        # 1. Kiểm tra mất tín hiệu / timeout
        if frame is None or frame.size == 0:
            if self.last_frame_time and (current_time - self.last_frame_time) > self.frame_timeout_sec:
                return "DISCONNECTED", ["Mất tín hiệu camera quá 2 giây"]
            return "DISCONNECTED", ["Không nhận được khung hình từ camera"]

        if self.last_frame_time is not None:
            gap = current_time - self.last_frame_time
            if gap > self.frame_timeout_sec:
                issues.append(f"Mất tín hiệu camera tạm thời ({gap:.1f}s)")

        self.last_frame_time = current_time

        # Thu nhỏ để kiểm tra nhanh
        small = cv2.resize(frame, (64, 48))
        if len(small.shape) == 3:
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        else:
            gray = small

        mean_val = float(np.mean(gray))
        var_val = float(np.var(gray))

        # 2. Kiểm tra camera bị che khuất (đen ngòm hoặc một màu đơn điệu)
        if mean_val < self.dark_threshold and var_val < self.low_variance_threshold:
            return "OBSTRUCTED", ["Camera bị che khuất hoặc ống kính bị bịt kín"]
        elif var_val < 3.0:
            return "OBSTRUCTED", ["Ảnh camera đơn sắc hoàn toàn, nghi ngờ bị che ống kính"]

        # 3. Kiểm tra đóng băng khung hình (Frame Freeze)
        if self.prev_gray_sample is not None:
            diff = float(np.mean(np.abs(gray.astype(np.float32) - self.prev_gray_sample.astype(np.float32))))
            if diff < 0.3:  # Hầu như không có thay đổi giữa 2 khung hình liên tiếp
                if self.freeze_start_time is None:
                    self.freeze_start_time = current_time
                elif (current_time - self.freeze_start_time) > self.freeze_duration_thresh:
                    return "FROZEN", [f"Khung hình camera bị đóng băng đứng hình ({current_time - self.freeze_start_time:.1f}s)"]
            else:
                self.freeze_start_time = None
        else:
            self.freeze_start_time = None

        self.prev_gray_sample = gray.copy()
        return "OK", issues

    def evaluate_system_health(
        self,
        frame: Optional[np.ndarray],
        current_time: float,
        gps_valid: bool = True,
        imu_pitch_deg: float = 0.0
    ) -> Dict[str, Any]:
        """
        Đánh giá tổng thể sức khỏe cảm biến và xác định danh sách module cần tạm ngắt
        để tránh phát cảnh báo sai (False Alarms).
        """
        cam_status, cam_issues = self.check_camera_health(frame, current_time)

        # Kiểm tra góc nghiêng camera
        tilt_issue = None
        if abs(imu_pitch_deg) > 25.0:
            tilt_issue = f"Camera bị lệch góc / rung lắc quá lớn (Góc nghiêng: {imu_pitch_deg:.1f}°)"

        # Xác định module cần tắt an toàn
        disabled_modules = []
        if cam_status in ("OBSTRUCTED", "DISCONNECTED", "FROZEN"):
            disabled_modules.extend([
                "vehicle_detection", "tracker", "speed_estimator",
                "collision_warning", "sign_recognition", "plate_reader",
                "helmet_checker", "safe_distance_calculator"
            ])

        gps_status = "OK" if gps_valid else "LOST"
        if not gps_valid:
            disabled_modules.append("gps_speed_governor")

        all_issues = list(cam_issues)
        if tilt_issue:
            all_issues.append(tilt_issue)
        if not gps_valid:
            all_issues.append("Mất tín hiệu định vị GPS")

        is_healthy = (cam_status == "OK") and gps_valid and (not tilt_issue)

        return {
            "healthy": is_healthy,
            "camera_status": cam_status,
            "gps_status": gps_status,
            "issues": all_issues,
            "disabled_modules": list(set(disabled_modules)),
            "graceful_degradation_active": len(disabled_modules) > 0
        }
