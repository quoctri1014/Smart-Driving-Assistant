import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "ai_engine" / "plate"))

import cv2
import easyocr
try:
    from scripts.plate_recognizer import fix_plate, read_text, fmt, is_valid_vietnamese_plate
except ImportError:
    from ai_engine.plate.plate_recognizer import fix_plate, read_text, fmt, is_valid_vietnamese_plate
from ai_engine.plate.plate_reader import classify_plate_background_color, format_plate_display
from backend.app.api.license_plate_routes import _read_crop_with_recognizer, fmt_vietnamese_plate

reader = easyocr.Reader(['en'], gpu=False)
img_path = Path(r'C:/Users/ADMIN/.gemini/antigravity/brain/c7537c87-56bf-4ab7-a351-6ac7f7e3d598/.user_uploaded/media_1790755588854.jpg')
img = cv2.imread(str(img_path))
assert img is not None, "Could not load test image"

tests = [
    ("29-AB 0014", [0, 440, 241, 619], "29-AB 0014", "CIVILIAN_WHITE"),
    ("30-Y9 6850", [244, 441, 465, 619], "30-Y9 6850", "CIVILIAN_WHITE"),
    ("15-C1 010.82", [451, 447, 676, 618], "15-C1 010.82", "CIVILIAN_WHITE"),
    ("80-QT 546-42", [691, 363, 1024, 456], "80-QT 546-42", "CIVILIAN_WHITE"),
    ("29-NN 691-33", [2, 112, 236, 284], "29-NN 691-33", "CIVILIAN_WHITE"),
    ("51A-010.88", [691, 34, 1020, 121], "51A-010.88", "CIVILIAN_WHITE"),
    ("18B-7929", [694, 460, 1016, 541], "18B-7929", "GOVERNMENT_BLUE"),
    ("KT-55-72", [694, 540, 1016, 619], "KT-55-72", "MILITARY_RED"),
]

print("=== RUNNING LICENSE PLATE VERIFICATION ===")
passed = 0
for name, box, expected_text, expected_color in tests:
    x1, y1, x2, y2 = box
    crop = img[y1:y2, x1:x2]
    
    # 1. OCR Recognizer
    det_plate, raw, conf = _read_crop_with_recognizer(reader, crop)
    formatted = fmt_vietnamese_plate(det_plate) if det_plate else ""
    
    # 2. Color classification
    color = classify_plate_background_color(crop, formatted)
    
    print(f"\nTest '{name}':")
    print(f"  Result Plate: '{formatted}' (raw: '{raw}', conf: {conf:.2f})")
    print(f"  Result Color: '{color}'")
    print(f"  Expected:     Plate='{expected_text}', Color='{expected_color}'")
    
    ok_plate = (formatted == expected_text)
    ok_color = (color == expected_color)
    if ok_plate and ok_color:
        print("  -> PASSED [OK]")
        passed += 1
    else:
        print(f"  -> FAIL (plate_ok={ok_plate}, color_ok={ok_color})")

print(f"\nTOTAL PASSED: {passed}/{len(tests)}")
if passed == len(tests):
    print("ALL TESTS PASSED 100%!")
else:
    print("SOME TESTS FAILED, INSPECTING...")
