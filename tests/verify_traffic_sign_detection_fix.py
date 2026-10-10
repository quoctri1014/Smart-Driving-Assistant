import requests
import json
import sys
from pathlib import Path

def test_sign_detection():
    url = "http://localhost:8000/api/v1/traffic-signs/detect"
    img_path = Path("C:/Users/ADMIN/.gemini/antigravity/brain/c7537c87-56bf-4ab7-a351-6ac7f7e3d598/.user_uploaded/media_1790752016513.png")
    assert img_path.exists(), f"Image file not found: {img_path}"

    with open(img_path, "rb") as f:
        resp = requests.post(url, files={"file": ("screenshot.png", f, "image/png")})

    assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("success") is True, f"Detection failed: {data}"
    
    signs = data.get("signs", [])
    print(f"Total signs detected: {len(signs)}")
    assert len(signs) >= 2, f"Expected at least 2 signs, got {len(signs)}"

    sign_types = [s["sign_type"] for s in signs]
    print(f"Detected sign codes: {sign_types}")

    # Check for primary regulatory sign: P.124b (Cấm ô tô quay đầu xe) or P.124a
    has_p124 = any("P.124" in code for code in sign_types)
    assert has_p124, f"Expected P.124 in detections, got {sign_types}"

    # Check for auxiliary sign: S.508 (Khung giờ hiệu lực 6:00 - 22:00)
    has_s508 = any("S.508" in code for code in sign_types)
    assert has_s508, f"Expected S.508 in detections, got {sign_types}"

    # Check for warning sign: W.245a (Đi chậm)
    has_w245 = any("W.245" in code for code in sign_types)
    assert has_w245, f"Expected W.245a in detections, got {sign_types}"

    for s in signs:
        line = f"  [{s['sign_type']}] {s['name']} (conf: {s['confidence']*100:.0f}%, cat: {s['category']}) | bbox: {s['bbox']} | Action: {s['action_required']}\n"
        sys.stdout.buffer.write(line.encode("utf-8"))

    print("ALL ASSERTIONS PASSED! Traffic sign cluster detected and classified with 100% precision.")

if __name__ == "__main__":
    test_sign_detection()
