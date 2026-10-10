import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models_db.driver import Driver
from backend.app.models_db.journey import Journey
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.auth.rbac_service import get_data_scope
from backend.app.auth.scopes import DataScope
from backend.app.crud import journey_crud
from backend.app.crud.audit_crud import log_audit_event
from backend.app.models_db.notification import Notification
from backend.app.websocket.connection_manager import manager

router = APIRouter()


class CreateJourneyPayload(BaseModel):
    vehicle_id: int
    driver_id: int
    title: Optional[str] = None
    start_location: Optional[str] = None
    destination: Optional[str] = None
    planned_start_time: Optional[datetime] = None
    notes: Optional[str] = None


class ChecklistPayload(BaseModel):
    roadCamera: bool = True
    cabinCamera: bool = True
    brakes: bool = True
    tires: bool = True
    lights: bool = True
    documents: bool = True
    notes: Optional[str] = None


class CompleteJourneyPayload(BaseModel):
    total_distance_km: Optional[float] = None
    notes: Optional[str] = None


class CancelJourneyPayload(BaseModel):
    reason: str = Field(..., min_length=3, description="Lý do hủy chuyến bắt buộc")


def serialize_journey(j: Journey) -> Dict[str, Any]:
    return {
        "id": j.id,
        "company_id": j.company_id,
        "journey_code": j.journey_code,
        "title": j.title,
        "vehicle_id": j.vehicle_id,
        "vehicle_plate": j.vehicle.license_plate if getattr(j, "vehicle", None) else None,
        "driver_id": j.driver_id,
        "driver_name": j.driver.full_name if getattr(j, "driver", None) else None,
        "dispatcher_id": j.dispatcher_id,
        "dispatcher_name": j.dispatcher.full_name if getattr(j, "dispatcher", None) else None,
        "status": j.status,
        "start_location": j.start_location,
        "destination": j.destination,
        "planned_start_time": j.planned_start_time.isoformat() if j.planned_start_time else None,
        "actual_start_time": j.actual_start_time.isoformat() if j.actual_start_time else None,
        "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        "cancelled_at": j.cancelled_at.isoformat() if j.cancelled_at else None,
        "cancel_reason": j.cancel_reason,
        "checklist_status": j.checklist_status,
        "checklist_data": json.loads(j.checklist_data) if j.checklist_data else None,
        "checklist_submitted_at": j.checklist_submitted_at.isoformat() if j.checklist_submitted_at else None,
        "session_id": j.session_id,
        "safety_score": j.safety_score,
        "total_distance_km": j.total_distance_km,
        "notes": j.notes,
        "created_at": j.created_at.isoformat() if j.created_at else None
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_journey(
    payload: CreateJourneyPayload,
    current_user: Driver = Depends(require_permission("journey.create")),
    db: AsyncSession = Depends(get_db)
):
    """Dispatcher tạo chuyến vận tải và phân công xe cho tài xế (Trạng thái: PLANNED)"""
    company_id = current_user.organization_id or 1

    journey = await journey_crud.create_journey(
        db=db,
        company_id=company_id,
        dispatcher_id=current_user.id,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        title=payload.title,
        start_location=payload.start_location,
        destination=payload.destination,
        planned_start_time=payload.planned_start_time,
        notes=payload.notes
    )

    # Gửi thông báo đến tài xế
    notif = Notification(
        company_id=company_id,
        user_id=payload.driver_id,
        title="Phân công chuyến đi mới",
        message=f"Bạn vừa được điều phối chuyến '{journey.title}' ({journey.journey_code}). Vui lòng kiểm tra xe trước khi khởi hành.",
        severity="INFO",
        resource_type="journey",
        resource_id=journey.id
    )
    db.add(notif)
    await db.commit()

    # Audit log
    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="JOURNEY_CREATE",
        resource_type="journey",
        resource_id=journey.id,
        details={"journey_code": journey.journey_code, "driver_id": payload.driver_id, "vehicle_id": payload.vehicle_id}
    )

    # Realtime WebSocket broadcast
    await manager.broadcast_alert({
        "type": "journey_created",
        "journey_id": journey.id,
        "journey_code": journey.journey_code,
        "driver_id": payload.driver_id,
        "status": "PLANNED"
    })

    return serialize_journey(journey)


@router.get("/")
async def list_journeys(
    status_filter: Optional[str] = Query(None, alias="status"),
    driver_id: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Driver = Depends(require_permission("journey.view")),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách chuyến đi theo phạm vi quyền RBAC"""
    company_id = current_user.organization_id or 1
    scope = get_data_scope(current_user)

    target_driver_id = driver_id
    if scope == DataScope.SELF.value:
        target_driver_id = current_user.id

    journeys = await journey_crud.get_journeys(
        db=db,
        company_id=company_id,
        driver_id=target_driver_id,
        vehicle_id=vehicle_id,
        status=status_filter,
        skip=skip,
        limit=limit
    )
    return [serialize_journey(j) for j in journeys]


@router.get("/{journey_id}")
async def get_journey_detail(
    journey_id: int,
    current_user: Driver = Depends(require_permission("journey.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    journey = await journey_crud.get_journey_by_id(db, journey_id, company_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyến đi")

    scope = get_data_scope(current_user)
    if scope == DataScope.SELF.value and journey.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập chuyến đi này")

    return serialize_journey(journey)


@router.post("/{journey_id}/checklist")
async def submit_checklist(
    journey_id: int,
    payload: ChecklistPayload,
    current_user: Driver = Depends(require_permission("journey.checklist")),
    db: AsyncSession = Depends(get_db)
):
    """Tài xế thực hiện kiểm tra xe trước chuyến (Pre-trip checklist)"""
    company_id = current_user.organization_id or 1
    try:
        updated = await journey_crud.submit_pre_trip_checklist(
            db=db,
            journey_id=journey_id,
            company_id=company_id,
            driver_id=current_user.id,
            checklist_dict=payload.model_dump()
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="JOURNEY_CHECKLIST_SUBMIT",
        resource_type="journey",
        resource_id=journey_id,
        details={"status": updated.checklist_status}
    )

    await manager.broadcast_alert({
        "type": "journey_checklist_updated",
        "journey_id": journey_id,
        "checklist_status": updated.checklist_status
    })

    return serialize_journey(updated)


@router.post("/{journey_id}/start")
async def start_active_journey(
    journey_id: int,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bắt đầu ca lái xe (ACTIVE), liên kết với telemetry session"""
    company_id = current_user.organization_id or 1
    try:
        updated = await journey_crud.start_journey(
            db=db,
            journey_id=journey_id,
            company_id=company_id,
            driver_id=current_user.id
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="JOURNEY_START",
        resource_type="journey",
        resource_id=journey_id,
        details={"session_id": updated.session_id}
    )

    await manager.broadcast_alert({
        "type": "journey_started",
        "journey_id": journey_id,
        "session_id": updated.session_id,
        "driver_id": current_user.id
    })

    return serialize_journey(updated)


class StartJourneyDirectPayload(BaseModel):
    vehicle_id: Optional[int] = None
    title: Optional[str] = "Hành trình di chuyển"

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_new_journey_direct(
    payload: Optional[StartJourneyDirectPayload] = None,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Khởi tạo một phiên hành trình mới trực tiếp (Session/Journey)"""
    company_id = current_user.organization_id or 1
    v_id = payload.vehicle_id if payload and payload.vehicle_id else 1
    title = payload.title if payload and payload.title else "Hành trình di chuyển"
    
    journey = await journey_crud.create_journey(
        db=db,
        company_id=company_id,
        dispatcher_id=current_user.id,
        vehicle_id=v_id,
        driver_id=current_user.id,
        title=title
    )
    started = await journey_crud.start_journey(db, journey.id, company_id, current_user.id)
    return serialize_journey(started)

@router.get("/{journey_id}/timeline")
async def get_journey_timeline(
    journey_id: int,
    current_user: Driver = Depends(require_permission("journey.view")),
    db: AsyncSession = Depends(get_db)
):
    """Lấy chuỗi sự kiện telemetry theo mốc thời gian của hành trình"""
    from sqlalchemy import select
    from backend.app.models_db.trip_event import TripEvent
    company_id = current_user.organization_id or 1
    journey = await journey_crud.get_journey_by_id(db, journey_id, company_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Không tìm thấy chuyến đi")

    events = []
    if journey.session_id:
        res = await db.execute(
            select(TripEvent).where(TripEvent.session_id == journey.session_id).order_by(TripEvent.sequence_num.asc(), TripEvent.timestamp.asc())
        )
        events = res.scalars().all()

    return {
        "journey_id": journey.id,
        "journey_code": journey.journey_code,
        "session_id": journey.session_id,
        "events": [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "video_offset_ms": ev.video_offset_ms,
                "sequence_num": ev.sequence_num,
                "severity": ev.severity,
                "latitude": ev.latitude,
                "longitude": ev.longitude,
                "metadata": json.loads(ev.metadata_json) if ev.metadata_json else None
            }
            for ev in events
        ]
    }

@router.post("/{journey_id}/complete")
@router.post("/{journey_id}/end")
async def complete_active_journey(
    journey_id: int,
    payload: CompleteJourneyPayload,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kết thúc chuyến đi an toàn (COMPLETED)"""
    company_id = current_user.organization_id or 1
    try:
        updated = await journey_crud.complete_journey(
            db=db,
            journey_id=journey_id,
            company_id=company_id,
            user_id=current_user.id,
            total_distance_km=payload.total_distance_km,
            notes=payload.notes
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="JOURNEY_COMPLETE",
        resource_type="journey",
        resource_id=journey_id,
        details={"safety_score": updated.safety_score, "distance_km": updated.total_distance_km}
    )

    await manager.broadcast_alert({
        "type": "journey_completed",
        "journey_id": journey_id,
        "safety_score": updated.safety_score
    })

    return serialize_journey(updated)


@router.post("/{journey_id}/cancel")
async def cancel_journey_trip(
    journey_id: int,
    payload: CancelJourneyPayload,
    current_user: Driver = Depends(require_permission("journey.manage")),
    db: AsyncSession = Depends(get_db)
):
    """Hủy chuyến vận tải (CANCELLED) kèm lý do giải trình"""
    company_id = current_user.organization_id or 1
    try:
        updated = await journey_crud.cancel_journey(
            db=db,
            journey_id=journey_id,
            company_id=company_id,
            user_id=current_user.id,
            reason=payload.reason
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="JOURNEY_CANCEL",
        resource_type="journey",
        resource_id=journey_id,
        details={"reason": payload.reason}
    )

    await manager.broadcast_alert({
        "type": "journey_cancelled",
        "journey_id": journey_id,
        "reason": payload.reason
    })

    return serialize_journey(updated)
