"""
test_tracking_and_speed.py
--------------------------
Unit tests cho ByteTrack + Kalman 2D Tracker và SpeedEstimator.
"""

import numpy as np
import pytest
from ai_engine.modules.tracker import KalmanBoxTracker, SimpleTracker, Track
from ai_engine.modules.speed_estimator import SpeedEstimator, SpeedKalmanFilter1D


def test_kalman_box_tracker_prediction_and_update():
    box = (100.0, 100.0, 200.0, 200.0)
    tracker = KalmanBoxTracker(box)
    
    # Predict vị trí tiếp theo
    pred = tracker.predict()
    assert len(pred) == 4
    # Với vận tốc ban đầu = 0, vị trí dự đoán gần trùng với vị trí ban đầu
    assert abs(pred[0] - box[0]) < 5.0
    
    # Update với box dịch chuyển theo phương ngang
    new_box = (110.0, 100.0, 210.0, 200.0)
    tracker.update(new_box)
    state = tracker.get_state()
    assert state[0] > 100.0


def test_simple_tracker_association():
    tracker = SimpleTracker(max_age=10, min_hits=1)
    
    # Frame 1: 2 xe
    dets_frame1 = [
        ((100.0, 100.0, 200.0, 200.0), "car", 0.9),
        ((400.0, 150.0, 500.0, 250.0), "motorbike", 0.85)
    ]
    tracks1 = tracker.update(dets_frame1, frame_idx=1)
    assert len(tracks1) == 2
    id1, id2 = tracks1[0].id, tracks1[1].id
    
    # Frame 2: xe di chuyển nhẹ -> ID phải được duy trì liên tục (Không nhảy ID)
    dets_frame2 = [
        ((105.0, 102.0, 205.0, 202.0), "car", 0.9),
        ((404.0, 152.0, 504.0, 252.0), "motorbike", 0.88)
    ]
    tracks2 = tracker.update(dets_frame2, frame_idx=2)
    assert len(tracks2) == 2
    current_ids = {t.id for t in tracks2}
    assert id1 in current_ids
    assert id2 in current_ids


def test_speed_kalman_filter():
    kf = SpeedKalmanFilter1D(initial_speed=50.0)
    # Đo đạc có nhiễu dao động quanh 50 km/h: 53, 47, 52, 49
    measurements = [53.0, 47.0, 52.0, 49.0]
    results = [kf.update(m) for m in measurements]
    # Tốc độ sau lọc phải được làm mịn, không vọt lố
    assert all(45.0 <= r <= 55.0 for r in results)


def test_speed_estimator_integration():
    estimator = SpeedEstimator(fps=25.0)
    tracker = SimpleTracker()
    
    # Giả lập xe chạy qua 10 frame
    for f in range(1, 10):
        dets = [((200.0 + f * 5.0, 300.0 + f * 3.0, 300.0 + f * 5.0, 400.0 + f * 3.0), "car", 0.9)]
        active_tracks = tracker.update(dets, frame_idx=f)
        speeds = estimator.update(active_tracks, frame_idx=f, frame_w=1280, frame_h=720)
        
    assert len(speeds) > 0
    # Tốc độ ước tính phải nằm trong khoảng vật lý hợp lý
    assert all(0.0 <= spd <= 150.0 for spd in speeds.values())
