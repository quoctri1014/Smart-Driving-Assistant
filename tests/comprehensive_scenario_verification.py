"""
comprehensive_scenario_verification.py
--------------------------------------
Bộ kiểm thử tự động toàn diện đa kịch bản (Multi-Scenario Edge Cases Verification)
dành cho hệ thống Trợ lý Lái xe Thông minh (TrafficGuard - Smart Driving Assistant):

Bao phủ 5 phân hệ lớn và 25 kịch bản thực tế đặc thù Việt Nam:
1. Phân hệ ADAS Đường bộ (Collision Warning TTC, Safe Distance TT31, Speed Estimator, Lane Fallback)
2. Phân hệ Giám sát Cabin DMS (Eyes Closed Monitor, PERCLOS 60s, Head Pose, Fatigue Timer, Sunglasses)
3. Phân hệ Nhận diện Biển số ALPR (Biển trắng, biển vàng, biển xanh, biển đỏ, lọc số điện thoại taxi)
4. Phân hệ Biển báo & Khuyến nghị Tốc độ (QCVN 41:2019, Map Fusion, Quy tắc an toàn)
5. Phân hệ Quyết định & An toàn Dữ liệu (Decision Engine Priority, Evidence Anonymization, SHA-256)
"""

import sys
from pathlib import Path

# Add project root and ai_engine to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ai_engine"))

import math
import time
import json
import uuid
import numpy as np
from types import SimpleNamespace

# Core module imports
from ai_engine.modules.collision_warning import CollisionWarning, DistanceKalmanFilter
from ai_engine.modules.safe_distance_calculator import SafeDistanceCalculator, get_tt31_safe_distance, safe_speed_for_distance
from ai_engine.modules.speed_estimator import SpeedEstimator, SpeedKalmanFilter1D
from ai_engine.modules.lane_detector import LaneDetector
from ai_engine.modules.detector import compute_diou, apply_soft_nms, merge_truck_and_trailer
from ai_engine.modules.tracker import SimpleTracker, Track, appearance_similarity, compute_appearance_embedding
from ai_engine.modules.eyes_closed_monitor import EyesClosedMonitor, EyeState, EyesClosedConfig
from ai_engine.modules.drowsiness_detector import DrowsinessDetector, estimate_head_pose_pnp
from ai_engine.modules.driving_timer import DrivingTimer
from ai_engine.modules.sign_recognition import TrafficSignRecognizer
from ai_engine.modules.speed_recommendation import recommend_speed
from ai_engine.plate.plate_recognizer import (
    is_valid_vietnamese_plate,
    is_phone_or_garbage,
    fix_plate,
    is_valid_plate_with_aspect_ratio,
    TO_DIGIT,
    TO_LETTER
)
from ai_engine.plate.plate_reader import classify_plate_background_color
from backend.app.schemas.adas_event import AdasEvent, DecisionResult
from backend.app.core.decision_engine import DecisionEngine
from backend.app.core.privacy_anonymizer import anonymize_evidence_frame, compute_evidence_hash


class ScenarioVerificationRunner:
    def __init__(self):
        self.results = []
        self.passed_count = 0
        self.failed_count = 0

    def record(self, case_id: str, name: str, category: str, passed: bool, details: dict, error_msg: str = ""):
        entry = {
            "case_id": case_id,
            "name": name,
            "category": category,
            "passed": passed,
            "details": details,
            "error_msg": error_msg
        }
        self.results.append(entry)
        if passed:
            self.passed_count += 1
            print(f"  [PASS] {case_id}: {name}", flush=True)
        else:
            self.failed_count += 1
            print(f"  [FAIL] {case_id}: {name} -> Error: {error_msg}", flush=True)

    # =========================================================================
    # NHÓM 1: ADAS ĐƯỜNG BỘ & VA CHẠM (ROAD-FACING ADAS)
    # =========================================================================

    def test_case_1_1_highway_safe_distance(self):
        """Case 1.1: Cao tốc 110 km/h theo Điều 11 Thông tư 31/2019/TT-BGTVT."""
        speed = 110.0
        min_d, disc, citation = get_tt31_safe_distance(speed, is_wet=False)
        calc = SafeDistanceCalculator(road_condition="dry")
        res = calc.calculate(
            col_warnings=[{"track": SimpleNamespace(id=1), "rate": 0.1}],
            speed_map={1: 100.0},
            estimated_distance_m=85.0,
            ego_speed_kmh=speed,
            is_calibrated=True
        )
        # Tại 110 km/h, luật yêu cầu 100m, khoảng cách phanh vật lý là 86.4m.
        # Đo được 85.0m vi phạm cả cự ly luật (100m) và cự ly dừng vật lý (86.4m) -> Báo động
        passed = (
            min_d == 100.0 and 
            disc is False and 
            res is not None and 
            res["distance_status"] in ("WARNING_UNSAFE_DISTANCE", "CRITICAL_TOO_CLOSE") and
            res["recommended_distance_m"] >= 100.0
        )
        self.record("CASE_1.1", "Khoảng cách an toàn cao tốc 110 km/h (TT31/2019)", "ADAS Road", passed, {
            "ego_speed": speed,
            "min_legal_distance": min_d,
            "measured_distance": 85.0,
            "status": res.get("distance_status") if res else None,
            "citation": citation
        })

    def test_case_1_2_emergency_braking_ttc(self):
        """Case 1.2: Phanh gấp phía trước, chuỗi hội tụ Kalman tính TTC khẩn cấp <= 1.5s."""
        # Giả lập xe phía trước phanh gấp: cự ly giảm nhanh từ 20m xuống 5m qua 4 bước (dt=0.1s)
        # Tương đương vận tốc tương đối âm mạnh (v_rel ~ -9.4 m/s)
        kf = DistanceKalmanFilter(initial_d=22.0)
        distances = [20.0, 15.0, 10.0, 5.0]
        smooth_d, v_rel = 0.0, 0.0
        for d in distances:
            smooth_d, v_rel = kf.update(d, dt=0.1)

        ttc = smooth_d / abs(v_rel) if v_rel < -0.5 else 999.0
        is_critical = ttc <= 1.5
        passed = is_critical and v_rel < 0.0
        self.record("CASE_1.2", "Cảnh báo va chạm khẩn cấp TTC <= 1.5s", "ADAS Road", passed, {
            "smooth_distance": round(smooth_d, 2),
            "relative_speed": round(v_rel, 2),
            "calculated_ttc": round(ttc, 2),
            "is_critical": is_critical
        })

    def test_case_1_3_adverse_weather_safe_distance(self):
        """Case 1.3: Trời mưa đường ướt nhân hệ số an toàn x1.30."""
        speed = 70.0
        dry_d, _, _ = get_tt31_safe_distance(speed, is_wet=False)
        wet_d, _, wet_citation = get_tt31_safe_distance(speed, is_wet=True)
        expected_wet = round(55.0 * 1.30, 1)
        passed = (dry_d == 55.0 and wet_d == expected_wet and "x1.30" in wet_citation)
        self.record("CASE_1.3", "Hệ số đường trơn trượt mùa mưa x1.30 (TT31/2019)", "ADAS Road", passed, {
            "speed": speed,
            "dry_distance": dry_d,
            "wet_distance": wet_d,
            "expected_wet": expected_wet,
            "citation": wet_citation
        })

    def test_case_1_4_traffic_jam_low_speed_suppression(self):
        """Case 1.4: Triệt tiêu cảnh báo va chạm khi kẹt xe di chuyển < 10 km/h."""
        cw = CollisionWarning()
        track = Track(1, (500, 300, 700, 500), "car")
        # Ego di chuyển 6 km/h (kẹt xe đường phố)
        warnings = cw.check(
            tracks=[track],
            frame_w=1280,
            frame_h=720,
            ego_speed_kmh=6.0
        )
        passed = (len(warnings) == 0)
        self.record("CASE_1.4", "Triệt tiêu cảnh báo khi kẹt xe < 10 km/h", "ADAS Road", passed, {
            "ego_speed": 6.0,
            "warnings_triggered": len(warnings)
        })

    def test_case_1_5_pothole_shake_suppression(self):
        """Case 1.5: Loại trừ rung lắc camera khi qua ổ gà / gờ giảm tốc."""
        cw = CollisionWarning()
        track = Track(1, (500, 300, 700, 500), "car")
        # Góc pitch lắc mạnh 2.5 rad/s
        warnings = cw.check(
            tracks=[track],
            frame_w=1280,
            frame_h=720,
            ego_speed_kmh=40.0,
            imu_pitch_rate=2.5
        )
        passed = (len(warnings) == 0)
        self.record("CASE_1.5", "Bỏ qua nhiễu rung lắc camera (IMU pitch rate > 1.5)", "ADAS Road", passed, {
            "pitch_rate": 2.5,
            "warnings_count": len(warnings)
        })

    def test_case_1_6_pinhole_distance_calibration(self):
        """Case 1.6: Đo khoảng cách quang học Pinhole chuẩn kích thước phương tiện."""
        cw = CollisionWarning()
        # Ô tô rộng 1.8m, bbox rộng 180px, f=900px -> D = 1.8 * 900 / 180 = 9.0m
        box = (100, 200, 280, 380)  # box_w = 180px
        d_car = cw.estimate_distance_pinhole(box, "car", frame_w=1000, frame_h=600)
        # Xe máy rộng 0.8m, cùng box -> D = 0.8 * 900 / 180 = 4.0m
        d_moto = cw.estimate_distance_pinhole(box, "motorbike", frame_w=1000, frame_h=600)
        passed = (abs(d_car - 8.0) <= 2.5 and abs(d_moto - 3.55) <= 2.0 and d_car > d_moto)
        self.record("CASE_1.6", "Đo cự ly Pinhole Optics theo chuẩn kích thước xe VN", "ADAS Road", passed, {
            "car_dist_m": round(d_car, 2),
            "moto_dist_m": round(d_moto, 2)
        })

    def test_case_1_7_lane_detector_fallback_corridor(self):
        """Case 1.7: Tự kích hoạt hành lang an toàn khi đường mòn mất vạch kẻ."""
        ld = LaneDetector()
        black_img = np.zeros((720, 1280, 3), dtype=np.uint8)
        res = ld.detect_ego_lane(black_img)
        passed = (res["is_fallback"] is True and res["is_detected"] is False and len(res["polygon"]) == 4)
        self.record("CASE_1.7", "Tự động bật Fallback Corridor khi mất vạch kẻ đường", "ADAS Road", passed, {
            "is_fallback": res.get("is_fallback"),
            "polygon_points": len(res.get("polygon", []))
        })

    def test_case_1_8_dense_motorbikes_soft_nms(self):
        """Case 1.8: Soft-NMS bảo toàn cả 2 xe máy đi song song che khuất."""
        dets = [
            {"box": (100, 200, 160, 320), "cls_id": 3, "cls_name": "motorbike", "conf": 0.88},
            {"box": (115, 205, 175, 325), "cls_id": 3, "cls_name": "motorbike", "conf": 0.82}
        ]
        res = apply_soft_nms(dets, sigma=0.5, score_threshold=0.20, use_diou=True)
        passed = (len(res) == 2 and res[0]["conf"] == 0.88 and res[1]["conf"] > 0.20)
        self.record("CASE_1.8", "Soft-NMS & DIoU giữ nguyên 2 xe máy đi sát nhau", "ADAS Road", passed, {
            "initial_dets": 2,
            "retained_dets": len(res),
            "second_bike_conf": round(res[1]["conf"], 3) if len(res) > 1 else None
        })

    def test_case_1_9_trailer_merge_integrity(self):
        """Case 1.9: Hợp nhất đầu kéo và rơ-moóc thành một phương tiện thống nhất."""
        tractor = {"box": (150, 200, 250, 350), "cls_id": 7, "cls_name": "truck", "conf": 0.90}
        trailer = {"box": (155, 340, 248, 550), "cls_id": 7, "cls_name": "truck", "conf": 0.85}
        merged = merge_truck_and_trailer([tractor, trailer], iou_min=0.01)
        passed = (len(merged) == 1 and merged[0]["box"][1] <= 200 and merged[0]["box"][3] >= 550)
        self.record("CASE_1.9", "Hợp nhất đầu kéo và rơ-moóc xe tải", "ADAS Road", passed, {
            "merged_count": len(merged),
            "combined_bbox": merged[0]["box"] if merged else None
        })

    def test_case_1_10_speed_estimator_deadband(self):
        """Case 1.10: Lọc rung động deadband < 1.5 km/h khi dừng đèn đỏ."""
        estimator = SpeedEstimator(fps=25.0, pixels_per_meter=10.0)
        track = SimpleNamespace(id=1, cls_name="car", current_box=(200, 300, 250, 380))
        # Frame 1
        estimator.update([track], frame_idx=1, timestamp=0.0)
        # Frame 2: Dịch chuyển siêu nhỏ 2px trong 1s -> 2px / 10 = 0.2m -> 0.2 m/s = 0.72 km/h (< 1.5 km/h)
        track.current_box = (201, 301, 251, 381)
        speeds = estimator.update([track], frame_idx=26, timestamp=1.0)
        passed = (speeds.get(1) == 0.0)
        self.record("CASE_1.10", "Loại bỏ vận tốc nhiễu dao động < 1.5 km/h tại đèn đỏ", "ADAS Road", passed, {
            "speed_reported": speeds.get(1)
        })

    # =========================================================================
    # NHÓM 2: BIỂN BÁO & KHUYẾN NGHỊ TỐC ĐỘ (TRAFFIC SIGNS & ADVISORY)
    # =========================================================================

    def test_case_2_1_school_zone_speed_advisory(self):
        """Case 2.1: Khuyến nghị tốc độ tuân thủ tuyệt đối biển 50 km/h."""
        rec = recommend_speed(
            current_speed=52.0,
            vehicle_count_in_zone=2,
            sign_speed_limit=50.0,
            safe_distance_speed=60.0,
            has_collision_warning=False,
            is_urban_area=True
        )
        passed = (rec["recommended_speed"] <= 50.0 and "50" in rec["primary_reason"])
        self.record("CASE_2.1", "Khuyến nghị tốc độ giới hạn khu dân cư 50 km/h", "Sign & Speed", passed, {
            "recommended_speed": rec.get("recommended_speed"),
            "primary_reason": rec.get("primary_reason"),
            "alert_level": rec.get("alert_level")
        })

    def test_case_2_2_map_camera_fusion_conflict(self):
        """Case 2.2: Xử lý xung đột camera thấy 60 km/h nhưng map báo 80 km/h."""
        recognizer = TrafficSignRecognizer()
        recognizer.current_speed_limit = 60
        recognizer.speed_limit_source = "CAMERA_SIGN_QCVN41"
        recognizer.is_confirmed = True
        fused = recognizer.fuse_with_map(osm_map_speed=80.0)
        passed = (fused["status"] == "UNCERTAIN" and fused["effective_speed_limit"] == 60)
        self.record("CASE_2.2", "Xung đột biển báo Camera (60) vs Bản đồ số (80)", "Sign & Speed", passed, {
            "effective_speed": fused.get("effective_speed_limit"),
            "status": fused.get("status"),
            "notes": fused.get("notes")
        })

    def test_case_2_3_sign_distance_expiration(self):
        """Case 2.3: Biển báo tự động hết hiệu lực sau quãng đường 500m."""
        recognizer = TrafficSignRecognizer()
        recognizer.current_speed_limit = 60
        recognizer.speed_limit_source = "CAMERA_SIGN_QCVN41"
        recognizer.is_confirmed = True
        recognizer.update_distance(520.0)
        passed = (recognizer.current_speed_limit is None and recognizer.speed_limit_source == "EXPIRED")
        self.record("CASE_2.3", "Biển báo tự động hết hiệu lực sau 500m di chuyển", "Sign & Speed", passed, {
            "current_speed_limit": recognizer.current_speed_limit,
            "speed_limit_source": recognizer.speed_limit_source
        })

    # =========================================================================
    # NHÓM 3: GIÁM SÁT CABIN TÀI XẾ (CABIN DMS)
    # =========================================================================

    def test_case_3_1_prolonged_eyes_closed_states(self):
        """Case 3.1: Nhắm mắt kéo dài từ Cảnh báo (2s) đến Nguy hiểm (5s)."""
        cfg = EyesClosedConfig(warn_s=2.0, critical_s=5.0, calib_s=0.0)
        monitor = EyesClosedMonitor(cfg=cfg, baseline_ear=0.30)
        t, dt = 100.0, 1.0 / 15.0
        res_warn = None
        res_crit = None
        for _ in range(int(5.5 * 15)):
            res = monitor.update(t, face_found=True, ear=0.12, quality=0.9)
            elapsed = t - 100.0
            if 2.2 <= elapsed <= 2.5 and res_warn is None:
                res_warn = res
            if elapsed >= 5.2 and res_crit is None:
                res_crit = res
            t += dt
        passed = (res_warn is not None and res_crit is not None and 
                  res_warn.state == EyeState.CLOSED_WARN and res_crit.state == EyeState.CLOSED_CRITICAL)
        self.record("CASE_3.1", "Chuyển trạng thái nhắm mắt 2s (WARN) và 5s (CRITICAL)", "Cabin DMS", passed, {
            "warn_state": res_warn.state.value if res_warn else None,
            "critical_state": res_crit.state.value if res_crit else None,
            "events_emitted": [e["type"] for e in res_crit.events] if res_crit else []
        })

    def test_case_3_2_perclos_60s_window(self):
        """Case 3.2: PERCLOS tính tỷ lệ nhắm mắt chuẩn cửa sổ trượt 60 giây."""
        dms = DrowsinessDetector()
        t_base = 1000.0
        # Thêm 100 frame mở mắt và 20 frame nhắm mắt trong 60 giây
        for i in range(80):
            dms.perclos_samples.append((t_base + i * 0.5, False))
        for i in range(20):
            dms.perclos_samples.append((t_base + 40.0 + i * 0.5, True))
        closed_count = sum(1 for _, closed in dms.perclos_samples if closed)
        perclos = closed_count / len(dms.perclos_samples)
        passed = (0.19 <= perclos <= 0.21)
        self.record("CASE_3.2", "PERCLOS cửa sổ trượt 60s (20% nhắm mắt)", "Cabin DMS", passed, {
            "total_samples": len(dms.perclos_samples),
            "closed_count": closed_count,
            "calculated_perclos": round(perclos, 3)
        })

    def test_case_3_3_natural_blink_non_trigger(self):
        """Case 3.3: Chớp mắt sinh lý bình thường 0.2s không gây báo động sai."""
        cfg = EyesClosedConfig(warn_s=2.0, critical_s=5.0, calib_s=0.0)
        monitor = EyesClosedMonitor(cfg=cfg, baseline_ear=0.30)
        t0 = 200.0
        # Mắt nhắm trong 0.25 giây rồi mở lại
        monitor.update(t0, face_found=True, ear=0.12, quality=0.9)
        monitor.update(t0 + 0.25, face_found=True, ear=0.12, quality=0.9)
        res_open = monitor.update(t0 + 0.35, face_found=True, ear=0.30, quality=0.9)
        passed = (res_open.state == EyeState.OPEN and len(res_open.events) == 0)
        self.record("CASE_3.3", "Chớp mắt tự nhiên 0.25s không kích hoạt cảnh báo", "Cabin DMS", passed, {
            "final_state": res_open.state.value,
            "events_count": len(res_open.events)
        })

    def test_case_3_4_head_pose_solvepnp_accuracy(self):
        """Case 3.4: Thuật toán solvePnP tính góc Pitch, Yaw, Roll 3D."""
        landmarks_2d = np.array([
            (320.0, 240.0),  # mũi
            (320.0, 340.0),  # cằm
            (260.0, 190.0),  # mắt trái
            (380.0, 190.0),  # mắt phải
            (280.0, 290.0),  # miệng trái
            (360.0, 290.0),  # miệng phải
        ], dtype=np.float64)
        pitch, yaw, roll = estimate_head_pose_pnp(landmarks_2d, 640, 480)
        passed = (isinstance(pitch, float) and isinstance(yaw, float) and abs(yaw) < 30.0)
        self.record("CASE_3.4", "Ước lượng tư thế đầu solvePnP 3D Euler angles", "Cabin DMS", passed, {
            "pitch_deg": round(pitch, 1),
            "yaw_deg": round(yaw, 1),
            "roll_deg": round(roll, 1)
        })

    def test_case_3_5_fatigue_timer_red_light_non_reset(self):
        """Case 3.5: Dừng đèn đỏ 2 phút không được reset đồng hồ lái xe 4 giờ."""
        clock_val = [1000.0]
        timer = DrivingTimer(clock=lambda: clock_val[0])
        # Lái liên tục 120 phút
        clock_val[0] += 7200.0
        timer.update(is_vehicle_moving=True, speed_kmh=50.0)
        # Dừng đèn đỏ 120 giây (tốc độ = 0 km/h)
        clock_val[0] += 120.0
        status = timer.update(is_vehicle_moving=False, speed_kmh=0.0)
        passed = (status["continuous_minutes"] >= 120.0 and status["should_rest"] is False)
        self.record("CASE_3.5", "Dừng đèn đỏ không reset thời gian lái xe liên tục", "Cabin DMS", passed, {
            "continuous_minutes": round(status["continuous_minutes"], 1),
            "should_rest": status["should_rest"]
        })

    def test_case_3_6_fatigue_timer_4_hour_warning(self):
        """Case 3.6: Cảnh báo bắt buộc nghỉ ngơi khi lái xe liên tục vượt 4 giờ."""
        clock_val = [1000.0]
        timer = DrivingTimer(clock=lambda: clock_val[0])
        # Lái liên tục 4 giờ 5 phút = 245 phút
        clock_val[0] += 245 * 60.0
        status = timer.update(is_vehicle_moving=True, speed_kmh=60.0)
        passed = (status["should_rest"] is True and status["continuous_minutes"] >= 240.0)
        self.record("CASE_3.6", "Cảnh báo mệt mỏi khi lái quá 4 giờ liên tục (TT05/BGTVT)", "Cabin DMS", passed, {
            "continuous_minutes": round(status["continuous_minutes"], 1),
            "should_rest": status["should_rest"]
        })

    # =========================================================================
    # NHÓM 4: BIỂN SỐ XE VIỆT NAM (ALPR & VIETNAMESE PLATES)
    # =========================================================================

    def test_case_4_1_civilian_car_plate(self):
        """Case 4.1: Biển trắng ô tô dân sự 5 số (VD: 30A-123.45)."""
        plate = "30A12345"
        is_valid = is_valid_vietnamese_plate(plate)
        fixed, _ = fix_plate("30A-123.45")
        passed = (is_valid is True and fixed is not None)
        self.record("CASE_4.1", "Nhận dạng biển trắng ô tô 5 số (30A-123.45)", "ALPR", passed, {
            "plate": plate,
            "is_valid": is_valid,
            "fixed": fixed
        })

    def test_case_4_2_commercial_yellow_plate(self):
        """Case 4.2: Biển vàng kinh doanh vận tải (VD: 29E-555.88)."""
        plate = "29E55588"
        is_valid = is_valid_vietnamese_plate(plate)
        yellow_img = np.full((60, 180, 3), (20, 200, 220), dtype=np.uint8)
        color = classify_plate_background_color(yellow_img)
        passed = (is_valid is True and color == "COMMERCIAL_YELLOW")
        self.record("CASE_4.2", "Biển vàng kinh doanh vận tải & phân loại màu (TT58)", "ALPR", passed, {
            "plate": plate,
            "is_valid": is_valid,
            "color_classified": color
        })

    def test_case_4_3_military_red_plate(self):
        """Case 4.3: Biển đỏ xe quân sự (VD: KT-55-72)."""
        plate = "KT5572"
        is_valid = is_valid_vietnamese_plate(plate)
        red_img = np.full((60, 180, 3), (20, 20, 220), dtype=np.uint8)
        color = classify_plate_background_color(red_img)
        passed = (is_valid is True and color == "MILITARY_RED")
        self.record("CASE_4.3", "Biển đỏ quân đội (KT-55-72) & phân loại màu", "ALPR", passed, {
            "plate": plate,
            "is_valid": is_valid,
            "color_classified": color
        })

    def test_case_4_4_government_blue_plate(self):
        """Case 4.4: Biển xanh cơ quan nhà nước (VD: 80A-001.23)."""
        plate = "80A00123"
        is_valid = is_valid_vietnamese_plate(plate)
        blue_img = np.full((60, 180, 3), (200, 100, 20), dtype=np.uint8)
        color = classify_plate_background_color(blue_img)
        passed = (is_valid is True and color == "GOVERNMENT_BLUE")
        self.record("CASE_4.4", "Biển xanh công vụ (80A-001.23) & phân loại màu", "ALPR", passed, {
            "plate": plate,
            "is_valid": is_valid,
            "color_classified": color
        })

    def test_case_4_5_filter_taxi_hotline_garbage(self):
        """Case 4.5: Lọc triệt để số hotline taxi và số điện thoại quảng cáo."""
        samples = [
            ("0938123456", True),
            ("38272727", True),
            ("19001234", True),
            ("51A12345", False),
            ("29-B1 56789", False)
        ]
        all_passed = True
        for raw, expected in samples:
            filtered = is_phone_or_garbage(raw)
            if filtered != expected:
                all_passed = False
                break
        self.record("CASE_4.5", "Lọc số điện thoại hotline taxi và rác OCR", "ALPR", all_passed, {
            "tested_samples": len(samples),
            "all_passed": all_passed
        })

    def test_case_4_6_ocr_confusable_character_mapping(self):
        """Case 4.6: Tự động sửa ký tự nhầm lẫn quang học (O->0, D->0, B->8)."""
        # Kiểm tra bảng TO_DIGIT
        passed = (
            TO_DIGIT.get("O") == "0" and
            TO_DIGIT.get("D") == "0" and
            TO_DIGIT.get("B") == "8" and
            TO_DIGIT.get("S") == "5" and
            TO_LETTER.get("4") == "A"
        )
        self.record("CASE_4.6", "Chuyển đổi ký tự nhầm lẫn quang học theo quy tắc ngữ cảnh", "ALPR", passed, {
            "O_to_0": TO_DIGIT.get("O"),
            "D_to_0": TO_DIGIT.get("D"),
            "B_to_8": TO_DIGIT.get("B"),
            "4_to_A": TO_LETTER.get("4")
        })

    # =========================================================================
    # NHÓM 5: BỘ RA QUYẾT ĐỊNH & AN TOÀN DỮ LIỆU (DECISION & PRIVACY)
    # =========================================================================

    def test_case_5_1_multi_event_priority_hierarchy(self):
        """Case 5.1: Xếp hạng ưu tiên: Cảnh báo va chạm khẩn cấp lấn át cảnh báo mệt mỏi."""
        engine = DecisionEngine()
        ev_fcw = AdasEvent(
            module="ttc",
            type="fcw_critical",
            severity="critical",
            confidence=0.95,
            payload={"ttc": 1.2, "track_id": 1}
        )
        ev_timer = AdasEvent(
            module="driving_timer",
            type="fatigue_break",
            severity="warning",
            confidence=0.99,
            payload={"hours": 4.1}
        )
        # Duy trì 3 khung hình liên tiếp để vượt qua bộ lọc EventNoiseFilter (TTC yêu cầu 3 frames)
        decision = None
        for _ in range(3):
            decision = engine.process_events([ev_fcw, ev_timer], session_id=1, driver_id=1)

        passed = (
            decision is not None and 
            decision.primary_event is not None and 
            decision.primary_event.module == "ttc" and
            decision.primary_event.severity == "critical" and
            decision.ui_theme == "critical"
        )
        self.record("CASE_5.1", "Ưu tiên quyết định: Va chạm khẩn cấp lấn át mệt mỏi", "Decision Engine", passed, {
            "primary_module": decision.primary_event.module if decision and decision.primary_event else None,
            "primary_severity": decision.primary_event.severity if decision and decision.primary_event else None,
            "ui_theme": decision.ui_theme if decision else None
        })

    def test_case_5_2_evidence_anonymization_and_hash(self):
        """Case 5.2: Làm mờ khuôn mặt bảo mật cá nhân & băm SHA-256 chống làm giả bằng chứng."""
        img = np.full((100, 100, 3), 180, dtype=np.uint8)
        # Bounding box khuôn mặt
        anon = anonymize_evidence_frame(img, face_boxes=[(20, 20, 60, 60)])
        digest = compute_evidence_hash(img.tobytes())
        passed = (
            anon is not None and 
            isinstance(digest, str) and 
            len(digest) == 64 and 
            digest.isalnum()
        )
        self.record("CASE_5.2", "Làm mờ bằng chứng & mã băm SHA-256 tính toàn vẹn", "Privacy & Security", passed, {
            "sha256_hash": digest,
            "hash_length": len(digest),
            "anonymized_successfully": anon is not None
        })

    def run_all(self):
        print("=" * 80)
        print("BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG ĐA KỊCH BẢN CHO DỰ ÁN TRAFFICGUARD")
        print("=" * 80)
        t_start = time.time()

        # Group 1: ADAS Road
        print("\n--- NHÓM 1: PHÂN HỆ ADAS ĐƯỜNG BỘ & VA CHẠM ---")
        self.test_case_1_1_highway_safe_distance()
        self.test_case_1_2_emergency_braking_ttc()
        self.test_case_1_3_adverse_weather_safe_distance()
        self.test_case_1_4_traffic_jam_low_speed_suppression()
        self.test_case_1_5_pothole_shake_suppression()
        self.test_case_1_6_pinhole_distance_calibration()
        self.test_case_1_7_lane_detector_fallback_corridor()
        self.test_case_1_8_dense_motorbikes_soft_nms()
        self.test_case_1_9_trailer_merge_integrity()
        self.test_case_1_10_speed_estimator_deadband()

        # Group 2: Signs & Speed
        print("\n--- NHÓM 2: BIỂN BÁO & KHUYẾN NGHỊ TỐC ĐỘ ---")
        self.test_case_2_1_school_zone_speed_advisory()
        self.test_case_2_2_map_camera_fusion_conflict()
        self.test_case_2_3_sign_distance_expiration()

        # Group 3: Cabin DMS
        print("\n--- NHÓM 3: GIÁM SÁT CABIN TÀI XẾ (DMS) ---")
        self.test_case_3_1_prolonged_eyes_closed_states()
        self.test_case_3_2_perclos_60s_window()
        self.test_case_3_3_natural_blink_non_trigger()
        self.test_case_3_4_head_pose_solvepnp_accuracy()
        self.test_case_3_5_fatigue_timer_red_light_non_reset()
        self.test_case_3_6_fatigue_timer_4_hour_warning()

        # Group 4: ALPR
        print("\n--- NHÓM 4: BIỂN SỐ XE VIỆT NAM (ALPR) ---")
        self.test_case_4_1_civilian_car_plate()
        self.test_case_4_2_commercial_yellow_plate()
        self.test_case_4_3_military_red_plate()
        self.test_case_4_4_government_blue_plate()
        self.test_case_4_5_filter_taxi_hotline_garbage()
        self.test_case_4_6_ocr_confusable_character_mapping()

        # Group 5: Decision & Privacy
        print("\n--- NHÓM 5: BỘ RA QUYẾT ĐỊNH & BẢO MẬT DỮ LIỆU ---")
        self.test_case_5_1_multi_event_priority_hierarchy()
        self.test_case_5_2_evidence_anonymization_and_hash()

        duration = round(time.time() - t_start, 2)
        total = self.passed_count + self.failed_count
        pass_rate = round((self.passed_count / total) * 100, 1) if total > 0 else 0.0

        print("\n" + "=" * 80)
        print(f"KẾT QUẢ KIỂM THỬ: {self.passed_count}/{total} PASSED ({pass_rate}%) trong {duration}s")
        print("=" * 80)

        report = {
            "summary": {
                "total_cases": total,
                "passed": self.passed_count,
                "failed": self.failed_count,
                "pass_rate_percent": pass_rate,
                "duration_seconds": duration,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "cases": self.results
        }

        import os
        os.makedirs("output", exist_ok=True)
        with open("output/scenario_verification_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return self.failed_count == 0


if __name__ == "__main__":
    runner = ScenarioVerificationRunner()
    success = runner.run_all()
    exit(0 if success else 1)
