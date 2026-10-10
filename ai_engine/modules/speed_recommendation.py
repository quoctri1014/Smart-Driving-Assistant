"""
speed_recommendation.py
-----------------------
Hệ thống khuyến nghị tốc độ thông minh (Explainable Rule Engine):
1. Hợp nhất đa nguồn:
   - Giới hạn tốc độ pháp lý (Biển báo QCVN 41:2019 / Bản đồ OpenStreetMap).
   - Loại phương tiện (Ô tô con, xe buýt, xe tải nặng theo TT 31/2019).
   - Mật độ giao thông (Zone counting).
   - Thời tiết / đường trơn (giảm 15% khi mưa lớn).
   - Khoảng cách an toàn với xe chạy liền trước (SafeDistanceCalculator).
2. Tính giải thích được (Explainable AI): Mỗi đề xuất nêu rõ lý do và căn cứ pháp lý.
3. Nguyên tắc an toàn bất biến: TUYỆT ĐỐI KHÔNG KHUYẾN NGHỊ VƯỢT QUÁ GIỚI HẠN PHÁP LÝ.
4. Ngoại lệ: Khi không có biển/bản đồ, tự động dùng giới hạn an toàn mặc định theo loại đường (Đô thị 50 km/h, Ngoài đô thị 80 km/h) và gắn cờ 'Ước lượng'.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CONFIG_PATH = Path("ai_engine/config/adas_config.json")

# Bảng tốc độ theo mật độ giao thông (số xe trong vùng quan sát)
DENSITY_SPEED_TABLE: List[Tuple[int, float]] = [
    (0,  120.0),
    (2,  100.0),
    (4,   80.0),
    (6,   60.0),
    (10,  40.0),
    (15,  30.0),  # Ùn tắc / mật độ dày đặc
]

COLLISION_SPEED_REDUCTION = 0.70


def _load_speed_rec_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("modules_config", {}).get("m10_speed_recommendation", {})
        except Exception:
            pass
    return {
        "rule_engine_mode": "strict_minimum",
        "default_urban_speed_kph": 50.0,
        "default_rural_speed_kph": 80.0
    }


def _density_speed_limit(vehicle_count: int) -> float:
    limit = 120.0
    for threshold, speed in sorted(DENSITY_SPEED_TABLE, key=lambda x: x[0], reverse=True):
        if vehicle_count >= threshold:
            limit = speed
            break
    return limit


def recommend_speed(
    current_speed: float,
    vehicle_count_in_zone: int,
    sign_speed_limit: Optional[float] = None,
    safe_distance_speed: Optional[float] = None,
    has_collision_warning: bool = False,
    vehicle_type: str = "car",
    is_urban_area: bool = True,
    is_rainy: bool = False,
) -> Dict[str, Any]:
    """
    Tính toán tốc độ khuyến nghị tối đa an toàn và giải thích nguyên do.
    """
    current_speed = max(0.0, current_speed)
    cfg = _load_speed_rec_config()
    limits: List[Tuple[float, str]] = []
    is_estimated = False

    # 1. Giới hạn pháp lý từ biển báo / bản đồ (Ưu tiên số 1)
    if sign_speed_limit is not None and sign_speed_limit > 0:
        legal_lim = float(sign_speed_limit)
        # Theo TT 31/2019 Điều 7: Xe tải > 3.5 tấn hoặc xe khách > 30 chỗ có giới hạn thấp hơn xe con 10 km/h ngoài đô thị
        if not is_urban_area and vehicle_type in ("truck", "bus"):
            legal_lim = max(40.0, legal_lim - 10.0)
            limits.append((legal_lim, f"Biển báo ({sign_speed_limit:.0f} km/h) trừ 10 km/h cho xe tải/xe khách (TT 31/2019)"))
        else:
            limits.append((legal_lim, f"Giới hạn tốc độ theo biển báo: {legal_lim:.0f} km/h"))
    else:
        # Ngoại lệ: Không có biển báo -> Dùng mặc định pháp lý theo loại đường
        default_lim = cfg.get("default_urban_speed_kph", 50.0) if is_urban_area else cfg.get("default_rural_speed_kph", 80.0)
        limits.append((default_lim, f"Mặc định theo TT 31/2019 ({'Đô thị 50 km/h' if is_urban_area else 'Ngoài đô thị 80 km/h'})"))
        is_estimated = True

    # 2. Điều kiện thời tiết (Mưa, sương mù làm giảm 15% tốc độ an toàn)
    if is_rainy:
        rain_limit = limits[0][0] * 0.85
        limits.append((rain_limit, "Đường ướt/trời mưa: Giảm 15% tốc độ để bảo đảm quãng đường phanh"))

    # 3. Khoảng cách an toàn với xe phía trước
    if safe_distance_speed is not None and safe_distance_speed >= 0:
        limits.append((float(safe_distance_speed), f"Khoảng cách an toàn xe trước: tối đa {safe_distance_speed:.1f} km/h"))

    # 4. Mật độ xe (Kẹt xe / xe máy đông đúc)
    density_limit = _density_speed_limit(vehicle_count_in_zone)
    if density_limit < 120.0:
        limits.append((density_limit, f"Mật độ giao thông cao ({vehicle_count_in_zone} phương tiện trong vùng)"))

    # 5. Cảnh báo va chạm tức thời
    if has_collision_warning and current_speed > 0:
        collision_limit = current_speed * COLLISION_SPEED_REDUCTION
        limits.append((collision_limit, "⚠️ CẢNH BÁO VA CHẠM — Giảm tốc độ khẩn cấp!"))

    # Lấy giới hạn khắt khe nhất (nhỏ nhất)
    recommended_speed, primary_reason = min(limits, key=lambda x: x[0])
    recommended_speed = max(0.0, round(recommended_speed, 1))

    # Cấp độ cảnh báo
    if has_collision_warning:
        alert_level = "danger"
    elif current_speed > recommended_speed * 1.10:
        alert_level = "warning"
    elif current_speed > recommended_speed:
        alert_level = "caution"
    else:
        alert_level = "normal"

    return {
        "recommended_speed": recommended_speed,
        "primary_reason": primary_reason,
        "reason": primary_reason,
        "is_estimated": is_estimated,
        "sources": [{"limit": round(lim, 1), "reason": rsn} for lim, rsn in limits],
        "alert_level": alert_level,
        "current_speed": round(current_speed, 1),
        "over_limit": max(0.0, round(current_speed - recommended_speed, 1)),
        "speed_status": "ƯỚC LƯỢNG" if is_estimated else "CHÍNH THỨC"
    }


def suggest_speed(
    current_speed: float,
    vehicle_count_in_zone: int,
    sign_speed_limit: Optional[float] = None,
    safe_distance_speed: Optional[float] = None,
) -> Dict[str, Any]:
    """Tương thích ngược với interface cũ."""
    res = recommend_speed(
        current_speed=current_speed,
        vehicle_count_in_zone=vehicle_count_in_zone,
        sign_speed_limit=sign_speed_limit,
        safe_distance_speed=safe_distance_speed
    )
    return {"recommended_speed": res["recommended_speed"], "reason": res["reason"]}
