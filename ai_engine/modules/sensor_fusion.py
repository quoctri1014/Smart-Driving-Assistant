"""
sensor_fusion.py
----------------
0.3 Sensor Fusion (Hợp nhất GPS + IMU bằng Extended Kalman Filter):
- Kết hợp GPS (kinh độ, vĩ độ, vận tốc, hướng di chuyển) và IMU (gia tốc kế, con quay yaw rate, góc nghiêng pitch).
- Bù trừ độ dốc cầu/dốc và phanh gấp bằng góc pitch: a_forward = a_measured - g * sin(pitch).
- Chế độ Dead Reckoning khi mất GPS (hầm, nhà cao tầng) với giới hạn thời gian tin cậy.
- Lọc vọt GPS (outlier) và kiểm tra gia tốc vật lý bất thường (> 1.2g ~ 11.76 m/s^2).
- Vùng trễ (deadband) khi xe đứng yên để tránh trôi GPS.
"""

import math
import time
from typing import Dict, Any, Optional, Tuple
import numpy as np


class SensorFusionEKF:
    def __init__(
        self,
        max_physical_accel_mps2: float = 11.76,  # 1.2g
        deadband_kph: float = 1.5,
        max_dead_reckoning_sec: float = 15.0
    ):
        self.max_accel = max_physical_accel_mps2
        self.deadband_mps = deadband_kph / 3.6
        self.max_dr_sec = max_dead_reckoning_sec
        self.g = 9.81  # Gia tốc trọng trường m/s^2

        # Trạng thái: [x (m), y (m), v (m/s), psi (rad)]
        self.state = np.zeros(4, dtype=np.float64)

        # Ma trận hiệp phương sai sai số P
        self.P = np.diag([5.0, 5.0, 1.0, 0.1])

        # Nhiễu quá trình Q
        self.Q = np.diag([0.2, 0.2, 0.5, 0.05])

        # Nhiễu đo lường GPS R
        self.R_gps = np.diag([4.0, 4.0, 0.4, 0.08])

        self.last_timestamp: Optional[float] = None
        self.last_gps_timestamp: Optional[float] = None
        self.in_dead_reckoning: bool = False
        self.gps_lost_duration: float = 0.0

    def predict(
        self,
        dt: float,
        accel_x: float = 0.0,
        yaw_rate: float = 0.0,
        pitch_deg: float = 0.0
    ):
        """
        Bước Dự Báo (Predict) với dữ liệu IMU:
        Bù trừ độ dốc/rung xóc từ góc pitch: a_true = a_x - g * sin(pitch)
        """
        if dt <= 0.0 or dt > 2.0:
            return

        pitch_rad = math.radians(pitch_deg)
        # Bù thành phần trọng lực khi lên/xuống dốc
        accel_compensated = accel_x - (self.g * math.sin(pitch_rad))

        # Kiểm tra ngưỡng vật lý bất thường
        if abs(accel_compensated) > self.max_accel:
            accel_compensated = math.copysign(self.max_accel, accel_compensated)

        x, y, v, psi = self.state

        # Cập nhật chuyển động học
        new_v = max(0.0, v + accel_compensated * dt)
        if new_v < self.deadband_mps and abs(accel_compensated) < 0.2:
            new_v = 0.0

        new_psi = (psi + yaw_rate * dt) % (2 * math.pi)
        new_x = x + new_v * math.cos(new_psi) * dt
        new_y = y + new_v * math.sin(new_psi) * dt

        self.state = np.array([new_x, new_y, new_v, new_psi])

        # Jacobian ma trận chuyển trạng thái F
        F = np.eye(4)
        F[0, 2] = math.cos(new_psi) * dt
        F[0, 3] = -new_v * math.sin(new_psi) * dt
        F[1, 2] = math.sin(new_psi) * dt
        F[1, 3] = new_v * math.cos(new_psi) * dt

        self.P = F @ self.P @ F.T + self.Q * dt

    def update_gps(
        self,
        gps_x: float,
        gps_y: float,
        gps_speed_mps: float,
        gps_heading_rad: float,
        current_time: float
    ):
        """
        Bước Cập Nhật (Update) khi nhận được gói tin GPS hợp lệ
        """
        # Kiểm tra nhảy vọt GPS (outlier rejection)
        estimated_speed = self.state[2]
        if abs(gps_speed_mps - estimated_speed) > (self.max_accel * 3.0) and estimated_speed > 2.0:
            # Nghi ngờ GPS nhảy sóng (Multipath), hạ trọng số
            R = self.R_gps * 5.0
        else:
            R = self.R_gps

        z = np.array([gps_x, gps_y, max(0.0, gps_speed_mps), gps_heading_rad % (2 * math.pi)])
        H = np.eye(4)

        y_res = z - self.state
        # Chuẩn hóa góc chênh lệch heading vào [-pi, pi]
        y_res[3] = (y_res[3] + math.pi) % (2 * math.pi) - math.pi

        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.state = self.state + K @ y_res
        self.state[2] = max(0.0, self.state[2])
        self.P = (np.eye(4) - K @ H) @ self.P

        self.last_gps_timestamp = current_time
        self.in_dead_reckoning = False
        self.gps_lost_duration = 0.0

    def process_telemetry(
        self,
        timestamp: float,
        gps_data: Optional[Dict[str, Any]] = None,
        imu_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Xử lý đồng bộ 1 chu kỳ cảm biến.
        """
        if self.last_timestamp is None:
            self.last_timestamp = timestamp
            if gps_data and gps_data.get("valid"):
                self.state[2] = gps_data.get("speed_kph", 0.0) / 3.6
            return self.get_fused_state()

        dt = timestamp - self.last_timestamp
        self.last_timestamp = timestamp

        accel_x = imu_data.get("accel_x", 0.0) if imu_data else 0.0
        yaw_rate = imu_data.get("yaw_rate", 0.0) if imu_data else 0.0
        pitch_deg = imu_data.get("pitch_deg", 0.0) if imu_data else 0.0

        # 1. Dự báo trạng thái qua IMU
        self.predict(dt=dt, accel_x=accel_x, yaw_rate=yaw_rate, pitch_deg=pitch_deg)

        # 2. Cập nhật đo lường GPS nếu có tín hiệu hợp lệ
        if gps_data and gps_data.get("valid", True) and gps_data.get("latitude") is not None:
            # Chuyển đổi tọa độ tham chiếu cục bộ (m)
            gps_x = gps_data.get("local_x", self.state[0])
            gps_y = gps_data.get("local_y", self.state[1])
            gps_speed = gps_data.get("speed_kph", 0.0) / 3.6
            gps_heading = math.radians(gps_data.get("heading_deg", 0.0))

            self.update_gps(gps_x, gps_y, gps_speed, gps_heading, current_time=timestamp)
        else:
            # Mất tín hiệu GPS -> Chuyển sang Dead Reckoning
            self.in_dead_reckoning = True
            if self.last_gps_timestamp:
                self.gps_lost_duration = timestamp - self.last_gps_timestamp
            else:
                self.gps_lost_duration += dt

            # Tăng độ bất định P khi chạy Dead Reckoning
            self.P[0, 0] += 0.5 * dt
            self.P[1, 1] += 0.5 * dt
            self.P[2, 2] += 0.2 * dt

        return self.get_fused_state()

    def get_fused_state(self) -> Dict[str, Any]:
        speed_mps = float(self.state[2])
        speed_kph = round(speed_mps * 3.6, 1)
        heading_deg = round(math.degrees(self.state[3]) % 360, 1)

        # Đánh giá độ tin cậy dựa trên thời gian mất GPS
        confidence = 1.0
        if self.in_dead_reckoning:
            confidence = max(0.2, round(1.0 - (self.gps_lost_duration / self.max_dr_sec), 2))

        return {
            "speed_kph": speed_kph,
            "speed_mps": round(speed_mps, 2),
            "heading_deg": heading_deg,
            "local_x_m": round(float(self.state[0]), 2),
            "local_y_m": round(float(self.state[1]), 2),
            "in_dead_reckoning": self.in_dead_reckoning,
            "gps_lost_seconds": round(self.gps_lost_duration, 1),
            "confidence": confidence,
            "speed_uncertainty_kph": round(math.sqrt(self.P[2, 2]) * 3.6, 2)
        }
