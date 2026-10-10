"""
coaching_crud.py
----------------
CRUD operations for Safety Coaching Assignments:
Assignment, Tracking, Completion, and Safety Score Restoration.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from backend.app.models_db.coaching import CoachingAssignment
from backend.app.models_db.driver import Driver
from backend.app.models_db.violation import Violation
from backend.app.services.safety_scoring import restore_driver_safety_score
from backend.app.utils.datetime_utils import utc_now


async def create_coaching_assignment(
    db: AsyncSession,
    company_id: int,
    assigned_by: int,
    driver_id: int,
    title: str,
    description: Optional[str] = None,
    module_type: str = "GENERAL",
    due_date: Optional[datetime] = None,
    violation_id: Optional[int] = None
) -> CoachingAssignment:
    assignment = CoachingAssignment(
        company_id=company_id,
        driver_id=driver_id,
        assigned_by=assigned_by,
        violation_id=violation_id,
        title=title,
        description=description,
        module_type=module_type.upper(),
        status="ASSIGNED",
        due_date=due_date,
        score_restored=0.0
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def get_coaching_assignments(
    db: AsyncSession,
    company_id: int,
    driver_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[CoachingAssignment]:
    conditions = [CoachingAssignment.company_id == company_id]
    if driver_id:
        conditions.append(CoachingAssignment.driver_id == driver_id)
    if status:
        conditions.append(CoachingAssignment.status == status.upper())

    stmt = (
        select(CoachingAssignment)
        .where(and_(*conditions))
        .options(
            selectinload(CoachingAssignment.driver),
            selectinload(CoachingAssignment.assigner),
            selectinload(CoachingAssignment.violation)
        )
        .order_by(desc(CoachingAssignment.created_at))
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


async def get_coaching_by_id(
    db: AsyncSession,
    coaching_id: int,
    company_id: int
) -> Optional[CoachingAssignment]:
    stmt = (
        select(CoachingAssignment)
        .where(and_(CoachingAssignment.id == coaching_id, CoachingAssignment.company_id == company_id))
        .options(
            selectinload(CoachingAssignment.driver),
            selectinload(CoachingAssignment.assigner),
            selectinload(CoachingAssignment.violation)
        )
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def complete_coaching(
    db: AsyncSession,
    coaching_id: int,
    company_id: int,
    driver_id: int,
    driver_notes: Optional[str] = None,
    bonus_points: float = 5.0
) -> CoachingAssignment:
    assignment = await get_coaching_by_id(db, coaching_id, company_id)
    if not assignment:
        raise ValueError("Không tìm thấy bài tập huấn luyện")
    if assignment.driver_id != driver_id:
        raise PermissionError("Chỉ tài xế được chỉ định mới có thể nộp bài tập này")
    if assignment.status == "COMPLETED":
        return assignment

    now = utc_now()
    assignment.status = "COMPLETED"
    assignment.completed_at = now
    assignment.driver_notes = driver_notes
    assignment.score_restored = bonus_points

    # Phục hồi điểm an toàn cho tài xế
    await restore_driver_safety_score(db, driver_id=driver_id, bonus_points=bonus_points)

    await db.commit()
    await db.refresh(assignment)
    return assignment
