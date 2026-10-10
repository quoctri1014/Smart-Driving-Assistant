import pytest
import math
import numpy as np

from ai_engine.modules.sensor_fusion import SensorFusionEKF


def test_sensor_fusion_gps_update():
    ekf = SensorFusionEKF()
    # Khởi tạo chu kỳ đầu tiên
    telemetry = ekf.process_telemetry(
        timestamp=100.0,
        gps_data={"valid": True, "latitude": 21.0285, "speed_kph": 60.0, "heading_deg": 90.0, "local_x": 0.0, "local_y": 0.0}
    )
    assert abs(telemetry["speed_kph"] - 60.0) < 1.0
    assert not telemetry["in_dead_reckoning"]

    # Cập nhật tiếp với GPS
    telemetry2 = ekf.process_telemetry(
        timestamp=101.0,
        gps_data={"valid": True, "latitude": 21.0286, "speed_kph": 62.0, "heading_deg": 90.0, "local_x": 17.0, "local_y": 0.0},
        imu_data={"accel_x": 0.5, "yaw_rate": 0.0, "pitch_deg": 0.0}
    )
    assert 58.0 <= telemetry2["speed_kph"] <= 65.0
    assert not telemetry2["in_dead_reckoning"]


def test_pitch_slope_compensation():
    ekf = SensorFusionEKF()
    ekf.process_telemetry(100.0, gps_data={"valid": True, "speed_kph": 50.0})

    # Xe lên dốc 10 độ, cảm biến trọng lực tác động lên trục x:
    # a_measured = g * sin(10 deg) ~ 9.81 * 0.1736 = 1.70 m/s^2 trong khi xe thực tế chạy đều (a_true = 0)
    pitch_angle = 10.0
    g_component = 9.81 * math.sin(math.radians(pitch_angle))

    # Cung cấp gia tốc đo được đúng bằng thành phần dốc -> EKF phải bù trừ và giữ tốc độ ổn định
    ekf.predict(dt=1.0, accel_x=g_component, yaw_rate=0.0, pitch_deg=pitch_angle)
    speed_kph = ekf.get_fused_state()["speed_kph"]
    assert abs(speed_kph - 50.0) < 1.5


def test_dead_reckoning_on_gps_loss():
    ekf = SensorFusionEKF(max_dead_reckoning_sec=10.0)
    ekf.process_telemetry(100.0, gps_data={"valid": True, "speed_kph": 40.0})

    # Mất GPS trong 3 giây liên tiếp, xe tiếp tục chạy với IMU đo được gia tốc 0
    for t in [101.0, 102.0, 103.0]:
        state = ekf.process_telemetry(t, gps_data=None, imu_data={"accel_x": 0.0, "pitch_deg": 0.0})
        assert state["in_dead_reckoning"] is True

    assert state["gps_lost_seconds"] == pytest.approx(3.0, 0.1)
    # Tốc độ vẫn được duy trì qua dead reckoning
    assert abs(state["speed_kph"] - 40.0) < 2.0
    # Độ tin cậy giảm nhẹ theo thời gian mất GPS
    assert state["confidence"] < 1.0


def test_deadband_vehicle_stop():
    ekf = SensorFusionEKF(deadband_kph=1.5)
    ekf.state[2] = 0.3 # 0.3 m/s = 1.08 km/h (< 1.5 km/h)
    ekf.predict(dt=1.0, accel_x=0.0, yaw_rate=0.0, pitch_deg=0.0)
    # Vùng trễ phải triệt tiêu vận tốc nhỏ để chống trôi xe khi dừng đèn đỏ
    assert ekf.get_fused_state()["speed_kph"] == 0.0
