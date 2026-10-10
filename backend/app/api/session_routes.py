from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel

from backend.app.models_db.driving_session import DrivingSession
from backend.app.models_db.trip_event import TripEvent
from backend.app.models_db.driver import Driver
from backend.app.database.session import get_db
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.auth.rbac_service import apply_data_scope, can_access_resource
from backend.app.crud import session_crud

router = APIRouter()

class StartTripPayload(BaseModel):
    vehicle_id: Optional[int] = None

@router.get("/active-trip")
async def get_active_trip_for_driver(
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Phục vụ Mobile Recovery Flow: Kiểm tra chuyến đi đang hoạt động khi mở lại app"""
    query = select(DrivingSession).where(
        and_(
            DrivingSession.driver_id == current_user.id,
            DrivingSession.end_time.is_(None)
        )
    ).order_by(DrivingSession.start_time.desc()).limit(1)

    result = await db.execute(query)
    active_session = result.scalars().first()

    if not active_session:
        return {"has_active_trip": False, "session": None}

    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    return {
        "has_active_trip": True,
        "session": {
            "id": active_session.id,
            "driver_id": active_session.driver_id,
            "organization_id": active_session.organization_id,
            "start_time": active_session.start_time.isoformat() if active_session.start_time else None,
            "elapsed_seconds": int((now_utc - active_session.start_time).total_seconds()) if active_session.start_time else 0
        }
    }

@router.get("/active")
async def get_active_sessions_list(
    current_user: Driver = Depends(require_permission("journey.view")),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách các phiên giám sát camera đang hoạt động (Active Streaming Sessions)"""
    from backend.app.websocket.connection_manager import manager
    company_id = current_user.organization_id or 1

    query = select(DrivingSession).where(
        and_(
            DrivingSession.organization_id == company_id,
            DrivingSession.end_time.is_(None)
        )
    ).order_by(DrivingSession.start_time.desc())
    result = await db.execute(query)
    active_db_sessions = result.scalars().all()

    active_stream_count = len(getattr(manager, "active_connections", []))

    return {
        "active_streaming_count": active_stream_count,
        "active_sessions": [
            {
                "id": s.id,
                "driver_id": s.driver_id,
                "organization_id": s.organization_id,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "status": "LIVE_STREAMING"
            }
            for s in active_db_sessions
        ]
    }

@router.post("/start", status_code=status.HTTP_200_OK)
async def start_trip(
    payload: Optional[StartTripPayload] = None,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bắt đầu chuyến đi với bảo vệ Double Start Trip (Enforce 1 Active Trip / Driver).
    Nếu tài xế đã có chuyến đi đang hoạt động: Trả về phiên hiện tại (Idempotent), không tạo duplicate.
    """
    company_id = current_user.organization_id or 1

    # Kiểm tra xem đã có active session chưa
    existing_query = select(DrivingSession).where(
        and_(
            DrivingSession.driver_id == current_user.id,
            DrivingSession.end_time.is_(None)
        )
    ).order_by(DrivingSession.start_time.desc()).limit(1)

    existing_session = (await db.execute(existing_query)).scalars().first()
    if existing_session:
        return {
            "message": "Đang tiếp tục chuyến đi hiện tại (Active Trip Resumed)",
            "session_id": existing_session.id,
            "start_time": existing_session.start_time.isoformat() if existing_session.start_time else None,
            "is_resumed": True
        }

    # Tạo phiên mới với Database Invariant Protection
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        new_session = DrivingSession(
            driver_id=current_user.id,
            company_id=company_id,
            start_time=now_utc
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
    except Exception:
        await db.rollback()
        existing_session = (await db.execute(existing_query)).scalars().first()
        if existing_session:
            return {
                "message": "Đang tiếp tục chuyến đi hiện tại (Active Trip Resumed)",
                "session_id": existing_session.id,
                "start_time": existing_session.start_time.isoformat() if existing_session.start_time else None,
                "is_resumed": True
            }
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Xung đột khởi tạo chuyến đi: Đã có chuyến đi đang hoạt động"
        )

    # Ghi sự kiện TRIP_STARTED
    trip_start_event = TripEvent(
        session_id=new_session.id,
        event_type="TRIP_STARTED",
        timestamp=now_utc,
        video_offset_ms=0,
        sequence_num=1,
        severity="INFO",
        driver_id=current_user.id,
        vehicle_id=payload.vehicle_id if payload else None
    )
    db.add(trip_start_event)
    await db.commit()

    return {
        "message": "Bắt đầu chuyến đi mới thành công",
        "session_id": new_session.id,
        "start_time": new_session.start_time.isoformat(),
        "is_resumed": False
    }

@router.post("/{session_id}/end")
async def end_trip(
    session_id: int,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kết thúc chuyến đi và tính toán tổng thời gian lái xe"""
    company_id = current_user.organization_id or 1
    session = (await db.execute(
        select(DrivingSession).where(
            and_(
                DrivingSession.id == session_id,
                DrivingSession.organization_id == company_id
            )
        )
    )).scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hành trình")

    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=session.organization_id,
        resource_driver_id=session.driver_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền kết thúc hành trình này")

    if session.end_time is None:
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        session.end_time = now_utc
        if session.start_time:
            delta = now_utc - session.start_time
            session.total_minutes = max(1.0, round(delta.total_seconds() / 60.0, 1))

        # Ghi sự kiện TRIP_ENDED
        trip_end_event = TripEvent(
            session_id=session.id,
            event_type="TRIP_ENDED",
            timestamp=now_utc,
            video_offset_ms=int((now_utc - session.start_time).total_seconds() * 1000) if session.start_time else 0,
            sequence_num=999,
            severity="INFO",
            driver_id=current_user.id
        )
        db.add(trip_end_event)
        await db.commit()
        await db.refresh(session)

    return {
        "message": "Hành trình đã kết thúc an toàn",
        "session_id": session.id,
        "total_minutes": session.total_minutes,
        "end_time": session.end_time.isoformat()
    }

@router.get("/")
async def get_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Driver = Depends(require_permission("journey.view")),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách phiên lái xe dựa trên Data Scope của người dùng"""
    query = select(DrivingSession).order_by(DrivingSession.start_time.desc(), DrivingSession.id.desc())
    query = apply_data_scope(query, DrivingSession, current_user, db)
    
    clamped_limit = max(1, min(limit, 100))
    result = await db.execute(query.offset(skip).limit(clamped_limit))
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "organization_id": s.organization_id,
            "driver_id": s.driver_id,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "total_minutes": s.total_minutes
        }
        for s in sessions
    ]

@router.get("/{session_id}")
async def get_session_detail(
    session_id: int,
    current_user: Driver = Depends(require_permission("journey.view")),
    db: AsyncSession = Depends(get_db)
):
    """Chi tiết phiên lái xe với IDOR Protection"""
    company_id = current_user.organization_id or 1
    session = (await db.execute(
        select(DrivingSession).where(
            and_(
                DrivingSession.id == session_id,
                DrivingSession.organization_id == company_id
            )
        )
    )).scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hành trình lái xe")

    # IDOR check
    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=session.organization_id,
        resource_driver_id=session.driver_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập hành trình này")

    return {
        "id": session.id,
        "organization_id": session.organization_id,
        "driver_id": session.driver_id,
        "start_time": session.start_time.isoformat() if session.start_time else None,
        "end_time": session.end_time.isoformat() if session.end_time else None,
        "total_minutes": session.total_minutes
    }

@router.get("/{session_id}/events")
async def get_session_semantic_events(
    session_id: int,
    current_user: Driver = Depends(require_permission("journey.view")),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách các sự kiện an toàn ngữ nghĩa (Semantic Events) của chuyến đi"""
    company_id = current_user.organization_id or 1
    session = (await db.execute(
        select(DrivingSession).where(
            and_(
                DrivingSession.id == session_id,
                DrivingSession.organization_id == company_id
            )
        )
    )).scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hành trình")

    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=session.organization_id,
        resource_driver_id=session.driver_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem sự kiện của hành trình này")

    events_query = select(TripEvent).where(
        TripEvent.session_id == session_id
    ).order_by(TripEvent.timestamp.asc(), TripEvent.sequence_num.asc())

    events = (await db.execute(events_query)).scalars().all()
    return [
        {
            "id": e.id,
            "session_id": e.session_id,
            "event_type": e.event_type,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "video_offset_ms": e.video_offset_ms,
            "sequence_num": e.sequence_num,
            "severity": e.severity,
            "latitude": e.latitude,
            "longitude": e.longitude,
            "metadata": e.metadata_json,
            "violation_id": e.violation_id
        }
        for e in events
    ]

@router.get("/{session_id}/replay")
async def get_session_replay_data(
    session_id: int,
    current_user: Driver = Depends(require_permission("journey.view")),
    db: AsyncSession = Depends(get_db)
):
    """Lấy dữ liệu mô phỏng lại chuyến đi (Trip Replay) kèm Safety Timeline và IDOR Protection"""
    company_id = current_user.organization_id or 1
    session = (await db.execute(
        select(DrivingSession).options(selectinload(DrivingSession.events)).where(
            and_(
                DrivingSession.id == session_id,
                DrivingSession.organization_id == company_id
            )
        )
    )).scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên hành trình lái xe")

    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=session.organization_id,
        resource_driver_id=session.driver_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem lại dữ liệu chuyến đi này")

    # Semantic events
    events_list = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "video_offset_ms": e.video_offset_ms,
            "sequence_num": e.sequence_num,
            "severity": e.severity,
            "latitude": e.latitude,
            "longitude": e.longitude,
            "metadata": e.metadata_json,
            "violation_id": e.violation_id
        }
        for e in (session.events or [])
    ]

    # Downsampled Telemetry Path
    telemetry_path = [
        {"video_offset_ms": 0, "speed_kmh": 45.0, "safe_distance_m": 22.0, "lat": 21.0285, "lng": 105.8542, "status": "normal"},
        {"video_offset_ms": 60000, "speed_kmh": 58.5, "safe_distance_m": 18.5, "lat": 21.0310, "lng": 105.8580, "status": "normal"},
        {"video_offset_ms": 120000, "speed_kmh": 64.0, "safe_distance_m": 12.0, "lat": 21.0345, "lng": 105.8620, "status": "warning_distance"},
        {"video_offset_ms": 180000, "speed_kmh": 52.0, "safe_distance_m": 20.0, "lat": 21.0380, "lng": 105.8655, "status": "normal"},
    ]

    return {
        "session_id": session.id,
        "driver_id": session.driver_id,
        "start_time": session.start_time.isoformat() if session.start_time else None,
        "end_time": session.end_time.isoformat() if session.end_time else None,
        "total_minutes": session.total_minutes,
        "safety_score": 94,
        "events": events_list,
        "telemetry_points": telemetry_path
    }

@router.post("/reset-rest")
async def reset_rest(
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bắt đầu một phiên lái xe mới (đánh dấu tài xế đã nghỉ ngơi)"""
    sessions = await session_crud.get_sessions_by_driver(db, current_user.id, limit=1)
    if sessions and len(sessions) > 0:
        latest = sessions[0]
        if latest.end_time is None:
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            latest.end_time = now_utc
            if latest.start_time:
                delta = latest.end_time - latest.start_time
                latest.total_minutes = delta.total_seconds() / 60.0
            await db.commit()
    
    new_session = await session_crud.create_session(db, current_user.id, current_user.organization_id or 1)
    return {"message": "Nghỉ ngơi thành công, bắt đầu phiên lái xe an toàn mới", "session_id": new_session.id}
