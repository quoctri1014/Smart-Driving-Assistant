"""Regression tests for the twelve-feature data flow; no model downloads."""
import csv
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
import config
from modules.tracker import Track, SimpleTracker
from modules.zone_manager import ZoneManager
from modules.violation_manager import ViolationManager
from modules.speed_estimator import SpeedEstimator
from modules.speed_recommendation import recommend_speed
from modules.safe_distance_calculator import SafeDistanceCalculator
from modules.sign_detector import SignDetector
from modules.helmet_checker import HelmetChecker
from modules.seatbelt_checker import SeatbeltChecker
from modules.driving_timer import DrivingTimer


def test_zone_density_is_current_vehicles_not_passage_total():
    zones = ZoneManager({"all": [(0, 0), (1, 0), (1, 1), (0, 1)]})
    car = Track(1, (10, 10, 30, 30), "car")
    person = Track(2, (40, 10, 50, 30), "person")
    zones.update([car, person], 100, 100)
    zones.update([car, person], 100, 100)
    assert zones.counts == {"all": 2}
    assert zones.vehicle_occupancy == {"all": 1}
    zones.update([], 100, 100)
    assert zones.vehicle_occupancy == {"all": 0}
    assert zones.current_zones == {}
    assert zones.counts == {"all": 2}


def test_speed_requires_calibration_and_uses_elapsed_time():
    car = Track(1, (0, 0, 20, 20), "car")
    assert SpeedEstimator(pixels_per_meter=None).update([car], 1) == {}
    estimator = SpeedEstimator(fps=25, pixels_per_meter=10)
    assert estimator.update([car], 1, timestamp=10) == {}
    car.update((100, 0, 120, 20), 2)
    assert estimator.update([car], 2, timestamp=12)[1] == 18
    assert estimator.update([car], 3, timestamp=12) == {}


def test_collision_growth_is_per_second():
    track = Track(1, (0, 0, 10, 10), "car", timestamp=0)
    track.update((0, 0, 10, 15), 2, timestamp=2)
    assert track.growth_rate(2) == pytest.approx(0.25)


def test_tracker_uses_second_candidate_instead_of_creating_new_identity():
    tracker = SimpleTracker()
    tracker.update([((0, 0, 100, 100), "car"), ((50, 0, 150, 100), "car")], 1)
    tracks = tracker.update([((10, 0, 110, 100), "car"), ((20, 0, 120, 100), "car")], 2)
    assert {track.id for track in tracks} == {1, 2}


def test_driver_timer_survives_reconnect(monkeypatch):
    import asyncio
    from backend.app.websocket import connection_manager
    class Socket:
        def __init__(self, token=None):
            self.query_params = {"timer_token": token}
            self.messages = []
        async def accept(self):
            pass
        async def send_json(self, message):
            self.messages.append(message)
    monkeypatch.setattr(connection_manager, "DriverPipelineSession", lambda: SimpleNamespace(
        driving_timer=DrivingTimer(), close=lambda: None))
    manager = connection_manager.ConnectionManager()
    first = Socket()
    asyncio.run(manager.connect_driver(first))
    timer = manager.get_driver_session(first).driving_timer
    token = first.messages[0]["timer_token"]
    timer.start_break()
    manager.disconnect(first)
    second = Socket(token)
    asyncio.run(manager.connect_driver(second))
    assert manager.get_driver_session(second).driving_timer is timer
    assert timer.update()["is_resting"]
    manager.disconnect(second)


def test_safe_distance_uses_ego_speed_and_preserves_zero_gap():
    calculator = SafeDistanceCalculator()
    warnings = [(SimpleNamespace(id=1), 0.8)]
    assert calculator.calculate(warnings, {1: 50}) is None
    result = calculator.calculate(warnings, {1: 0}, ego_speed_kmh=90, estimated_distance_m=0)
    assert result["recommended_distance_m"] >= 50
    assert result["estimated_distance_m"] == 0
    assert result["recommended_speed_kmh"] == 0
    advice = recommend_speed(90, 0, sign_speed_limit=80, safe_distance_speed=0)
    assert advice["recommended_speed"] == 0


@pytest.mark.parametrize("state,count", [(None, 0), (True, 0), (False, 1)])
def test_helmet_violation_triggers_ocr_and_csv(tmp_path, state, count):
    person = Track(1, (20, 0, 60, 80), "person")
    person.helmet_status = state
    bike = Track(2, (10, 50, 70, 100), "motorbike")
    reader = Mock()
    reader.read_plate.return_value = "59A12345"
    manager = ViolationManager(str(tmp_path / "violations.csv"))
    records = manager.process_frame([bike], [person], 1, frame=np.zeros((100, 100, 3)), plate_reader=reader)
    assert len(records) == count
    assert reader.read_plate.call_count == count
    if count:
        assert records[0].plate_text == "59A12345"
        assert manager.process_frame([bike], [person], 1000) == []
        with open(manager.export_path, encoding="utf-8") as source:
            assert len(list(csv.DictReader(source))) == 1


def test_late_plate_enriches_same_violation(tmp_path):
    person = Track(1, (20, 0, 60, 80), "person")
    person.helmet_status = False
    bike = Track(2, (10, 50, 70, 100), "motorbike")
    manager = ViolationManager(str(tmp_path / "violations.csv"))
    manager.process_frame([bike], [person], 1)
    bike.plate_text = "59A12345"
    assert manager.process_frame([bike], [person], 10) == []
    with open(manager.export_path, encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 1
    assert rows[0]["plate_text"] == bike.plate_text


def test_pedestrian_is_not_helmet_violation():
    person = Track(1, (0, 0, 10, 10), "person")
    person.helmet_status = False
    assert ViolationManager().process_frame([], [person], 1) == []


def test_shared_sign_labels_provide_speed_not_arbitrary_class_ids():
    detector = SignDetector()
    assert detector.detect(None, [{"cls_name": "speed_limit_50", "conf": 0.9}])["speed_limit"] == 50
    assert not detector.detect(None, [{"cls_name": "class_50", "conf": 0.9}])["detected"]
    assert not detector.detect(None, [{"cls_name": "speed_limit_50", "conf": 0.1}])["detected"]


def test_red_circle_is_not_confirmed_speed_sign():
    import cv2
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(frame, (100, 100), 25, (0, 0, 255), 5)
    result = SignDetector().detect(frame)
    assert result["speed_limit"] is None
    assert result["type"] != "speed_limit"


def test_shared_helmet_detections_without_separate_model(tmp_path):
    checker = HelmetChecker(str(tmp_path / "missing.pt"))
    assert checker.check(None, (0, 0, 100, 200), [
        {"cls_name": "no_helmet", "conf": 0.9, "box": (20, 10, 60, 50)}]) is False
    assert checker.check(None, (0, 0, 100, 200), []) is None


def test_missing_seatbelt_model_is_unknown(tmp_path):
    status = SeatbeltChecker(str(tmp_path / "missing.pt")).check(None)
    assert status["seatbelt_on"] is None
    assert status["confidence"] == 0


def test_timer_four_hours_and_short_break_not_driving_time(monkeypatch):
    now = [0.0]
    timer = DrivingTimer(clock=lambda: now[0])
    now[0] = 230 * 60
    assert timer.update()["alert_level"] == "reminder"
    timer.start_break()
    now[0] += 10 * 60
    assert timer.update()["continuous_minutes"] == 230
    timer.end_break()
    assert timer.update()["continuous_minutes"] == 230
    now[0] += 10 * 60
    assert timer.update()["should_rest"]
    timer.start_break()
    now[0] += 15 * 60
    assert timer.update()["continuous_minutes"] == 0
    timer.end_break()
    assert timer.update()["continuous_minutes"] == 0


def test_combined_fatigue_and_long_drive_escalates():
    now = [0.0]
    timer = DrivingTimer(clock=lambda: now[0])
    now[0] = 235 * 60
    assert timer.combined_alert_level("warning") == "critical"


def test_backend_pipeline_routes_shared_detections_and_retains_sign(monkeypatch, tmp_path):
    import threading
    from backend.app.core import pipeline_runner
    detector = Mock()
    detector.detect.side_effect = [
        [{"box": (20, 20, 50, 60), "cls_name": "car", "conf": .9},
         {"box": (70, 10, 80, 20), "cls_name": "speed_limit_50", "conf": .9}],
        [],
    ]
    models = SimpleNamespace(detector=detector, plate_reader=None, helmet_checker=None,
                             sign_detector=SignDetector(), inference_lock=threading.Lock())
    monkeypatch.setattr(pipeline_runner, "SharedAIModels", lambda: models)
    session = pipeline_runner.PipelineSession()
    session.violation_manager.export_path = str(tmp_path / "session.csv")
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    first = session.process_frame(frame, vehicle_speed=60)
    second = session.process_frame(frame, vehicle_speed=60)
    assert detector.detect.call_count == 2  # One detector pass per frame.
    assert len(first.vehicles) == 1  # Sign must not become a vehicle track.
    assert first.vehicles[0].speed_kmh is None
    assert second.speed_advice.recommended_speed == 50
    assert not second.vehicles
    assert sum(second.zone_occupancy.values()) == 0


def test_cabin_alert_includes_seatbelt_without_drowsiness(monkeypatch):
    from modules import driver_monitor
    monkeypatch.setattr(driver_monitor, "DrowsinessDetector", lambda: SimpleNamespace(
        detect=lambda frame: {"alert_level": "normal"}, close=lambda: None))
    monkeypatch.setattr(driver_monitor, "SeatbeltChecker", lambda: SimpleNamespace(
        check=lambda frame: {"seatbelt_on": False, "confidence": .9}))
    session = driver_monitor.DriverPipelineSession()
    assert session.process_driver_frame(None)["combined_alert_level"] == "warning"
    session.seatbelt_checker.check = lambda frame: {"seatbelt_on": None}
    assert session.process_driver_frame(None)["combined_alert_level"] == "normal"


def test_shared_plate_localization_does_not_load_second_yolo(monkeypatch):
    from plate.plate_reader import PlateReader
    monkeypatch.setattr(config, "ROAD_MODEL_SHARED_CLASSES", True)
    reader = PlateReader(ocr_reader=Mock())
    assert reader.detector is None
    result = reader.detect_plates(np.zeros((100, 100, 3), dtype=np.uint8), shared_detections=[
        {"cls_name": "license_plate", "conf": .9, "box": (10, 10, 40, 30)},
        {"cls_name": "car", "conf": .9, "box": (0, 0, 100, 100)}])
    assert len(result) == 1
    assert result[0]["crop"].shape == (20, 30, 3)
