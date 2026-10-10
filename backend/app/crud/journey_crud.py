"""
journey_crud.py
---------------
CRUD operations for Journey Lifecycle & State Machine:
PLANNED -> CHECKLIST -> ACTIVE -> COMPLETED / CANCELLED
"""

import json
from datetime import datetime, timezone
import random
import string
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from backend.app.models_db.journey import Journey
from backend.app.models_db.driving_session import DrivingSession
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.driver import Driver
from backend.app.utils.datetime_utils import utc_now


def generate_journey_code() -> str:
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"JRN-{now_str}-{rand_suffix}"


async def create_journey(
    db: AsyncSession,
    company_id: int,
    dispatcher_id: int,
    vehicle_id: int,
    driver_id: int,
    title: Optional[str] = None,
    start_location: Optional[str] = None,
    destination: Optional[str] = None,
    planned_start_time: Optional[datetime] = None,
    notes: Optional[str] = None
) -> Journey:
    journey_code = generate_journey_code()
    journey = Journey(
        company_id=company_id,
        journey_code=journey_code,
        title=title or f"Chuyến vận tải {journey_code}",
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        dispatcher_id=dispatcher_id,
        status="PLANNED",
        start_location=start_location,
        destination=destination,
        planned_start_time=planned_start_time or utc_now(),
        notes=notes,
        safety_score=100.0,
        checklist_status="PENDING"
    )
    db.add(journey)
    await db.commit()
    await db.refresh(journey)
    return journey


async def get_journeys(
    db: AsyncSession,
    company_id: int,
    driver_id: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Journey]:
    conditions = [Journey.company_id == company_id]
    if driver_id:
        conditions.append(Journey.driver_id == driver_id)
    if vehicle_id:
        conditions.append(Journey.vehicle_id == vehicle_id)
    if status:
        conditions.append(Journey.status == status.upper())

    stmt = (
        select(Journey)
        .where(and_(*conditions))
        .options(
            selectinload(Journey.vehicle),
            selectinload(Journey.driver),
            selectinload(Journey.dispatcher)
        )
        .order_by(desc(Journey.created_at))
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


async def get_journey_by_id(
    db: AsyncSession,
    journey_id: int,
    company_id: int
) -> Optional[Journey]:
    stmt = (
        select(Journey)
        .where(and_(Journey.id == journey_id, Journey.company_id == company_id))
        .options(
            selectinload(Journey.vehicle),
            selectinload(Journey.driver),
            selectinload(Journey.dispatcher),
            selectinload(Journey.violations)
        )
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def submit_pre_trip_checklist(
    db: AsyncSession,
    journey_id: int,
    company_id: int,
    driver_id: int,
    checklist_dict: Dict[str, Any]
) -> Journey:
    journey = await get_journey_by_id(db, journey_id, company_id)
    if not journey:
        raise ValueError("Không tìm thấy chuyến đi")
    if journey.driver_id != driver_id:
        raise PermissionError("Chỉ tài xế được phân công mới có thể nộp checklist chuyến này")
    if journey.status not in ("PLANNED", "CHECKLIST"):
        raise ValueError(f"Không thể nộp checklist ở trạng thái {journey.status}")

    # Kiểm tra các mục an toàn tối thiểu (road camera, brakes, tires, docs)
    critical_items = ["roadCamera", "brakes", "tires"]
    passed = True
    for item in critical_items:
        if checklist_dict.get(item) is False:
            passed = False
            break

    journey.checklist_status = "PASSED" if passed else "FAILED"
    journey.checklist_data = json.dumps(checklist_dict, ensure_ascii=False)
    journey.checklist_submitted_at = utc_now()
    journey.status = "CHECKLIST"

    await db.commit()
    await db.refresh(journey)
    return journey


async def start_journey(
    db: AsyncSession,
    journey_id: int,
    company_id: int,
    driver_id: int
) -> Journey:
    journey = await get_journey_by_id(db, journey_id, company_id)
    if not journey:
        raise ValueError("Không tìm thấy chuyến đi")
    if journey.driver_id != driver_id:
        raise PermissionError("Chỉ tài xế được phân công mới có thể bắt đầu chuyến đi này")
    if journey.status != "CHECKLIST":
        raise ValueError(f"Chuyến đi chưa hoàn thành checklist trước chuyến (Trạng thái hiện tại: {journey.status})")
    if journey.checklist_status != "PASSED":
        raise ValueError("Checklist an toàn xe chưa đạt chuẩn PASSED, không thể khởi hành")

    # Kiểm tra xem tài xế đã có chuyến khác đang ACTIVE không
    active_stmt = select(Journey).where(
        and_(
            Journey.driver_id == driver_id,
            Journey.status == "ACTIVE",
            Journey.id != journey_id
        )
    )
    active_other = (await db.execute(active_stmt)).scalars().first()
    if active_other:
        raise ValueError(f"Tài xế đang có chuyến {active_other.journey_code} đang chạy, vui lòng hoàn thành trước")

    now = utc_now()
    journey.status = "ACTIVE"
    journey.actual_start_time = now

    # Tự động tạo DrivingSession để đồng bộ hệ thống AI telemetry
    session = DrivingSession(
        driver_id=driver_id,
        company_id=company_id,
        start_time=now
    )
    db.add(session)
    await db.flush()

    journey.session_id = session.id
    await db.commit()
    await db.refresh(journey)
    return journey


async def complete_journey(
    db: AsyncSession,
    journey_id: int,
    company_id: int,
    user_id: int,
    total_distance_km: Optional[float] = None,
    notes: Optional[str] = None
) -> Journey:
    journey = await get_journey_by_id(db, journey_id, company_id)
    if not journey:
        raise ValueError("Không tìm thấy chuyến đi")
    if journey.status != "ACTIVE":
        raise ValueError(f"Chỉ chuyến đi đang ACTIVE mới có thể hoàn thành (Hiện tại: {journey.status})")

    now = utc_now()
    journey.status = "COMPLETED"
    journey.completed_at = now
    if total_distance_km is not None:
        journey.total_distance_km = total_distance_km
    if notes:
        journey.notes = (journey.notes or "") + f"\n[Hoàn thành]: {notes}"

    # Đóng session nếu có
    if journey.session_id:
        sess_stmt = select(DrivingSession).where(DrivingSession.id == journey.session_id)
        session = (await db.execute(sess_stmt)).scalar_one_or_none()
        if session and session.end_time is None:
            session.end_time = now
            if session.start_time:
                session.total_minutes = round((now - session.start_time).total_seconds() / 60.0, 1)

    await db.commit()
    await db.refresh(journey)
    return journey


async def cancel_journey(
    db: AsyncSession,
    journey_id: int,
    company_id: int,
    user_id: int,
    reason: str
) -> Journey:
    journey = await get_journey_by_id(db, journey_id, company_id)
    if not journey:
        raise ValueError("Không tìm thấy chuyến đi")
    if journey.status in ("COMPLETED", "CANCELLED"):
        raise ValueError(f"Chuyến đi đã {journey.status}, không thể hủy")

    now = utc_now()
    journey.status = "CANCELLED"
    journey.cancelled_at = now
    journey.cancel_reason = reason

    if journey.session_id:
        sess_stmt = select(DrivingSession).where(DrivingSession.id == journey.session_id)
        session = (await db.execute(sess_stmt)).scalar_one_or_none()
        if session and session.end_time is None:
            session.end_time = now

    await db.commit()
    await db.refresh(journey)
    return journey
