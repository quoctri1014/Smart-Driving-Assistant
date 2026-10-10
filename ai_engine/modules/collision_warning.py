"""
collision_warning.py
--------------------
Hệ thống cảnh báo va chạm sớm (Forward Collision Warning - FCW & TTC) chuẩn thương mại ADAS:
1. Ước lượng khoảng cách hình học (Pinhole Optics):
   D = (W_real * f) / W_bbox, bù góc nghiêng Pitch từ IMU.
2. Bộ lọc Kalman 2D theo dõi khoảng cách D và vận tốc tương đối v_rel = dD/dt.
3. Tính Time-To-Collision (TTC = D / |v_rel|).
4. Phân cấp cảnh báo:
   - Cảnh báo sớm: TTC <= 2.5s (Warning)
   - Cảnh báo khẩn cấp: TTC <= 1.5s (Critical)
5. Chỉ xét vật thể TRONG LÀN CỦA MÌNH (kết hợp với M4 LaneDetector / Ego-Lane Polygon).
6. Xử lý ngoại lệ:
   - Kẹt xe tốc độ thấp: Tắt cảnh báo khi vận tốc xe chủ < 10 km/h.
   - Xe máy tạt đầu (Cut-in) hoặc luồn lách: Phân tích vận tốc ngang dx/dt.
   - Bù rung xóc ổ gà/gờ giảm tốc qua IMU.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import config
from .utils import box_bottom_center, point_in_polygon

CONFIG_PATH = Path("ai_engine/config/adas_config.json")


def _load_ttc_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m7_collision_ttc", {})
        except Exception:
            pass
    return {
        "early_warning_ttc_sec": 2.5,
        "urgent_warning_ttc_sec": 1.5,
        "min_speed_suppress_kph": 10.0,
        "standard_vehicle_widths_m": {
            "car": 1.8,
            "bus": 2.55,
            "truck": 2.5,
            "motorbike": 0.8,
            "default": 1.8
        },
        "default_camera_focal_length_px": 800.0,
        "default_camera_height_m": 1.45
    }


class DistanceKalmanFilter:
    """Bộ lọc Kalman 2 trạng thái: [Khoảng cách D (m), Vận tốc tương đối v_rel (m/s)]."""
    def __init__(self, initial_d: float = 30.0):
        self.x = np.array([[initial_d], [0.0]])  # [D, v_rel]
        self.F = np.array([[1.0, 0.04], [0.0, 1.0]])  # dt = 0.04s (25 FPS)
        self.H = np.array([[1.0, 0.0]])
        self.P = np.eye(2) * 5.0
        self.Q = np.diag([0.05, 0.5])
        self.R = np.array([[1.5]])

    def predict(self, dt: float = 0.04):
        self.F[0, 1] = dt
        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        return float(self.x[0, 0]), float(self.x[1, 0])

    def update(self, measured_d: float, dt: float = 0.04) -> Tuple[float, float]:
        self.predict(dt)
        y = measured_d - float(np.dot(self.H, self.x)[0, 0])
        S = float(np.dot(np.dot(self.H, self.P), self.H.T)[0, 0]) + float(self.R[0, 0])
        K = np.dot(self.P, self.H.T) / S
        self.x = self.x + K * y
        self.P = np.dot(np.eye(2) - np.dot(K, self.H), self.P)
        return float(self.x[0, 0]), float(self.x[1, 0])


class CollisionWarning:
    """
    Module Cảnh báo va chạm dựa trên quang học Pinhole và Time-To-Collision (TTC).
    """

    def __init__(self, lane_polygon_percent=config.COLLISION_LANE_POLYGON):
        self.lane_polygon_percent = lane_polygon_percent
        self.cfg = _load_ttc_config()
        self._distance_filters: Dict[int, DistanceKalmanFilter] = {}
        self._warning_counters: Dict[int, int] = {}
        self._active_warnings: Dict[int, Dict[str, Any]] = {}
        self._last_timestamps: Dict[int, float] = {}

    def estimate_distance_pinhole(
        self, 
        box: Tuple[float, float, float, float], 
        cls_name: str, 
        frame_w: int, 
        frame_h: int,
        imu_pitch_rad: float = 0.0
    ) -> float:
        """
        Ước lượng khoảng cách hình học D = (W_real * f) / W_pixel.
        Bù góc pitch từ IMU.
        """
        widths_map = self.cfg.get("standard_vehicle_widths_m", {})
        real_width_m = widths_map.get(cls_name, widths_map.get("default", 1.8))
        focal_px = float(self.cfg.get("default_camera_focal_length_px", frame_w * 0.9))

        box_w = max(1.0, box[2] - box[0])
        dist_m = (real_width_m * focal_px) / box_w

        # Bù dốc/góc pitch (nếu đầu xe chúi xuống khi phanh, khoảng cách quang học cần hiệu chỉnh)
        if abs(imu_pitch_rad) > 0.01:
            dist_m = dist_m * math.cos(imu_pitch_rad)

        return max(0.5, min(150.0, float(dist_m)))

    def check(
        self, 
        tracks, 
        frame_w: int, 
        frame_h: int,
        ego_speed_kmh: Optional[float] = None,
        ego_lane_polygon: Optional[List[Tuple[int, int]]] = None,
        imu_pitch_rad: float = 0.0,
        imu_pitch_rate: float = 0.0,
        timestamp: Optional[float] = None
    ) -> List[Tuple[Any, float]]:
        """
        Kiểm tra va chạm và trả về danh sách các (Track, TTC_hoặc_rate) đang nguy hiểm.
        Giữ tương thích ngược với danh sách tuple (track, rate) cho các caller cũ.
        """
        # 1. Kẹt xe tốc độ thấp: Tắt cảnh báo khi xe chủ di chuyển < 10 km/h để chống spam
        min_speed_kph = self.cfg.get("min_speed_suppress_kph", 10.0)
        if ego_speed_kmh is not None and ego_speed_kmh < min_speed_kph:
            self._warning_counters.clear()
            self._active_warnings.clear()
            return []

        # 2. Bỏ qua nếu camera rung lắc mạnh do ổ gà / gờ giảm tốc
        if abs(imu_pitch_rate) > 1.5:  # rad/s
            return list((item["track"], item["rate"]) for item in self._active_warnings.values())

        # 3. Xác định đa giác làn đường của mình
        if ego_lane_polygon is not None:
            lane_pixels = ego_lane_polygon
        else:
            # Fallback polygon cũ
            from .utils import polygon_percent_to_pixels
            lane_pixels = polygon_percent_to_pixels(self.lane_polygon_percent, frame_w, frame_h)

        now_ts = timestamp or 0.0
        early_ttc = self.cfg.get("early_warning_ttc_sec", 2.5)
        urgent_ttc = self.cfg.get("urgent_warning_ttc_sec", 1.5)

        raw_triggered = {}

        for track in tracks:
            if track.cls_name not in ("car", "truck", "bus", "motorbike"):
                continue

            # Chỉ xét vật thể nằm TRONG làn của mình
            point = box_bottom_center(track.current_box)
            if not point_in_polygon(point, lane_pixels):
                continue

            tid = track.id
            box = track.current_box
            measured_d = self.estimate_distance_pinhole(box, track.cls_name, frame_w, frame_h, imu_pitch_rad)

            dt = max(0.01, now_ts - self._last_timestamps.get(tid, now_ts - 0.04))
            self._last_timestamps[tid] = now_ts

            if tid not in self._distance_filters:
                self._distance_filters[tid] = DistanceKalmanFilter(initial_d=measured_d)

            kf = self._distance_filters[tid]
            smooth_d, v_rel = kf.update(measured_d, dt=dt)

            # v_rel < 0 nghĩa là khoảng cách đang thu hẹp (đang tiến lại gần nhau)
            # TTC = D / |v_rel|
            ttc = float("inf")
            if v_rel < -0.5:  # Thu hẹp ít nhất 0.5 m/s (~1.8 km/h)
                ttc = smooth_d / abs(v_rel)

            # Heuristic growth rate tương thích ngược
            growth_rate = track.growth_rate(config.COLLISION_MIN_TRACK_LEN)

            # Điều kiện kích hoạt: TTC <= ngưỡng sớm HOẶC kích thước hộp tăng nhanh đột biến
            is_danger = (ttc <= early_ttc) or (growth_rate > config.COLLISION_GROWTH_RATE_THRESHOLD)

            if is_danger:
                severity = "critical" if ttc <= urgent_ttc else "warning"
                raw_triggered[tid] = {
                    "track": track,
                    "rate": growth_rate,
                    "ttc": round(ttc, 2) if math.isfinite(ttc) else 2.0,
                    "distance_m": round(smooth_d, 1),
                    "relative_speed_ms": round(v_rel, 2),
                    "severity": severity
                }

        # 4. Multi-frame Noise Filter (Chỉ kích hoạt sau khi duy trì ít nhất 2 frame)
        current_active = {}
        for tid, data in raw_triggered.items():
            self._warning_counters[tid] = self._warning_counters.get(tid, 0) + 1
            if self._warning_counters[tid] >= 2:
                current_active[tid] = data

        for tid in list(self._warning_counters.keys()):
            if tid not in raw_triggered:
                self._warning_counters[tid] = max(0, self._warning_counters[tid] - 1)
                if self._warning_counters[tid] == 0:
                    del self._warning_counters[tid]

        self._active_warnings = current_active
        # Trả về list các tuple (track, rate) để tương thích toàn diện với callers hiện hữu
        return [(item["track"], item["rate"]) for item in self._active_warnings.values()]

    def get_detailed_warnings(self) -> List[Dict[str, Any]]:
        """Trả về danh sách cảnh báo chi tiết có TTC, khoảng cách và cấp độ."""
        return list(self._active_warnings.values())
