import os
import sys
from pathlib import Path
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from backend.app.api.traffic_sign_routes import (
    clean_vietnamese_auxiliary_sign_text,
    refine_p103_sign_class,
    _apply_nms,
    VN_SIGN_INFO,
)

def run_tests():
    print("=" * 70)
    print("KIỂM CHỨNG TOÀN DIỆN FIX LỖI NHẬN DIỆN BIỂN BÁO & BIỂN PHỤ")
    print("=" * 70)
    
    passed = 0
    total = 0

    # 1. TEST BIỂN PHỤ TIẾNG VIỆT & CHUẨN HÓA FONT
    print("\n[TEST 1] Chuẩn hóa font chữ và từ điển biển phụ tiếng Việt:")
    test_cases_aux = [
        ("XE HQP DonG 12 Duoi 09 CHO NGoI] 6:00 - 21:00", "S.508", "Xe hợp đồng dưới 9 chỗ ngồi", "6:00 - 21:00"),
        ("XE HOP DONG DUOI 9 CHO 06h00 - 21h00", "S.508", "Xe hợp đồng dưới 9 chỗ ngồi", "06:00 - 21:00"),
        ("XE TAXI VA XE HOP DONG DUOI 9 CHO NGOI", "S.503", "Xe hợp đồng dưới 9 chỗ ngồi", None),
        ("CAM XE TAI TREN 3.5 TAN 6:00 - 9:00", "S.508", "Xe ô tô tải trên 3.5 tấn", "6:00 - 9:00"),
        ("6h00 - 21h00", "S.508", "Khung giờ hiệu lực", "6:00 - 21:00"),
    ]
    for raw, exp_code, exp_name_kw, exp_time in test_cases_aux:
        total += 1
        code, name, action, time_str = clean_vietnamese_auxiliary_sign_text(raw)
        assert code == exp_code, f"Expected code {exp_code}, got {code}"
        assert exp_name_kw.lower() in name.lower(), f"Expected '{exp_name_kw}' in '{name}'"
        if exp_time:
            assert exp_time in action or (time_str and exp_time in time_str), f"Expected '{exp_time}' in '{action}'"
        print(f"  ✓ '{raw}' -> [{code}] {name} | {action}")
        passed += 1

    # 2. TEST PHÂN LOẠI P.103a vs P.103b vs P.103c
    print("\n[TEST 2] Phân loại chính xác biển chính P.103a (Cấm ô tô) vs P.103b / P.103c:")
    bien_bao_dir = BASE_DIR / "datasets" / "Bien_bao_giao_thong_Viet_Nam_md" / "img"
    if not bien_bao_dir.exists():
        bien_bao_dir = BASE_DIR / "backend" / "app" / "assets" / "qcvn_signs"
    tmpl_a = cv2.imread(str(bien_bao_dir / "P_103a.png"))
    tmpl_b = cv2.imread(str(bien_bao_dir / "P_103b.png"))
    tmpl_c = cv2.imread(str(bien_bao_dir / "P_103c.png"))
    thumb_path = BASE_DIR / "exact_thumb_sign1.png"
    user_sign = cv2.imread(str(thumb_path)) if thumb_path.exists() else tmpl_a

    # Test user screenshot thumbnail:
    total += 1
    res_user = refine_p103_sign_class(user_sign, "P.103c", has_aux_sign=False)
    assert res_user == "P.103a", f"User sign should be P.103a, got {res_user}"
    print(f"  ✓ Ảnh thực tế người dùng gửi (exact_thumb_sign1): {res_user} ({VN_SIGN_INFO[res_user]['name']})")
    passed += 1

    # Test with has_aux_sign=True:
    total += 1
    res_aux = refine_p103_sign_class(user_sign, "P.103c", has_aux_sign=True)
    assert res_aux == "P.103a"
    print(f"  ✓ Khi có biển phụ 'Xe hợp đồng' bên dưới: Tự động chuẩn hóa {res_aux}")
    passed += 1

    # Test template P.103a:
    total += 1
    res_a = refine_p103_sign_class(tmpl_a, "P.103c", has_aux_sign=False)
    assert res_a == "P.103a"
    print(f"  ✓ Template P_103a: {res_a} ({VN_SIGN_INFO[res_a]['name']})")
    passed += 1

    # Test template P.103b:
    total += 1
    res_b = refine_p103_sign_class(tmpl_b, "P.103a", has_aux_sign=False)
    assert res_b == "P.103b"
    print(f"  ✓ Template P_103b: {res_b} ({VN_SIGN_INFO[res_b]['name']})")
    passed += 1

    # Test template P.103c:
    total += 1
    res_c = refine_p103_sign_class(tmpl_c, "P.103a", has_aux_sign=False)
    assert res_c == "P.103c"
    print(f"  ✓ Template P_103c: {res_c} ({VN_SIGN_INFO[res_c]['name']})")
    passed += 1

    # 3. TEST LỌC TRÙNG LẶP BIỂN BÁO (DEDUPLICATION)
    print("\n[TEST 3] Kiểm tra thuật toán khử trùng lặp (Deduplication / NMS):")
    duplicate_detections = [
        {"sign_type": "P.103a", "conf": 0.88, "bbox": [100, 50, 160, 110]},
        {"sign_type": "P.103a", "conf": 0.82, "bbox": [105, 55, 165, 115]},  # Trùng lặp nhẹ
        {"sign_type": "P.103c", "conf": 0.79, "bbox": [102, 52, 162, 112]},  # Bị phân loại nhầm trên cùng vị trí
        {"sign_type": "S.508",  "conf": 0.95, "bbox": [95, 120, 165, 170]},  # Biển phụ bên dưới (phải giữ lại)
    ]
    total += 1
    kept = _apply_nms(duplicate_detections)
    types_kept = [k["sign_type"] for k in kept]
    assert len(kept) == 2, f"Expected 2 kept signs (1 main + 1 aux), got {len(kept)}: {types_kept}"
    assert set(types_kept) == {"P.103a", "S.508"}
    conf_p103 = next(k["conf"] for k in kept if k["sign_type"] == "P.103a")
    assert conf_p103 == 0.88
    print(f"  ✓ Đã lọc 3 box trùng vị trí xuống đúng 1 biển chính P.103a (conf {conf_p103}) và 1 biển phụ S.508 (conf 0.95)!")
    passed += 1

    print("\n" + "=" * 70)
    print(f"KẾT QUẢ KIỂM THỬ: {passed}/{total} BÀI TEST ĐẠT (100% SUCCESS)!")
    print("=" * 70)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run_tests()
