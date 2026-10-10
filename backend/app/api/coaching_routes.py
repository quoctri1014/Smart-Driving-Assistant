from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models_db.driver import Driver
from backend.app.models_db.coaching import CoachingAssignment
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.auth.rbac_service import get_data_scope
from backend.app.auth.scopes import DataScope
from backend.app.crud import coaching_crud
from backend.app.crud.audit_crud import log_audit_event
from backend.app.models_db.notification import Notification
from backend.app.websocket.connection_manager import manager

router = APIRouter()


class CreateCoachingPayload(BaseModel):
    driver_id: int
    title: str = Field(..., min_length=5)
    description: Optional[str] = None
    module_type: str = "GENERAL"
    due_date: Optional[datetime] = None
    violation_id: Optional[int] = None


class CompleteCoachingPayload(BaseModel):
    driver_notes: Optional[str] = Field(None, description="Ghi chú nhận thức / bài học của tài xế")
    bonus_points: float = Field(5.0, ge=1.0, le=10.0, description="Điểm an toàn được phục hồi")


def serialize_coaching(c: CoachingAssignment) -> Dict[str, Any]:
    return {
        "id": c.id,
        "company_id": c.company_id,
        "driver_id": c.driver_id,
        "driver_name": c.driver.full_name if getattr(c, "driver", None) else None,
        "assigned_by": c.assigned_by,
        "assigner_name": c.assigner.full_name if getattr(c, "assigner", None) else None,
        "violation_id": c.violation_id,
        "title": c.title,
        "description": c.description,
        "module_type": c.module_type,
        "status": c.status,
        "due_date": c.due_date.isoformat() if c.due_date else None,
        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        "driver_notes": c.driver_notes,
        "score_restored": c.score_restored,
        "created_at": c.created_at.isoformat() if c.created_at else None
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
@router.post("/records", status_code=status.HTTP_201_CREATED)
async def assign_coaching(
    payload: CreateCoachingPayload,
    current_user: Driver = Depends(require_permission("coaching.assign")),
    db: AsyncSession = Depends(get_db)
):
    """Dispatcher giao bài huấn luyện an toàn cho tài xế sau khi ghi nhận vi phạm"""
    company_id = current_user.organization_id or 1

    assignment = await coaching_crud.create_coaching_assignment(
        db=db,
        company_id=company_id,
        assigned_by=current_user.id,
        driver_id=payload.driver_id,
        title=payload.title,
        description=payload.description,
        module_type=payload.module_type,
        due_date=payload.due_date,
        violation_id=payload.violation_id
    )

    # Thông báo cho tài xế
    notif = Notification(
        company_id=company_id,
        user_id=payload.driver_id,
        title="Khóa huấn luyện an toàn mới",
        message=f"Bạn vừa được giao bài huấn luyện: '{assignment.title}'. Vui lòng hoàn thành để nâng cao kỹ năng và phục hồi điểm an toàn.",
        severity="WARNING",
        resource_type="coaching",
        resource_id=assignment.id
    )
    db.add(notif)
    await db.commit()

    # Audit log
    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="COACHING_ASSIGN",
        resource_type="coaching",
        resource_id=assignment.id,
        details={"driver_id": payload.driver_id, "module_type": payload.module_type}
    )

    await manager.broadcast_alert({
        "type": "coaching_assigned",
        "coaching_id": assignment.id,
        "driver_id": payload.driver_id,
        "title": assignment.title
    })

    return serialize_coaching(assignment)


@router.get("/")
@router.get("/records")
async def list_coaching(
    status_filter: Optional[str] = Query(None, alias="status"),
    driver_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Driver = Depends(require_permission("coaching.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    scope = get_data_scope(current_user)

    target_driver = driver_id
    if scope == DataScope.SELF.value:
        target_driver = current_user.id

    assignments = await coaching_crud.get_coaching_assignments(
        db=db,
        company_id=company_id,
        driver_id=target_driver,
        status=status_filter,
        skip=skip,
        limit=limit
    )
    return [serialize_coaching(c) for c in assignments]


@router.get("/{coaching_id}")
async def get_coaching_detail(
    coaching_id: int,
    current_user: Driver = Depends(require_permission("coaching.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    item = await coaching_crud.get_coaching_by_id(db, coaching_id, company_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài tập huấn luyện")

    scope = get_data_scope(current_user)
    if scope == DataScope.SELF.value and item.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập bài tập này")

    return serialize_coaching(item)


@router.post("/{coaching_id}/complete")
async def complete_coaching_lesson(
    coaching_id: int,
    payload: CompleteCoachingPayload,
    current_user: Driver = Depends(require_permission("coaching.complete")),
    db: AsyncSession = Depends(get_db)
):
    """Tài xế hoàn thành bài tập huấn luyện và nhận phục hồi điểm an toàn"""
    company_id = current_user.organization_id or 1
    try:
        updated = await coaching_crud.complete_coaching(
            db=db,
            coaching_id=coaching_id,
            company_id=company_id,
            driver_id=current_user.id,
            driver_notes=payload.driver_notes,
            bonus_points=payload.bonus_points
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="COACHING_COMPLETE",
        resource_type="coaching",
        resource_id=coaching_id,
        details={"score_restored": payload.bonus_points}
    )

    await manager.broadcast_alert({
        "type": "coaching_completed",
        "coaching_id": coaching_id,
        "driver_id": current_user.id,
        "score_restored": payload.bonus_points
    })

    return serialize_coaching(updated)
