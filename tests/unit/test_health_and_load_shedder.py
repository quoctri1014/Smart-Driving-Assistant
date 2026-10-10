import pytest
import numpy as np

from ai_engine.modules.health_monitor import SensorHealthMonitor
from ai_engine.modules.load_shedder import AdaptiveLoadShedder


def test_health_monitor_camera_obstructed():
    monitor = SensorHealthMonitor()
    # Khung hình tối đen hoàn toàn (bị che ống kính)
    black_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    status = monitor.evaluate_system_health(black_frame, current_time=10.0)
    assert status["healthy"] is False
    assert status["camera_status"] == "OBSTRUCTED"
    assert "vehicle_detection" in status["disabled_modules"]
    assert "collision_warning" in status["disabled_modules"]
    assert status["graceful_degradation_active"] is True


def test_health_monitor_frozen_frame():
    monitor = SensorHealthMonitor(freeze_duration_threshold_sec=1.0)
    # Khung hình có hoa văn tự nhiên (variance > 15) nhưng bị đứng hình giống hệt nhau qua 2 giây
    rng = np.random.RandomState(42)
    static_frame = rng.randint(40, 220, (480, 640, 3), dtype=np.uint8)

    monitor.evaluate_system_health(static_frame, current_time=0.0)
    monitor.evaluate_system_health(static_frame, current_time=0.5)
    frozen_status = monitor.evaluate_system_health(static_frame, current_time=2.0)

    assert frozen_status["camera_status"] == "FROZEN"
    assert frozen_status["graceful_degradation_active"] is True


def test_adaptive_load_shedder_invariants():
    shedder = AdaptiveLoadShedder(overload_threshold_ms=100.0, recovery_threshold_ms=60.0)

    # Khi độ trễ bình thường (30ms) -> NORMAL
    for _ in range(10):
        shedder.record_frame_latency(30.0)
    assert shedder.state == "NORMAL"
    assert shedder.scale_factor == 1.0
    assert shedder.should_process_module("plate_reader") is True

    # Khi độ trễ vọt lên cao (> 100ms) -> OVERLOADED
    for _ in range(10):
        shedder.record_frame_latency(150.0)
    assert shedder.state == "OVERLOADED"
    assert shedder.scale_factor == 0.75

    # NGUYÊN TẮC BẢO VỆ TUYỆT ĐỐI:
    # Module an toàn sinh mạng (TTC & DMS) KHÔNG BAO GIỜ bị cắt giảm khi quá tải
    assert shedder.should_process_module("collision_warning") is True
    assert shedder.should_process_module("drowsiness_detector") is True
    assert shedder.should_process_module("vehicle_detection") is True
