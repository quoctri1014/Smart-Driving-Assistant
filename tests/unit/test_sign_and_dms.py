"""
test_sign_and_dms.py
--------------------
Unit tests cho SignRecognition (5-frame voting) và DrowsinessDetector (calibration).
"""

import numpy as np
import cv2
import pytest
from ai_engine.modules.sign_recognition import SignRecognition, _detect_speed_sign_heuristic
from ai_engine.modules.drowsiness_detector import DrowsinessDetector


def test_speed_sign_voting_logic():
    sign_rec = SignRecognition()
    
    # Tạo 1 ảnh giả lập biển tròn viền đỏ nền trắng
    fake_frame = np.zeros((300, 300, 3), dtype=np.uint8)
    # Vẽ nền đường
    fake_frame[:] = (100, 100, 100)
    # Vẽ viền đỏ tròn ở giữa (BGR: Đỏ = [0, 0, 220])
    cv2.circle(fake_frame, (150, 150), 50, (0, 0, 230), thickness=8)
    # Vẽ nền trắng bên trong
    cv2.circle(fake_frame, (150, 150), 42, (255, 255, 255), thickness=-1)
    
    # Đưa vào 1 frame: chưa đủ 5 frame voting nên confirmed_by_voting = False
    res1 = sign_rec.read_speed_limit_sign([], fake_frame)
    assert res1["confirmed_by_voting"] is False
    
    # Bơm tiếp qua 5 frame
    res_final = None
    for _ in range(5):
        res_final = sign_rec.read_speed_limit_sign([], fake_frame)
        
    # Sau đủ frame voting -> chốt tốc độ giới hạn
    assert res_final is not None
    assert res_final["confirmed_by_voting"] is True
    assert res_final["speed_limit"] in (50, 60, 80, 100)


def test_drowsiness_detector_calibration_and_mar():
    dms = DrowsinessDetector()
    
    # Kiểm tra biến hiệu chuẩn động được khởi tạo
    assert hasattr(dms, "is_calibrated")
    assert hasattr(dms, "baseline_ear")
    assert hasattr(dms, "ear_threshold")
    
    # Frame rỗng không có mặt -> face_detected = False
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res = dms.detect(blank_frame)
    assert res["face_detected"] is False
    assert res["alert_level"] == "normal"
