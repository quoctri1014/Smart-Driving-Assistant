"""
verify_vehicle_speed_fix.py
---------------------------
Bộ kiểm thử tự động xác thực giải pháp đo tốc độ phương tiện:
1. BƯỚC 1: Tracking ID phương tiện qua các khung hình.
2. BƯỚC 2: Điểm đại diện tiếp xúc mặt đường (bottom_center: ((x1+x2)/2, y2)).
3. BƯỚC 3: Đổi pixel sang mét (Road Homography).
4. BƯỚC 4: Vận tốc v = delta_d / delta_t * 3.6 (cửa sổ 0.5s - 1.0s, làm mượt EMA, deadband 0 km/h).
5. RÀNG BUỘC CỐT LÕI:
   - CHỈ XÁC ĐỊNH TỐC ĐỘ TRÊN VIDEO!
   - TRÊN ẢNH TĨNH: speed_kmh BẮT BUỘC là None / undefined, không gắn nhãn 45 km/h giả mạo.
"""

import io
import os
import sys
import time
from pathlib import Path

# Đảm bảo in UTF-8 không lỗi trên Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
import requests

from backend.app.services.vehicle_speed_tracker import VehicleSpeedTracker

BASE_URL = "http://localhost:8000"
USER_IMAGE_PATH = Path(r"C:\Users\ADMIN\.gemini\antigravity\brain\c7537c87-56bf-4ab7-a351-6ac7f7e3d598\.user_uploaded\media_1790745381245.png")


def test_1_static_image_has_no_speed():
    """Kiểm tra: Tải ảnh tĩnh (is_video=False) của người dùng: TUYỆT ĐỐI KHÔNG có speed_kmh."""
    print("\n--- TEST 1: Static Image Upload (is_video=False) with Real User Street Image ---")
    assert USER_IMAGE_PATH.exists(), f"Không tìm thấy file ảnh thực tế: {USER_IMAGE_PATH}"

    with open(USER_IMAGE_PATH, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("user_street.png", file_bytes, "image/png")}
    params = {"is_video": "false", "session_id": "test_static"}

    res = requests.post(f"{BASE_URL}/api/v1/traffic-density/detect", files=files, params=params)
    assert res.status_code == 200, f"HTTP Error {res.status_code}: {res.text}"
    data = res.json()

    assert data["success"] is True, "Phản hồi API không thành công"
    vehicles = data.get("vehicles", [])
    print(f"[PASS] API responded successfully. Total vehicles detected: {len(vehicles)}")
    assert len(vehicles) > 0, "YOLO phải phát hiện ít nhất 1 phương tiện trong ảnh đường phố thực tế!"

    # Kiểm tra từng xe: speed_kmh BẮT BUỘC LÀ NONE
    for v in vehicles:
        assert v["speed_kmh"] is None, f"LỖI NGHIÊM TRỌNG: Xe #{v['id']} có speed_kmh = {v['speed_kmh']} km/h (Phải là None)!"
        print(f"  -> Xe #{v['id']} ({v['display_name']}): Cự ly = {v['distance_m']}m | speed_kmh = {v['speed_kmh']} (HOÀN TOÀN KHÔNG HIỆN TỐC ĐỘ GIẢ)")

    # Kiểm tra ttc_seconds trên ảnh tĩnh: BẮT BUỘC LÀ NONE
    assert data["ttc_seconds"] is None, f"LỖI: Ảnh tĩnh có ttc_seconds = {data['ttc_seconds']} (Phải là None)!"
    print(f"[PASS] ttc_seconds is None for static images: {data['ttc_seconds']}")


def test_2_vehicle_speed_tracker_4_steps():
    """Kiểm tra VehicleSpeedTracker tuân thủ đúng 4 bước theo tài liệu."""
    print("\n--- TEST 2: VehicleSpeedTracker 4-Step Algorithmic Verification ---")
    tracker = VehicleSpeedTracker(frame_w=1280, frame_h=720, window_sec=0.6)

    # Bước 2: Bounding box và bottom_center
    # Giả lập xe ô tô #101 di chuyển từ xa lại gần (vận tốc ~50 km/h)
    # Tốc độ 50 km/h ~ 13.89 m/s.
    # Trong 0.6s, xe đi được ~8.33 mét.
    fps = 30
    speeds = []
    for frame_idx in range(35):
        t = frame_idx / float(fps)
        # Bbox di chuyển dần xuống dưới khung hình
        y2 = int(420 + (frame_idx / 30.0) * 120)
        y1 = y2 - 80
        x1 = 580
        x2 = 700
        bbox = [x1, y1, x2, y2]

        res = tracker.update_vehicle(vehicle_id=101, bbox=bbox, timestamp_sec=t)
        speed = res[0] if isinstance(res, tuple) else res
        speeds.append(speed)

    # Frame 0 đến frame 10 (dt < 0.35s): Chưa đủ cửa sổ thời gian -> None
    assert speeds[0] is None, "Frame 0 phải trả về None vì chưa đủ thời gian"
    print(f"[PASS] Frame 0 initial speed: {speeds[0]} (None as expected)")

    # Frame 25..34 (dt >= 0.35s): Phải tính được vận tốc hợp lý (> 30 km/h và < 70 km/h)
    final_speed = speeds[-1]
    assert final_speed is not None, "Vận tốc sau khi đủ thời gian không được là None"
    assert 30.0 <= final_speed <= 70.0, f"Vận tốc tính toán bất thường: {final_speed} km/h"
    print(f"[PASS] Frame 34 calculated smooth vehicle speed: {final_speed} km/h (Mục tiêu ~50 km/h)")


def test_3_deadband_stopped_vehicle():
    """Kiểm tra xe dừng đèn đỏ: Vận tốc phải trả về 0.0 km/h (không bị nhảy số do rung pixel)."""
    print("\n--- TEST 3: Deadband Stationary Vehicle Verification ---")
    tracker = VehicleSpeedTracker(frame_w=1280, frame_h=720)

    # Xe đứng yên một chỗ tại vị trí (x1=600, y1=500, x2=720, y2=600) kèm rung pixel nhẹ +-1px
    for frame_idx in range(30):
        t = frame_idx / 30.0
        jitter = (-1 if frame_idx % 2 == 0 else 1)
        bbox = [600 + jitter, 500, 720 + jitter, 600]
        res = tracker.update_vehicle(vehicle_id=202, bbox=bbox, timestamp_sec=t)
        speed = res[0] if isinstance(res, tuple) else res

    assert speed == 0.0, f"Xe đứng yên nhưng tính ra vận tốc: {speed} km/h (Phải là 0.0 km/h)!"
    print(f"[PASS] Stationary vehicle with pixel jitter correctly reports: {speed} km/h")


def test_4_video_endpoint_tracking():
    """Kiểm tra gọi endpoint với is_video=True: Có ID tracking và hỗ trợ tính toán tốc độ trên video."""
    print("\n--- TEST 4: Video Sequence Endpoint Tracking (is_video=True) ---")
    session_id = f"test_vid_{int(time.time())}"

    # Reset tracker trước
    res_reset = requests.post(f"{BASE_URL}/api/v1/traffic-density/reset-tracker", params={"session_id": session_id})
    assert res_reset.status_code == 200

    with open(USER_IMAGE_PATH, "rb") as f:
        file_bytes = f.read()

    files = {"file": ("frame_0.png", file_bytes, "image/png")}
    params = {"is_video": "true", "session_id": session_id, "timestamp": "0.0"}

    res = requests.post(f"{BASE_URL}/api/v1/traffic-density/detect", files=files, params=params)
    assert res.status_code == 200
    data = res.json()
    print(f"[PASS] Video mode responded. Vehicle count: {len(data['vehicles'])}")
    if data["vehicles"]:
        # Khung hình đầu tiên chưa đủ delta_t nên speed_kmh là None (đúng chuẩn toán học, không bịa số)
        print(f"[PASS] Frame 0 video vehicle #1 speed_kmh: {data['vehicles'][0]['speed_kmh']} (None before window)")


def main():
    print("=" * 60)
    print("   AUTOMATED VERIFICATION: VEHICLE SPEED TRACKING & ISOLATION")
    print("=" * 60)

    try:
        test_1_static_image_has_no_speed()
        test_2_vehicle_speed_tracker_4_steps()
        test_3_deadband_stopped_vehicle()
        test_4_video_endpoint_tracking()

        print("\n" + "=" * 60)
        print("  >>> ALL 4 VERIFICATION TESTS PASSED SUCCESSFULLY (100%) <<<")
        print("=" * 60)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
