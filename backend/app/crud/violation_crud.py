import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
from fastapi import HTTPException, status

from backend.app.models_db.violation import Violation
from backend.app.models_db.violation_review import ViolationReview
from backend.app.services.state_machine import validate_and_compute_transition

async def create_violation(
    db: AsyncSession, 
    violation_type: str, 
    severity: str = "WARNING", 
    confidence: Optional[float] = None,
    source_module: Optional[str] = None,
    speed_kph: Optional[float] = None,
    speed_limit_kph: Optional[float] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_name: Optional[str] = None,
    image_path: Optional[str] = None,
    vehicle_id: Optional[int] = None,
    session_id: Optional[int] = None,
    organization_id: Optional[int] = 1,
    driver_id: Optional[int] = None,
    fleet_id: Optional[int] = None,
) -> Violation:
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    db_violation = Violation(
        organization_id=organization_id,
        fleet_id=fleet_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        session_id=session_id,
        violation_type=violation_type,
        severity=severity.upper(),
        review_status="PENDING_REVIEW",
        resolution_status="OPEN",
        status="PENDING_REVIEW",
        confidence=confidence,
        source_module=source_module,
        speed_kph=speed_kph,
        speed_limit_kph=speed_limit_kph,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        image_path=image_path,
        detected_at=now,
        timestamp=now,
        version=1
    )
    db.add(db_violation)
    await db.commit()
    await db.refresh(db_violation)
    return db_violation

async def get_violations(
    db: AsyncSession,
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    driver_id: Optional[int] = None,
    fleet_ids: Optional[List[int]] = None,
    violation_type: Optional[str] = None,
    review_status: Optional[str] = None,
    resolution_status: Optional[str] = None,
    severity: Optional[str] = None,
    min_confidence: Optional[float] = None,
    search: Optional[str] = None
) -> List[Violation]:
    query = select(Violation).where(Violation.organization_id == company_id)
    
    if driver_id is not None:
        query = query.where(Violation.driver_id == driver_id)
    elif fleet_ids is not None:
        query = query.where(Violation.fleet_id.in_(fleet_ids))
        
    if violation_type:
        query = query.where(Violation.violation_type.ilike(f"%{violation_type}%"))
    if review_status:
        query = query.where(Violation.review_status == review_status.upper())
    if resolution_status:
        query = query.where(Violation.resolution_status == resolution_status.upper())
    if severity:
        query = query.where(Violation.severity == severity.upper())
    if min_confidence is not None:
        query = query.where(Violation.confidence >= min_confidence)
    if search:
        query = query.where(
            or_(
                Violation.violation_type.ilike(f"%{search}%"),
                Violation.location_name.ilike(f"%{search}%")
            )
        )
        
    clamped_limit = max(1, min(limit, 100))
    query = query.order_by(Violation.detected_at.desc(), Violation.id.desc()).offset(skip).limit(clamped_limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_violation_by_id(
    db: AsyncSession,
    violation_id: int,
    company_id: int
) -> Optional[Violation]:
    """Lấy chi tiết vi phạm kèm quan hệ reviews và kiểm tra IDOR thuộc company_id"""
    query = select(Violation).options(
        selectinload(Violation.reviews).selectinload(ViolationReview.reviewer)
    ).where(
        and_(
            Violation.id == violation_id,
            Violation.organization_id == company_id
        )
    )
    result = await db.execute(query)
    return result.scalars().first()

async def review_violation(
    db: AsyncSession,
    violation_id: int,
    company_id: int,
    reviewer_id: int,
    action: str, # 'CONFIRM', 'FALSE_POSITIVE', 'NEED_EVIDENCE', 'RESOLVE', 'REOPEN'
    note: str,
    expected_version: Optional[int] = None
) -> Violation:
    """
    Thẩm định vi phạm với:
    1. Central State Machine Transition Validation.
    2. Atomic Optimistic Locking concurrency (HTTP 409 khi conflict).
    3. Mandatory note validation (>= 5 ký tự).
    4. Atomic write cho cả Violation và ViolationReview log.
    """
    violation = await get_violation_by_id(db, violation_id, company_id)
    if not violation:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự cố vi phạm")
    
    # 1. Concurrency Version Check
    current_ver = violation.version
    if expected_version is not None and current_ver != expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sự cố đã được thẩm định/cập nhật bởi chuyên viên khác (Phiên bản trên máy chủ: {current_ver}, phiên bản gửi lên: {expected_version}). Vui lòng tải lại trang."
        )

    old_review_status = violation.review_status
    old_resolution_status = violation.resolution_status

    # 2. Central State Machine Validation & State Computation
    new_review_status, new_resolution_status = validate_and_compute_transition(
        current_review_status=old_review_status,
        current_resolution_status=old_resolution_status,
        action=action,
        note=note
    )

    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    # 3. Cập nhật Violation
    violation.review_status = new_review_status
    violation.resolution_status = new_resolution_status
    violation.status = new_review_status
    violation.reviewed_by = reviewer_id
    violation.review_notes = note.strip()
    violation.reviewed_at = now
    if new_resolution_status == "RESOLVED":
        violation.resolved_at = now
    violation.version = current_ver + 1
    violation.updated_at = now

    # 4. Tạo bản ghi lịch sử Review
    review_entry = ViolationReview(
        violation_id=violation.id,
        reviewer_id=reviewer_id,
        action=action.upper().strip(),
        old_review_status=old_review_status,
        new_review_status=new_review_status,
        old_resolution_status=old_resolution_status,
        new_resolution_status=new_resolution_status,
        note=note.strip(),
        created_at=now
    )
    db.add(review_entry)
    
    # 5. Atomic commit
    await db.commit()
    await db.refresh(violation)
    return violation
