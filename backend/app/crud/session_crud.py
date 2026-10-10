from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from datetime import datetime
from backend.app.models_db.driving_session import DrivingSession

async def create_session(db: AsyncSession, driver_id: int, organization_id: int) -> DrivingSession:
    db_session = DrivingSession(driver_id=driver_id, organization_id=organization_id)
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_sessions_by_driver(db: AsyncSession, driver_id: int, skip: int = 0, limit: int = 100) -> List[DrivingSession]:
    query = select(DrivingSession).where(DrivingSession.driver_id == driver_id).order_by(DrivingSession.start_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
