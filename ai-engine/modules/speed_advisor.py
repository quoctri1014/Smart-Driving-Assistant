"""
speed_advisor.py
----------------
Gợi ý tốc độ an toàn dựa trên mật độ giao thông, khoảng cách an toàn và biển báo.
"""
from typing import Optional, Dict, Any

def suggest_speed(
    current_speed: float,
    vehicle_count_in_zone: int,
    sign_speed_limit: Optional[float] = None,
    safe_distance_speed: Optional[float] = None
) -> Dict[str, Any]:
    """
    Tính toán tốc độ khuyến nghị dựa trên các nguồn dữ liệu.
    Không tạo ra tốc độ âm.
    Trả về giới hạn khắt khe nhất (nhỏ nhất) làm recommended_speed.
    """
    if current_speed < 0:
        current_speed = 0.0

    limits = []
    
    if sign_speed_limit is not None and sign_speed_limit > 0:
        limits.append((float(sign_speed_limit), "Giới hạn tốc độ biển báo"))
        
    if safe_distance_speed is not None and safe_distance_speed > 0:
        limits.append((float(safe_distance_speed), "Giữ khoảng cách an toàn với xe trước"))
        
    # Heuristic mật độ xe
    if vehicle_count_in_zone >= 5:
        density_limit = max(20.0, current_speed - 15.0)
        limits.append((float(density_limit), "Mật độ giao thông cao"))
        
    if not limits:
        return {
            "recommended_speed": None,
            "reason": "Chưa có đủ dữ kiện giới hạn tốc độ"
        }
        
    # Chọn giới hạn khắt khe nhất
    recommended_speed, reason = min(limits, key=lambda x: x[0])
    
    return {
        "recommended_speed": recommended_speed,
        "reason": reason
    }
