from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from backend.app.database.session import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.models_db.driver import Driver
from backend.app.crud import violation_crud

router = APIRouter()

@router.get("/")
async def get_violations(
    skip: int = 0, 
    limit: int = 50,
    violation_type: Optional[str] = None,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách vi phạm của tài xế đang đăng nhập"""
    violations = await violation_crud.get_violations(
        db, 
        skip=skip, 
        limit=limit, 
        driver_id=current_user.id,
        violation_type=violation_type
    )
    return violations
