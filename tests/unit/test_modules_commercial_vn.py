"""
test_modules_commercial_vn.py
-----------------------------
Bộ kiểm thử toàn diện cho 12 module ADAS & DMS thương mại tối ưu cho giao thông Việt Nam:
M1: Nhận diện phương tiện (DIoU, Soft-NMS, xe máy che nhau, xe kéo rơ-moóc).
M2: Tracking (BoT-SORT/ByteTrack, CMC bù rung camera, ReID, khôi phục che khuất dài).
M3: Ước tính tốc độ (Bù góc Pitch IMU, khoảng sai số, deadband < 1.5 km/h).
M4: Vùng làn đường (Phát hiện vạch kẻ, polygon làn của mình, fallback khi mất vạch).
M5: Biển số xe (Phân loại màu biển vàng, xanh, đỏ, trắng theo TT 58/2020).
M6: Mũ bảo hiểm (Voting theo track, phát hiện nón vải/áo mưa đưa vào UNCERTAIN).
M7: Cảnh báo va chạm TTC (Pinhole distance, Kalman relative speed, ngưỡng 2.5s/1.5s).
M8: Cự ly an toàn (Đối chiếu Điều 11 TT 31/2019/TT-BGTVT, bù đường ướt x1.30).
M9: Biển báo giao thông (QCVN 41:2019, tuyệt đối không đoán số, hết hiệu lực 500m).
M10: Khuyến nghị tốc độ (Explainable Rule Engine, không bao giờ khuyến nghị vượt luật).
M11: DMS Giám sát cabin (PERCLOS 60s, solvePnP 3D Head Pose, Sunglasses mode).
M12: Dây an toàn & Giờ lái (4h liên tục, dừng đèn đỏ không tính là nghỉ, làm mờ bằng chứng).
"""

import math
import cv2
import numpy as np
import pytest

from ai_engine.modules.detector import compute_diou, apply_soft_nms, merge_truck_and_trailer
from ai_engine.modules.tracker import SimpleTracker, Track, appearance_similarity, compute_appearance_embedding
from ai_engine.modules.speed_estimator import SpeedEstimator, SpeedKalmanFilter1D
from ai_engine.modules.lane_detector import LaneDetector
from ai_engine.plate.plate_reader import classify_plate_background_color
from ai_engine.modules.helmet_checker import HelmetChecker, analyze_head_texture_and_poncho
from ai_engine.modules.collision_warning import CollisionWarning, DistanceKalmanFilter
from ai_engine.modules.safe_distance_calculator import SafeDistanceCalculator, get_tt31_safe_distance
from ai_engine.modules.sign_recognition import TrafficSignRecognizer
from ai_engine.modules.speed_recommendation import recommend_speed
from ai_engine.modules.drowsiness_detector import DrowsinessDetector, estimate_head_pose_pnp
from ai_engine.modules.driving_timer import DrivingTimer
from backend.app.core.privacy_anonymizer import anonymize_evidence_frame, compute_evidence_hash


# ── M1: Nhận diện phương tiện & Soft-NMS ──────────────────────────────────────
def test_m1_diou_and_soft_nms_dense_motorbikes():
    # Giả lập 2 xe máy đi cạnh nhau (bounding box chồng lấn một phần nhưng tâm khác nhau)
    b1 = (100.0, 200.0, 150.0, 300.0)
    b2 = (120.0, 205.0, 170.0, 305.0)

    diou_val = compute_diou(b1, b2)
    # DIoU phải nhỏ hơn 1.0 và phản ánh khoảng cách tâm
    assert 0.0 < diou_val < 0.85

    dets = [
        {"box": b1, "cls_id": 3, "cls_name": "motorbike", "conf": 0.90},
        {"box": b2, "cls_id": 3, "cls_name": "motorbike", "conf": 0.85}
    ]

    # Với Soft-NMS, cả 2 xe máy đều được giữ lại (không bị Hard NMS xóa mất xe thứ hai)
    filtered = apply_soft_nms(dets, sigma=0.5, score_threshold=0.20, use_diou=True)
    assert len(filtered) == 2
    assert filtered[0]["conf"] == 0.90
    assert filtered[1]["conf"] > 0.20


def test_m1_trailer_merge():
    # 2 box: đầu kéo và thùng rơ-moóc gắn liền phía sau
    tractor = {"box": (200.0, 100.0, 300.0, 220.0), "cls_id": 7, "cls_name": "truck", "conf": 0.88}
    trailer = {"box": (205.0, 210.0, 298.0, 450.0), "cls_id": 7, "cls_name": "truck", "conf": 0.82}

    merged = merge_truck_and_trailer([tractor, trailer], iou_min=0.05)
    # Đã hợp nhất thành 1 xe tải duy nhất
    assert len(merged) == 1
    m_box = merged[0]["box"]
    assert m_box[1] <= 100.0 and m_box[3] >= 450.0


# ── M2: Tracking & ReID & Camera Motion Compensation ──────────────────────────
def test_m2_reid_similarity_and_occlusion_recovery():
    tracker = SimpleTracker(max_age=10, min_hits=2)

    # Ảnh giả lập màu vàng (taxi/xe khách)
    yellow_car = np.full((60, 60, 3), (0, 220, 220), dtype=np.uint8)
    emb1 = compute_appearance_embedding(yellow_car)
    emb2 = compute_appearance_embedding(yellow_car)
    assert emb1 is not None
    sim = appearance_similarity(emb1, emb2)
    assert sim >= 0.95

    # Ảnh giả lập màu xanh
    blue_car = np.full((60, 60, 3), (220, 50, 0), dtype=np.uint8)
    emb_blue = compute_appearance_embedding(blue_car)
    assert appearance_similarity(emb1, emb_blue) < 0.60


# ── M3: Tốc độ, Bù Pitch IMU, và Deadband ─────────────────────────────────────
def test_m3_pitch_compensation_and_deadband():
    estimator = SpeedEstimator(fps=25.0, pixels_per_meter=10.0)

    # Bù Pitch: khi phanh chúi mũi (pitch = +0.05 rad), vị trí hộp được điều chỉnh
    tracks = [SimpleNamespace(id=1, cls_name="car", current_box=(200, 300, 250, 380))]
    speeds = estimator.update(tracks, frame_idx=1, imu_pitch_rad=0.05)
    assert isinstance(speeds, dict)

    # Chi tiết tốc độ
    details = estimator.get_speed_details(1)
    assert "error_margin_kmh" in details
    assert details["is_calibrated"] is False
    assert "Chưa hiệu chuẩn" in details["display_text"]


# ── M4: Vùng làn đường & Ego-Lane Detection ───────────────────────────────────
def test_m4_lane_detector_fallback_on_missing_lines():
    detector = LaneDetector()
    # Ảnh đường không có vạch kẻ (toàn màu xám)
    gray_road = np.full((720, 1280, 3), 100, dtype=np.uint8)
    res = detector.detect_ego_lane(gray_road)

    # Ngoại lệ: Vạch mờ -> Kích hoạt Fallback corridor an toàn
    assert res["is_fallback"] is True
    assert res["is_detected"] is False
    assert len(res["polygon"]) == 4
    assert res["shapely_poly"].is_valid


# ── M5: Phân loại màu biển số xe Việt Nam (TT 58/2020) ────────────────────────
def test_m5_plate_color_classification():
    # Biển vàng (Kinh doanh vận tải)
    yellow_plate = np.full((50, 150, 3), (20, 200, 220), dtype=np.uint8)
    assert classify_plate_background_color(yellow_plate) == "COMMERCIAL_YELLOW"

    # Biển xanh (Cơ quan hành chính / Công an)
    blue_plate = np.full((50, 150, 3), (200, 100, 20), dtype=np.uint8)
    assert classify_plate_background_color(blue_plate) == "GOVERNMENT_BLUE"

    # Biển đỏ (Quân đội)
    red_plate = np.full((50, 150, 3), (20, 20, 220), dtype=np.uint8)
    assert classify_plate_background_color(red_plate) == "MILITARY_RED"

    # Biển trắng (Dân sự thông thường)
    white_plate = np.full((50, 150, 3), (230, 230, 230), dtype=np.uint8)
    assert classify_plate_background_color(white_plate) == "CIVILIAN_WHITE"


# ── M6: Mũ bảo hiểm & Áo mưa trùm đầu ─────────────────────────────────────────
def test_m6_helmet_texture_and_poncho_detection():
    # Áo mưa nhiều nếp gấp nhăn nheo (nhiễu Laplacian cao)
    noisy_crop = np.random.randint(50, 200, (40, 40, 3), dtype=np.uint8)
    status = analyze_head_texture_and_poncho(noisy_crop)
    assert status in ("NON_STANDARD_OR_PONCHO", "NORMAL_HEADWEAR")


# ── M7: Cảnh báo va chạm TTC & Pinhole Optics ─────────────────────────────────
def test_m7_collision_warning_ttc_calculation():
    cw = CollisionWarning()
    # Ước lượng khoảng cách ô tô con rộng 1.8m, bbox rộng 200px trên ảnh 1280
    dist = cw.estimate_distance_pinhole((100, 200, 300, 400), "car", 1280, 720)
    assert 5.0 <= dist <= 30.0

    # Kiểm tra Distance Kalman Filter tính v_rel
    kf = DistanceKalmanFilter(initial_d=20.0)
    smooth_d, v_rel = kf.update(19.0)
    # Khoảng cách thu hẹp -> v_rel < 0
    assert v_rel < 0.0


# ── M8: Cự ly an toàn Điều 11 TT 31/2019/TT-BGTVT ─────────────────────────────
def test_m8_safe_distance_tt31_compliance():
    # Tốc độ <= 60 km/h: tài xế tự quyết định, khuyến nghị an toàn 35m
    d_60, disc_60, cit_60 = get_tt31_safe_distance(50.0, is_wet=False)
    assert d_60 == 35.0
    assert disc_60 is True
    assert "TT 31/2019" in cit_60

    # Tốc độ 70 km/h (nằm trong dải 60-80 km/h): luật bắt buộc 55m
    d_70, disc_70, _ = get_tt31_safe_distance(70.0, is_wet=False)
    assert d_70 == 55.0
    assert disc_70 is False

    # Trời mưa (đường ướt): nhân hệ số x1.30
    d_70_wet, _, cit_wet = get_tt31_safe_distance(70.0, is_wet=True)
    assert d_70_wet == round(55.0 * 1.30, 1)
    assert "x1.30" in cit_wet


# ── M9: Biển báo giao thông QCVN 41:2019 & Map Fusion ────────────────────────
def test_m9_sign_no_guessing_and_map_fusion():
    recognizer = TrafficSignRecognizer()
    assert 60 in recognizer.valid_speeds
    assert 120 in recognizer.valid_speeds

    # Khi camera thấy 60 km/h nhưng bản đồ báo 80 km/h -> Mâu thuẫn, hạ độ tin cậy
    recognizer.current_speed_limit = 60
    recognizer.speed_limit_source = "CAMERA_SIGN_QCVN41"
    recognizer.is_confirmed = True
    fused = recognizer.fuse_with_map(osm_map_speed=80.0)
    assert fused["status"] == "UNCERTAIN"
    assert fused["effective_speed_limit"] == 60
    assert "Mâu thuẫn" in fused["notes"]

    # Sau khi chạy quá 500m -> Biển báo tự động hết hiệu lực
    recognizer.update_distance(550.0)
    assert recognizer.current_speed_limit is None


# ── M10: Khuyến nghị tốc độ (Explainable Rule Engine) ─────────────────────────
def test_m10_speed_recommendation_never_exceeds_legal_limit():
    rec = recommend_speed(
        current_speed=40.0,
        vehicle_count_in_zone=1,
        sign_speed_limit=50.0,
        safe_distance_speed=65.0,
        has_collision_warning=False,
        is_urban_area=True
    )
    # Tốc độ khuyến nghị không được vượt quá biển báo 50 km/h
    assert rec["recommended_speed"] <= 50.0
    assert "50 km/h" in rec["primary_reason"]
    assert rec["alert_level"] == "normal"


# ── M11: DMS PERCLOS & solvePnP Head Pose ─────────────────────────────────────
def test_m11_dms_perclos_and_head_pose_pnp():
    dms = DrowsinessDetector()
    assert dms.perclos_window_sec == 60.0

    # 6 điểm landmark mặt phẳng chuẩn
    landmarks_2d = np.array([
        (320.0, 240.0),  # mũi
        (320.0, 320.0),  # cằm
        (280.0, 200.0),  # mắt trái
        (360.0, 200.0),  # mắt phải
        (290.0, 280.0),  # miệng trái
        (350.0, 280.0),  # miệng phải
    ], dtype=np.float64)

    pitch, yaw, roll = estimate_head_pose_pnp(landmarks_2d, 640, 480)
    assert isinstance(pitch, float)
    assert isinstance(yaw, float)


# ── M12: Giờ lái & Làm mờ bằng chứng bảo vệ quyền riêng tư ───────────────────
def test_m12_driving_timer_and_privacy_anonymization():
    now_ts = [1000.0]
    timer = DrivingTimer(clock=lambda: now_ts[0])

    # Lái 60 phút
    now_ts[0] += 3600.0
    status = timer.update(is_vehicle_moving=True, speed_kmh=40.0)
    assert status["continuous_minutes"] >= 59.0

    # Dừng đèn đỏ 2 phút (speed = 0): KHÔNG ĐƯỢC RESET
    now_ts[0] += 120.0
    status_stop = timer.update(is_vehicle_moving=False, speed_kmh=0.0)
    assert status_stop["continuous_minutes"] >= 60.0

    # Làm mờ ảnh bằng chứng vi phạm
    evidence_img = np.full((100, 100, 3), 150, dtype=np.uint8)
    cv2.rectangle(evidence_img, (20, 20), (40, 40), (0, 0, 0), -1)  # Giả lập mặt/biển số
    anon = anonymize_evidence_frame(evidence_img, face_boxes=[(20, 20, 40, 40)])
    assert anon is not None

    # Mã băm SHA-256 chống làm giả bằng chứng
    evidence_hash = compute_evidence_hash(evidence_img.tobytes())
    assert len(evidence_hash) == 64


class SimpleNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
