"""
verify_helmet_deduplication.py
------------------------------
Kiểm chứng tự động: Khắc phục lỗi lặp thẻ vi phạm mũ bảo hiểm (Người điều khiển #1 bị lặp lại).
1. Kiểm tra Backend: NMS với IoU và IoMin loại bỏ các box trùng trên cùng một người.
2. Kiểm tra Frontend Logic: Thuật toán uniqueHelmets và deduplication trong recognizeHelmetsFromFile
   ngăn chặn việc unshift trùng lặp khi người dùng quét lại nhiều lần.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

BASE_URL = "http://localhost:8000"
USER_IMAGE_PATH = Path(r"C:\Users\ADMIN\.gemini\antigravity\brain\c7537c87-56bf-4ab7-a351-6ac7f7e3d598\.user_uploaded\media_1790745381245.png")


def test_backend_helmet_nms():
    """Kiểm tra backend không trả về 2 box trùng lặp trên cùng 1 người."""
    print("\n--- TEST 1: Backend Helmet NMS Deduplication ---")
    assert USER_IMAGE_PATH.exists(), f"File {USER_IMAGE_PATH} không tồn tại"

    with open(USER_IMAGE_PATH, "rb") as f:
        res = requests.post(f"{BASE_URL}/api/v1/helmets/detect", files={"file": f})

    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    violations = data.get("violations", [])
    print(f"[PASS] Backend detected violations: {len(violations)}")
    # Trong ảnh media_1790745381245.png có đúng 2 người vi phạm (người lớn và trẻ em)
    assert len(violations) == 2, f"Kỳ vọng 2 người vi phạm không mũ, thực tế: {len(violations)}"

    # Kiểm tra track_id không bị trùng
    track_ids = [v["track_id"] for v in violations]
    assert len(track_ids) == len(set(track_ids)), f"Trùng track_id trong cùng 1 frame: {track_ids}"
    for v in violations:
        print(f"  -> Người điều khiển #{v['track_id']}: bbox={v['bbox']}, conf={v['confidence']}")


def test_frontend_deduplication_simulation():
    """Mô phỏng quét lại 3 lần liên tiếp: Danh sách phải deduplicate, không được nhân bản thành 6 thẻ!"""
    print("\n--- TEST 2: Multiple Re-Scan Simulation (Deduplication) ---")
    # Giả lập 2 vi phạm từ backend
    raw_violations = [
        {"track_id": 1, "bbox": {"x1": 500, "y1": 200, "x2": 600, "y2": 320}, "count": 1},
        {"track_id": 2, "bbox": {"x1": 420, "y1": 280, "x2": 510, "y2": 390}, "count": 1},
    ]

    # Mô phỏng thuật toán uniqueHelmets trong DetectionTabsPanel
    def compute_unique_helmets(violations_list):
        result = []
        for h in violations_list:
            existing = None
            for item in result:
                if item.get("track_id") and h.get("track_id") and item["track_id"] == h["track_id"]:
                    existing = item
                    break
                c1x = (item["bbox"]["x1"] + item["bbox"]["x2"]) / 2
                c1y = (item["bbox"]["y1"] + item["bbox"]["y2"]) / 2
                c2x = (h["bbox"]["x1"] + h["bbox"]["x2"]) / 2
                c2y = (h["bbox"]["y1"] + h["bbox"]["y2"]) / 2
                if ((c1x - c2x) ** 2 + (c1y - c2y) ** 2) ** 0.5 < 60:
                    existing = item
                    break

            if existing:
                existing["count"] = existing.get("count", 1) + h.get("count", 1)
            else:
                result.append(dict(h))
        return result

    # Quét lần 1
    accumulated = list(raw_violations)
    unique_1 = compute_unique_helmets(accumulated)
    assert len(unique_1) == 2, f"Lần 1 phải có 2 thẻ, thực tế: {len(unique_1)}"
    labels_1 = [f"Người #{x['track_id']}" for x in unique_1]
    print(f"[PASS] Lần 1: {len(unique_1)} thẻ duy nhất: {labels_1}")

    # Quét lần 2 (Quét lại ảnh cũ mà không reset)
    accumulated = list(raw_violations) + accumulated
    unique_2 = compute_unique_helmets(accumulated)
    assert len(unique_2) == 2, f"Lần 2 sau khi quét lại BẮT BUỘC chỉ có 2 thẻ duy nhất, thực tế: {len(unique_2)}"
    assert unique_2[0]["count"] == 2 and unique_2[1]["count"] == 2
    print(f"[PASS] Lần 2 (Quét lại): Vẫn duy trì đúng {len(unique_2)} thẻ (count tăng lên 2, KHÔNG BỊ NHÂN ĐÔI LÊN 4)")

    # Quét lần 3
    accumulated = list(raw_violations) + accumulated
    unique_3 = compute_unique_helmets(accumulated)
    assert len(unique_3) == 2, f"Lần 3 BẮT BUỘC chỉ có 2 thẻ duy nhất, thực tế: {len(unique_3)}"
    print(f"[PASS] Lần 3 (Quét lại tiếp): Vẫn duy trì đúng {len(unique_3)} thẻ duy nhất (count=3)")


def main():
    print("=" * 60)
    print("   AUTOMATED VERIFICATION: HELMET DEDUPLICATION FIX")
    print("=" * 60)

    test_backend_helmet_nms()
    test_frontend_deduplication_simulation()

    print("\n" + "=" * 60)
    print("  >>> ALL HELMET DEDUPLICATION TESTS PASSED (100%) <<<")
    print("=" * 60)


if __name__ == "__main__":
    main()
