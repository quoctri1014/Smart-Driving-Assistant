from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.session import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.models_db.driver import Driver
from backend.app.crud import session_crud
from datetime import datetime

router = APIRouter()

@router.get("/")
async def get_sessions(
    skip: int = 0, 
    limit: int = 50,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách phiên lái xe của tài xế đang đăng nhập"""
    sessions = await session_crud.get_sessions_by_driver(
        db, 
        driver_id=current_user.id,
        skip=skip, 
        limit=limit
    )
    return sessions

@router.post("/reset-rest")
async def reset_rest(
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bắt đầu một phiên lái xe mới (đánh dấu tài xế đã nghỉ ngơi)"""
    # 1. Lấy phiên gần nhất và kết thúc nó
    sessions = await session_crud.get_sessions_by_driver(db, current_user.id, limit=1)
    if sessions and len(sessions) > 0:
        latest = sessions[0]
        latest.end_time = datetime.utcnow()
        if latest.start_time:
            delta = latest.end_time - latest.start_time
            latest.total_minutes = delta.total_seconds() / 60.0
        await db.commit()
    
    # 2. Tạo phiên mới
    new_session = await session_crud.create_session(db, current_user.id)
    return {"message": "Rest successful, new session started", "session_id": new_session.id}
