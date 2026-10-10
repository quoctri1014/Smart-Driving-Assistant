"""
safe_distance_calculator.py
----------------------------
Tính và đề xuất khoảng cách an toàn theo đúng quy định pháp luật Việt Nam:
Căn cứ: Điều 11 Thông tư số 31/2019/TT-BGTVT ngày 29/08/2019 của Bộ Giao thông vận tải:
- V <= 60 km/h: Người lái xe chủ động giữ khoảng cách an toàn phù hợp (khuyến nghị >= 35m).
- 60 < V <= 80 km/h: Khoảng cách an toàn tối thiểu là 55m.
- 80 < V <= 100 km/h: Khoảng cách an toàn tối thiểu là 70m.
- 100 < V <= 120 km/h: Khoảng cách an toàn tối thiểu là 100m.
- Khi trời mưa, sương mù, mặt đường trơn trượt: Nhân hệ số an toàn x1.30.

Ngoại lệ:
- Tốc độ dưới 60 km/h: Luật để tài xế tự quyết khoảng cách phù hợp.
- Khoảng cách chưa được kiểm chuẩn: Gắn cờ 'khoảng cách ước lượng'.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import config

CONFIG_PATH = Path("ai_engine/config/adas_config.json")
GRAVITY_MS2 = 9.81
FRICTION_DRY = 0.75
FRICTION_WET = 0.45
REACTION_TIME_S = 0.75


def _load_legal_safe_distances() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("legal_regulations", {}).get("tt_31_2019_tt_bgtvt", {})
        except Exception:
            pass
    return {
        "article_11_safe_distance_dry_road": [
            {"max_speed_kph": 60, "min_safe_distance_m": 35.0},
            {"max_speed_kph": 80, "min_safe_distance_m": 55.0},
            {"max_speed_kph": 100, "min_safe_distance_m": 70.0},
            {"max_speed_kph": 120, "min_safe_distance_m": 100.0}
        ],
        "adverse_weather_distance_multiplier": 1.30
    }


def get_tt31_safe_distance(speed_kmh: float, is_wet: bool = False) -> Tuple[float, bool, str]:
    """
    Tra cứu khoảng cách an toàn tối thiểu theo Điều 11 Thông tư 31/2019/TT-BGTVT.
    Trả về: (khoảng_cách_mét, là_tự_quyết_định, căn_cứ_pháp_lý)
    """
    legal_data = _load_legal_safe_distances()
    table = legal_data.get("article_11_safe_distance_dry_road", [])
    multiplier = legal_data.get("adverse_weather_distance_multiplier", 1.30) if is_wet else 1.0

    if speed_kmh <= 60.0:
        base_d = 35.0
        is_discretionary = True
        citation = "TT 31/2019/TT-BGTVT Điều 11: V <= 60 km/h tài xế chủ động giữ khoảng cách phù hợp"
    elif speed_kmh <= 80.0:
        base_d = 55.0
        is_discretionary = False
        citation = "TT 31/2019/TT-BGTVT Điều 11: 60 < V <= 80 km/h tối thiểu 55m"
    elif speed_kmh <= 100.0:
        base_d = 70.0
        is_discretionary = False
        citation = "TT 31/2019/TT-BGTVT Điều 11: 80 < V <= 100 km/h tối thiểu 70m"
    else:
        base_d = 100.0
        is_discretionary = False
        citation = "TT 31/2019/TT-BGTVT Điều 11: 100 < V <= 120 km/h tối thiểu 100m"

    final_d = round(base_d * multiplier, 1)
    if is_wet:
        citation += " (Đã điều chỉnh x1.30 do đường ướt/mưa)"

    return final_d, is_discretionary, citation


def safe_speed_for_distance(distance_m: float, friction: float = FRICTION_DRY) -> float:
    """Tính tốc độ an toàn tối đa (km/h) để có thể dừng trong khoảng cách distance_m."""
    if distance_m <= 0:
        return 0.0
    a = 1.0 / (2 * friction * GRAVITY_MS2)
    b = REACTION_TIME_S
    c = -distance_m
    discriminant = b ** 2 - 4 * a * c
    if discriminant < 0:
        return 0.0
    v = (-b + math.sqrt(discriminant)) / (2 * a)
    return max(0.0, round(v * 3.6, 1))


class SafeDistanceCalculator:
    """
    Tính và đề xuất khoảng cách an toàn đối chiếu Thông tư 31/2019/TT-BGTVT.
    """

    def __init__(self, road_condition: str = "dry"):
        self.road_condition = road_condition
        self.is_wet = (road_condition == "wet")

    def calculate(
        self,
        col_warnings: list,
        speed_map: Dict[int, float],
        estimated_distance_m: Optional[float] = None,
        ego_speed_kmh: Optional[float] = None,
        is_calibrated: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Tính đề xuất khoảng cách an toàn.
        """
        if not col_warnings:
            return None

        if ego_speed_kmh is None or not math.isfinite(ego_speed_kmh) or ego_speed_kmh < 0:
            return None

        # 1. Tra cứu khoảng cách an toàn pháp luật quy định
        min_legal_d, is_discretionary, citation = get_tt31_safe_distance(ego_speed_kmh, self.is_wet)

        # 2. Khoảng cách dừng khẩn cấp vật lý (Physical stopping distance)
        friction = FRICTION_WET if self.is_wet else FRICTION_DRY
        v_ms = ego_speed_kmh / 3.6
        reaction_d = v_ms * REACTION_TIME_S
        braking_d = (v_ms ** 2) / (2 * friction * GRAVITY_MS2)
        physical_stopping_d = round(reaction_d + braking_d, 1)

        # Khoảng cách khuyến nghị thực tế lấy max giữa luật quy định và khoảng cách dừng vật lý
        recommended_distance = max(min_legal_d, physical_stopping_d)
        rec_speed = safe_speed_for_distance(estimated_distance_m, friction) if estimated_distance_m is not None else 0.0

        # 3. Đánh giá khoảng cách hiện tại (nếu có đo được)
        distance_status = "SAFE"
        if estimated_distance_m is not None:
            if estimated_distance_m < physical_stopping_d:
                distance_status = "CRITICAL_TOO_CLOSE"
            elif estimated_distance_m < recommended_distance:
                distance_status = "WARNING_UNSAFE_DISTANCE"

        return {
            "ego_speed_kmh": round(ego_speed_kmh, 1),
            "min_legal_distance_m": min_legal_d,
            "physical_stopping_distance_m": physical_stopping_d,
            "recommended_distance_m": recommended_distance,
            "recommended_speed_kmh": rec_speed,
            "current_distance_m": round(estimated_distance_m, 1) if estimated_distance_m is not None else None,
            "estimated_distance_m": estimated_distance_m,
            "distance_status": distance_status,
            "is_discretionary": is_discretionary,
            "is_calibrated": is_calibrated,
            "distance_confidence_label": "Đo chuẩn xác" if is_calibrated else "Khoảng cách ước lượng",
            "legal_citation": citation,
            "road_condition": "Đường ướt/mưa" if self.is_wet else "Đường khô ráo"
        }
