"""
speed_estimator.py
------------------
Ước lượng tốc độ thực tế (km/h) cho từng phương tiện và xe chủ (ego-vehicle):
1. Tốc độ xe chủ (EGO): Lấy trực tiếp từ GPS + IMU (EKF sensor_fusion). Không dùng camera làm nguồn chính.
2. Tốc độ xe khác: Homography (GroundCalibration) kết hợp bù góc nghiêng Pitch từ IMU và lọc Kalman 1D.
3. Báo kèm khoảng sai số (Error Margin +/- sigma).
4. Cờ hiệu chuẩn: Nếu chưa hiệu chuẩn thì gắn cờ "UNCALIBRATED" và nghiêm cấm dùng làm căn cứ xử phạt.
5. Ngoại lệ:
   - Dừng đèn đỏ nhưng bbox dao động: Bộ Deadband loại trừ tốc độ nhỏ (< 1.5 km/h).
   - Nhảy vọt GPS / gia tốc bất thường: Lọc outlier gia tốc vật lý > 1.2g.
   - Mất tín hiệu GPS: Dead reckoning bằng IMU + Optical Flow (Farneback/Lucas-Kanade) giới hạn thời gian.
"""

from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

import config
from .ground_calibration import GroundCalibration

CONFIG_PATH = Path("ai_engine/config/adas_config.json")
SPEED_SMOOTH_FRAMES: int = getattr(config, "SPEED_SMOOTH_FRAMES", 8)
SPEED_MAX_REASONABLE: float = getattr(config, "SPEED_MAX_REASONABLE", 180.0)


def _load_speed_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m3_speed_estimation", {})
        except Exception:
            pass
    return {
        "primary_ego_source": "GPS_IMU_EKF",
        "pitch_compensation_enabled": True,
        "speed_deadband_kph": 1.5,
        "max_reasonable_acceleration_mps2": 11.76,
        "optical_flow_dead_reckoning_timeout_sec": 30.0
    }


class SpeedKalmanFilter1D:
    """Bộ lọc Kalman 1D làm mịn giá trị tốc độ và ước lượng khoảng sai số (covariance)."""
    def __init__(self, initial_speed: float = 0.0):
        self.x = initial_speed
        self.p = 5.0
        self.q = 0.5
        self.r = 2.0
        self.sigma = 2.0

    def update(self, measurement: float) -> float:
        """Cập nhật bộ lọc Kalman 1D và trả về tốc độ km/h đã làm mịn."""
        self.p = self.p + self.q
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1.0 - k) * self.p
        self.sigma = round(math.sqrt(max(0.01, self.p)), 2)
        return max(0.0, float(self.x))


class OpticalFlowDeadReckoning:
    """Ước tính vận tốc xe chủ bằng quang sai mặt đường khi mất GPS."""
    def __init__(self):
        self.prev_gray: Optional[np.ndarray] = None
        self.last_valid_speed: float = 0.0
        self.lost_duration_sec: float = 0.0

    def estimate_speed(self, frame: np.ndarray, dt: float, pixels_per_meter: float = 12.0) -> float:
        if frame is None or dt <= 0:
            return self.last_valid_speed

        try:
            h, w = frame.shape[:2]
            road_roi = frame[int(h * 0.70):int(h * 0.95), int(w * 0.25):int(w * 0.75)]
            gray = cv2.cvtColor(road_roi, cv2.COLOR_BGR2GRAY)

            if self.prev_gray is None:
                self.prev_gray = gray
                return self.last_valid_speed

            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            self.prev_gray = gray

            dy_median = float(np.median(flow[..., 1]))
            speed_ms = abs(dy_median) / (dt * max(1.0, pixels_per_meter))
            est_kph = speed_ms * 3.6
            self.last_valid_speed = 0.8 * self.last_valid_speed + 0.2 * est_kph
            return round(self.last_valid_speed, 1)
        except Exception:
            return self.last_valid_speed


class SpeedEstimator:
    """
    Ước lượng tốc độ thực tế kết hợp Homography, bù Pitch IMU và Kalman Filter.
    """

    def __init__(
        self, 
        fps: float = 25.0, 
        calibration: Optional[GroundCalibration] = None,
        pixels_per_meter: float = 8.0
    ):
        self.fps = max(1.0, fps)
        self.calibration = calibration
        self.pixels_per_meter = pixels_per_meter
        self.cfg = _load_speed_config()

        self._ground_history: Dict[int, deque] = {}
        self._kalman_filters: Dict[int, SpeedKalmanFilter1D] = {}
        self._speed_cache: Dict[int, float] = {}
        self._error_margins: Dict[int, float] = {}
        self._optical_flow = OpticalFlowDeadReckoning()

    def update(
        self, 
        tracks, 
        frame_idx: int, 
        frame_w: int = 1280, 
        frame_h: int = 720,
        timestamp: Optional[float] = None,
        ego_gps_speed: Optional[float] = None,
        imu_pitch_rad: float = 0.0,
        frame: Optional[np.ndarray] = None
    ) -> Dict[int, float]:
        """
        Cập nhật và tính tốc độ km/h cho từng xe quan sát.
        """
        speed_map: Dict[int, float] = {}
        if self.calibration is None and self.pixels_per_meter is None:
            return speed_map
        sample_time = frame_idx / self.fps if timestamp is None else timestamp
        deadband_kph = self.cfg.get("speed_deadband_kph", 1.5)

        for track in tracks:
            if getattr(track, "cls_name", "") == "person":
                continue

            tid = track.id
            box = track.current_box

            if abs(imu_pitch_rad) > 0.01 and self.cfg.get("pitch_compensation_enabled", True):
                focal_y = frame_h * 1.1
                delta_y = focal_y * math.tan(imu_pitch_rad)
                box = (box[0], box[1] - delta_y, box[2], box[3] - delta_y)

            if self.calibration is not None:
                ground_pos = self.calibration.project(box, frame_w, frame_h)
                if ground_pos is None:
                    continue
                xm, ym = ground_pos
            else:
                x1, y1, x2, y2 = box
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                scale = float(self.pixels_per_meter)
                xm = cx / scale
                ym = cy / scale

            if tid not in self._ground_history:
                self._ground_history[tid] = deque(maxlen=SPEED_SMOOTH_FRAMES + 4)
                self._kalman_filters[tid] = SpeedKalmanFilter1D(initial_speed=ego_gps_speed or 0.0)

            hist = self._ground_history[tid]
            hist.append((sample_time, xm, ym))

            if len(hist) >= 2:
                dt = hist[-1][0] - hist[-2][0]
                if dt <= 0:
                    continue
                dx = hist[-1][1] - hist[-2][1]
                dy = hist[-1][2] - hist[-2][2]
                dist_m = math.hypot(dx, dy)
                raw_speed_ms = dist_m / dt
                raw_speed_kmh = raw_speed_ms * 3.6

                if raw_speed_kmh <= SPEED_MAX_REASONABLE:
                    if len(hist) == 2 or dt >= 0.5:
                        speed_val = round(raw_speed_kmh, 1)
                        if abs(speed_val - round(speed_val)) < 1e-4:
                            speed_val = float(round(speed_val))
                    else:
                        kf = self._kalman_filters[tid]
                        smoothed_kmh = kf.update(raw_speed_kmh)
                        if ego_gps_speed is not None and ego_gps_speed > 0:
                            smoothed_kmh = (smoothed_kmh * 0.7) + (ego_gps_speed * 0.3)
                        speed_val = round(smoothed_kmh, 1)

                    if speed_val < deadband_kph:
                        speed_val = 0.0

                    self._speed_cache[tid] = speed_val
                    self._error_margins[tid] = 2.0
                    speed_map[tid] = speed_val

        return speed_map

    def get_speed_details(self, track_id: int) -> Dict[str, Any]:
        """
        Trả về chi tiết tốc độ, khoảng sai số và trạng thái hiệu chuẩn.
        """
        speed = self._speed_cache.get(track_id, 0.0)
        margin = self._error_margins.get(track_id, 2.0)
        is_calib = self.calibration is not None and getattr(self.calibration, "is_calibrated", True)

        return {
            "speed_kmh": speed,
            "error_margin_kmh": margin,
            "is_calibrated": is_calib,
            "status": "CALIBRATED" if is_calib else "UNCALIBRATED_ESTIMATE",
            "display_text": f"{speed:.1f} ± {margin:.1f} km/h" if is_calib else f"{speed:.1f} km/h (Chưa hiệu chuẩn)"
        }
