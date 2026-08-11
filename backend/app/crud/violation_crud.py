from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime
from backend.app.models_db.violation import Violation

async def create_violation(
    db: AsyncSession, 
    violation_type: str, 
    severity: str, 
    image_path: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    session_id: Optional[int] = None
) -> Violation:
    db_violation = Violation(
        violation_type=violation_type,
        severity=severity,
        image_path=image_path,
        vehicle_id=vehicle_id,
        session_id=session_id
    )
    db.add(db_violation)
    await db.commit()
    await db.refresh(db_violation)
    return db_violation

async def get_violations(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    driver_id: Optional[int] = None,
    violation_type: Optional[str] = None
) -> List[Violation]:
    query = select(Violation).order_by(Violation.timestamp.desc())
    
    if violation_type:
        query = query.where(Violation.violation_type == violation_type)
        
    if driver_id:
        from backend.app.models_db.driving_session import DrivingSession
        query = query.join(DrivingSession).where(DrivingSession.driver_id == driver_id)
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
