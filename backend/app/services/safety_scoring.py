"""
safety_scoring.py
-----------------
Dịch vụ tính toán và quản lý điểm an toàn (Safety Score) cho tài xế và chuyến đi:
- Khởi điểm: 100 điểm.
- Trừ điểm theo mức độ nghiêm trọng và loại vi phạm khi Dispatcher xác nhận (CONFIRM):
  * CRITICAL (Ngủ gật, Nguy cơ đâm va khẩn): -15 điểm
  * WARNING (Quá tốc độ, Không thắt dây, Cự ly nguy hiểm, Không mũ bảo hiểm): -5 điểm
  * INFO: -1 điểm
- Điểm được chặn trong khoảng [0.0, 100.0].
- Hỗ trợ phục hồi điểm an toàn khi tài xế hoàn thành bài tập huấn luyện (Coaching).
"""

from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models_db.driver import Driver
from backend.app.models_db.journey import Journey


SEVERITY_DEDUCTION = {
    "CRITICAL": 15.0,
    "WARNING": 5.0,
    "INFO": 1.0,
}

VIOLATION_TYPE_MULTIPLIER = {
    "drowsy": 1.2,           # Buồn ngủ cực kỳ nguy hiểm
    "collision_danger": 1.2, # Nguy cơ đâm va TTC khẩn
    "speed_limit": 1.0,
    "no_seatbelt": 1.0,
    "safe_distance": 1.0,
    "helmet_violation": 1.0,
}


def calculate_deduction(severity: str, violation_type: str = "general") -> float:
    base = SEVERITY_DEDUCTION.get(severity.upper(), 5.0)
    mult = VIOLATION_TYPE_MULTIPLIER.get(violation_type.lower(), 1.0)
    return round(base * mult, 1)


async def deduct_driver_safety_score(
    db: AsyncSession,
    driver_id: int,
    severity: str,
    violation_type: str,
    journey_id: int = None
) -> Tuple[float, float]:
    """
    Trừ điểm an toàn của tài xế và cập nhật chuyến đi (nếu có).
    Trả về: (new_score, deduction)
    """
    deduction = calculate_deduction(severity, violation_type)

    driver_stmt = select(Driver).where(Driver.id == driver_id)
    driver = (await db.execute(driver_stmt)).scalar_one_or_none()
    if not driver:
        return 100.0, 0.0

    current_score = getattr(driver, "safety_score", 100.0) or 100.0
    new_driver_score = max(0.0, round(current_score - deduction, 1))
    driver.safety_score = new_driver_score

    # Cập nhật điểm hành trình nếu có
    if journey_id:
        jrn_stmt = select(Journey).where(Journey.id == journey_id)
        journey = (await db.execute(jrn_stmt)).scalar_one_or_none()
        if journey:
            j_score = getattr(journey, "safety_score", 100.0) or 100.0
            journey.safety_score = max(0.0, round(j_score - deduction, 1))

    await db.flush()
    return new_driver_score, deduction


async def restore_driver_safety_score(
    db: AsyncSession,
    driver_id: int,
    bonus_points: float = 5.0
) -> float:
    """
    Phục hồi điểm an toàn cho tài xế sau khi hoàn thành khóa huấn luyện coaching.
    """
    driver_stmt = select(Driver).where(Driver.id == driver_id)
    driver = (await db.execute(driver_stmt)).scalar_one_or_none()
    if not driver:
        return 100.0

    current_score = getattr(driver, "safety_score", 100.0) or 100.0
    new_score = min(100.0, round(current_score + bonus_points, 1))
    driver.safety_score = new_score
    await db.flush()
    return new_score
