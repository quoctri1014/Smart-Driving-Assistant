import os
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional

from backend.app.database.session import get_db
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.auth.rbac_service import (
    get_data_scope,
    get_dispatcher_fleet_ids,
    can_access_resource
)
from backend.app.auth.scopes import DataScope
from backend.app.models_db.driver import Driver
from backend.app.crud import violation_crud
from backend.app.crud.audit_crud import log_audit_event
from backend.app.services.audit_sanitizer import compute_diff
from backend.app.services.storage_guard import resolve_safe_evidence_path

router = APIRouter()

@router.get("/{violation_id}/image")
async def evidence(violation_id: int, current_user: Driver = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from pathlib import Path
    from backend.app.models_db.violation import Violation
    from backend.app.storage.image_storage import STORAGE_PATH
    query = select(Violation).where(Violation.id == violation_id, Violation.organization_id == current_user.organization_id)
    if current_user.role not in ("admin", "manager"):
        query = query.where(Violation.driver_id == current_user.id)
    record = (await db.execute(query)).scalar_one_or_none()
    if record is None or not record.image_path:
        raise HTTPException(404, "Evidence not found")
    image = Path(record.image_path).resolve()
    if not image.is_relative_to(Path(STORAGE_PATH).resolve()) or not image.is_file():
        raise HTTPException(404, "Evidence not found")
    return FileResponse(image, headers={"Cache-Control": "private, no-store"})

class ViolationReviewPayload(BaseModel):
    action: Optional[str] = None # 'CONFIRM', 'FALSE_POSITIVE', 'NEED_EVIDENCE', 'RESOLVE', 'REOPEN'
    status: Optional[str] = None # Backward compatibility
    note: Optional[str] = None # Bắt buộc giải trình >= 5 ký tự khi FALSE_POSITIVE hoặc RESOLVE
    review_notes: Optional[str] = None # Backward compatibility
    expected_version: Optional[int] = None # Optimistic locking version

@router.get("/")
async def get_violations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    violation_type: Optional[str] = None,
    review_status: Optional[str] = None,
    resolution_status: Optional[str] = None,
    status_val: Optional[str] = None,
    severity: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    search: Optional[str] = None,
    current_user: Driver = Depends(require_permission("violation.view")),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách vi phạm bảo vệ Data Scope:
    - FLEET_DRIVER (SELF): Chỉ xem vi phạm do chính mình tạo ra
    - FLEET_DISPATCHER (FLEET): Chỉ xem vi phạm của các đội xe được phân công
    - ENTERPRISE_ADMIN (COMPANY): Xem toàn bộ vi phạm trong doanh nghiệp
    """
    company_id = current_user.organization_id or 1
    scope = get_data_scope(current_user)

    driver_id_filter = None
    allowed_fleet_ids = None

    if scope == DataScope.SELF.value:
        driver_id_filter = current_user.id
    elif scope == DataScope.FLEET.value:
        allowed_fleet_ids = await get_dispatcher_fleet_ids(db, current_user.id)

    target_review_status = review_status or status_val

    violations = await violation_crud.get_violations(
        db, 
        company_id=company_id,
        skip=skip, 
        limit=limit, 
        driver_id=driver_id_filter,
        fleet_ids=allowed_fleet_ids,
        violation_type=violation_type,
        review_status=target_review_status,
        resolution_status=resolution_status,
        severity=severity,
        min_confidence=min_confidence,
        search=search
    )
    return [
        {
            "id": v.id,
            "organization_id": v.organization_id,
            "fleet_id": v.fleet_id,
            "driver_id": v.driver_id,
            "vehicle_id": v.vehicle_id,
            "session_id": v.session_id,
            "violation_type": v.violation_type,
            "severity": v.severity,
            "review_status": v.review_status,
            "resolution_status": v.resolution_status,
            "status": v.review_status, # Backward compatibility
            "confidence": v.confidence, # Nullable float: 0.0 -> 1.0 (Không fake số)
            "source_module": v.source_module,
            "model_version": v.model_version,
            "speed_kph": v.speed_kph,
            "speed_limit_kph": v.speed_limit_kph,
            "latitude": v.latitude,
            "longitude": v.longitude,
            "location_name": v.location_name,
            "detected_at": v.detected_at.isoformat() if v.detected_at else None,
            "timestamp": v.detected_at.isoformat() if v.detected_at else None,
            "has_evidence": bool(v.image_path),
            "reviewed_by": v.reviewed_by,
            "review_notes": v.review_notes,
            "reviewed_at": v.reviewed_at.isoformat() if v.reviewed_at else None,
            "resolved_at": v.resolved_at.isoformat() if v.resolved_at else None,
            "version": v.version
        }
        for v in violations
    ]

@router.get("/{violation_id}")
async def get_violation_detail(
    violation_id: int,
    current_user: Driver = Depends(require_permission("violation.view")),
    db: AsyncSession = Depends(get_db)
):
    """Chi tiết sự cố vi phạm kèm lịch sử Human-in-the-Loop review và IDOR Protection"""
    company_id = current_user.organization_id or 1
    violation = await violation_crud.get_violation_by_id(db, violation_id=violation_id, company_id=company_id)
    if not violation:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi sự cố vi phạm")

    # IDOR Check — dùng company_id (tên thực trong model Violation)
    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=violation.company_id,
        resource_fleet_id=violation.fleet_id,
        resource_driver_id=violation.driver_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập sự cố vi phạm này")

    # Map reviews history
    reviews_list = []
    if violation.reviews:
        for r in violation.reviews:
            reviews_list.append({
                "id": r.id,
                "reviewer_id": r.reviewer_id,
                "reviewer_name": r.reviewer.full_name if r.reviewer else "Chuyên viên an toàn",
                "action": r.action,
                "old_review_status": r.old_review_status,
                "new_review_status": r.new_review_status,
                "old_resolution_status": r.old_resolution_status,
                "new_resolution_status": r.new_resolution_status,
                "note": r.note,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })

    # Lấy thêm thông tin tài xế, xe để hiển thị trong drawer
    driver_name = None
    driver_phone = None
    vehicle_plate = None
    fleet_name = None
    try:
        from backend.app.models_db.driver import Driver as DriverModel
        from backend.app.models_db.vehicle import Vehicle
        from sqlalchemy import select as sa_select

        if violation.driver_id:
            drv = (await db.execute(sa_select(DriverModel).where(DriverModel.id == violation.driver_id))).scalars().first()
            if drv:
                driver_name = drv.full_name

        if violation.vehicle_id:
            veh = (await db.execute(sa_select(Vehicle).where(Vehicle.id == violation.vehicle_id))).scalars().first()
            if veh:
                vehicle_plate = veh.license_plate
    except Exception:
        pass

    return {
        "id": violation.id,
        "organization_id": violation.company_id,  # Alias để frontend nhất quán
        "fleet_id": violation.fleet_id,
        "driver_id": violation.driver_id,
        "vehicle_id": violation.vehicle_id,
        "session_id": violation.session_id,
        "violation_type": violation.violation_type,
        "severity": violation.severity,
        "review_status": violation.review_status,
        "resolution_status": violation.resolution_status,
        "status": violation.review_status,
        "confidence": violation.confidence,
        "source_module": violation.source_module,
        "model_version": violation.model_version,
        "speed_kph": violation.speed_kph,
        "speed_limit_kph": violation.speed_limit_kph,
        "latitude": violation.latitude,
        "longitude": violation.longitude,
        "location_name": violation.location_name,
        "detected_at": violation.detected_at.isoformat() if violation.detected_at else None,
        "timestamp": violation.detected_at.isoformat() if violation.detected_at else None,
        "has_evidence": bool(violation.image_path),
        "image_path": violation.image_path,  # Trả về để frontend biết có ảnh không
        "reviewed_by": violation.reviewed_by,
        "review_notes": violation.review_notes,
        "reviewed_at": violation.reviewed_at.isoformat() if violation.reviewed_at else None,
        "resolved_at": violation.resolved_at.isoformat() if violation.resolved_at else None,
        "version": violation.version,
        "driver_name": driver_name,
        "driver_phone": driver_phone,
        "vehicle_plate": vehicle_plate,
        "fleet_name": fleet_name,
        "reviews": reviews_list
    }

class ViolationManualCreatePayload(BaseModel):
    vehicle_id: int
    driver_id: Optional[int] = None
    violation_type: str = "speeding"
    severity: str = "WARNING"
    speed_kph: Optional[float] = None
    location_name: Optional[str] = None
    notes: Optional[str] = None

@router.post("/manual", status_code=status.HTTP_201_CREATED)
async def create_manual_violation(
    payload: ViolationManualCreatePayload,
    current_user: Driver = Depends(require_permission("violation.review")),
    db: AsyncSession = Depends(get_db)
):
    """Ghi nhận sự cố vi phạm thủ công từ điều độ viên (Dispatcher)"""
    import datetime
    from backend.app.models_db.violation import Violation
    company_id = current_user.organization_id or 1
    now_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    v = Violation(
        company_id=company_id,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        violation_type=payload.violation_type,
        severity=payload.severity,
        speed_kph=payload.speed_kph,
        location_name=payload.location_name,
        review_notes=payload.notes,
        review_status="APPROVED",
        source_module="dispatcher_manual",
        detected_at=now_utc,
        reviewed_by=current_user.id,
        reviewed_at=now_utc
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="VIOLATION_MANUAL_CREATE",
        resource_type="violation",
        resource_id=v.id,
        details={"type": payload.violation_type, "vehicle_id": payload.vehicle_id}
    )

    return {"message": "Đã ghi nhận sự cố vi phạm thủ công thành công", "id": v.id}

class ViolationRecordPayload(BaseModel):
    violation_type: str
    severity: str = "WARNING"
    confidence: Optional[float] = None
    source_module: Optional[str] = None
    speed_kph: Optional[float] = None
    speed_limit_kph: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    image_base64: Optional[str] = None
    notes: Optional[str] = None
    vehicle_id: Optional[int] = None
    session_id: Optional[int] = None

@router.post("/", status_code=status.HTTP_201_CREATED)
@router.post("/record", status_code=status.HTTP_201_CREATED)
async def record_violation_event(
    payload: ViolationRecordPayload,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ghi nhận sự cố cảnh báo an toàn từ Trợ lý Lái xe Live AI.
    Hỗ trợ trích xuất ảnh snapshot từ camera dạng Base64 và lưu trữ an toàn.
    """
    import base64
    import uuid
    import datetime
    from backend.app.models_db.violation import Violation
    from backend.app.services.storage_guard import STORAGE_ROOT

    company_id = current_user.organization_id or 1
    now_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    image_filename = None
    if payload.image_base64:
        try:
            raw_b64 = payload.image_base64
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            img_bytes = base64.b64decode(raw_b64)
            ts_str = now_utc.strftime("%Y%m%d_%H%M%S")
            u_str = str(uuid.uuid4())[:8]
            safe_fname = f"{payload.violation_type}_{ts_str}_{u_str}.jpg"
            target_file = os.path.join(STORAGE_ROOT, safe_fname)
            with open(target_file, "wb") as f:
                f.write(img_bytes)
            image_filename = safe_fname
        except Exception as e:
            print("Error saving violation image base64:", e)

    v = Violation(
        organization_id=company_id,
        driver_id=current_user.id,
        vehicle_id=payload.vehicle_id,
        session_id=payload.session_id,
        violation_type=payload.violation_type,
        severity=payload.severity.upper() if payload.severity else "WARNING",
        review_status="PENDING_REVIEW",
        resolution_status="OPEN",
        status="PENDING_REVIEW",
        confidence=payload.confidence,
        source_module=payload.source_module,
        speed_kph=payload.speed_kph,
        speed_limit_kph=payload.speed_limit_kph,
        latitude=payload.latitude or 10.762622,
        longitude=payload.longitude or 106.660172,
        location_name=payload.location_name or "Tuyến đường di chuyển cá nhân",
        image_path=image_filename,
        detected_at=now_utc,
        timestamp=now_utc,
        review_notes=payload.notes,
        version=1
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)

    return {
        "message": "Ghi nhận sự cố an toàn thành công",
        "id": v.id,
        "violation_type": v.violation_type,
        "severity": v.severity,
        "review_status": v.review_status,
        "has_evidence": bool(v.image_path)
    }

@router.post("/{violation_id}/review")
@router.put("/{violation_id}/review")
async def review_violation_status(
    violation_id: int,
    payload: ViolationReviewPayload,
    current_user: Driver = Depends(require_permission("violation.review")),
    db: AsyncSession = Depends(get_db)
):
    """Thẩm định sự cố với Optimistic Locking, bắt buộc giải trình, và ghi Audit Diff"""
    company_id = current_user.organization_id or 1
    violation = await violation_crud.get_violation_by_id(db, violation_id=violation_id, company_id=company_id)
    if not violation:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi vi phạm")

    # Check IDOR for Dispatcher
    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=violation.organization_id,
        resource_fleet_id=violation.fleet_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không được phân công xử lý sự cố của đội xe này")

    action_to_perform = payload.action or payload.status or "CONFIRM"
    note_to_save = payload.note or payload.review_notes or "Đã xác nhận sự cố"

    old_snapshot = {
        "review_status": violation.review_status,
        "resolution_status": violation.resolution_status,
        "version": violation.version
    }

    updated_violation = await violation_crud.review_violation(
        db,
        violation_id=violation_id,
        company_id=company_id,
        reviewer_id=current_user.id,
        action=action_to_perform,
        note=note_to_save,
        expected_version=payload.expected_version
    )

    new_snapshot = {
        "review_status": updated_violation.review_status,
        "resolution_status": updated_violation.resolution_status,
        "version": updated_violation.version
    }

    old_diff_str, new_diff_str = compute_diff(old_snapshot, new_snapshot)

    # Nếu Dispatcher xác nhận vi phạm (CONFIRM): Trừ điểm an toàn tài xế, gửi thông báo & broadcast WebSocket
    deduction = 0.0
    new_driver_score = None
    if action_to_perform.upper() == "CONFIRM" and updated_violation.driver_id:
        from backend.app.services.safety_scoring import deduct_driver_safety_score
        from backend.app.models_db.notification import Notification
        from backend.app.websocket.connection_manager import manager

        new_driver_score, deduction = await deduct_driver_safety_score(
            db=db,
            driver_id=updated_violation.driver_id,
            severity=updated_violation.severity or "WARNING",
            violation_type=updated_violation.violation_type or "general",
            journey_id=getattr(updated_violation, "journey_id", None)
        )

        notif = Notification(
            company_id=company_id,
            user_id=updated_violation.driver_id,
            title="Vi phạm an toàn được xác nhận",
            message=f"Sự cố '{updated_violation.violation_type}' ({updated_violation.severity}) đã được xác nhận. Điểm an toàn bị trừ {deduction} điểm (Hiện tại: {new_driver_score} điểm).",
            severity="WARNING",
            resource_type="violation",
            resource_id=violation_id
        )
        db.add(notif)
        await db.commit()

        await manager.broadcast_alert({
            "type": "violation_confirmed",
            "violation_id": violation_id,
            "driver_id": updated_violation.driver_id,
            "deduction": deduction,
            "new_score": new_driver_score
        })

    # Ghi Audit Log tự động (Sanitized & Diff-only)
    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="VIOLATION_REVIEW",
        resource_type="violation",
        resource_id=violation_id,
        details={
            "action": action_to_perform.upper(),
            "note": note_to_save,
            "old_review_status": old_snapshot["review_status"],
            "new_review_status": new_snapshot["review_status"],
            "deduction": deduction,
            "new_driver_score": new_driver_score
        }
    )

    return {
        "id": updated_violation.id,
        "review_status": updated_violation.review_status,
        "resolution_status": updated_violation.resolution_status,
        "status": updated_violation.review_status,
        "reviewed_by": updated_violation.reviewed_by,
        "reviewed_at": updated_violation.reviewed_at.isoformat() if updated_violation.reviewed_at else None,
        "version": updated_violation.version,
        "deduction": deduction,
        "new_driver_score": new_driver_score,
        "message": f"Cập nhật kết quả thẩm định sự cố thành công: {updated_violation.review_status}"
    }

@router.get("/{violation_id}/evidence")
async def get_violation_evidence(
    violation_id: int,
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Xem và tải ảnh bằng chứng vi phạm bảo vệ bởi StorageGuard:
    - Xác thực danh tính & quyền truy cập (evidence.view)
    - IDOR check theo Data Scope
    - Chống Path Traversal (chỉ stream file nằm trong storage root)
    - Serve đúng MIME type
    """
    company_id = current_user.organization_id or 1
    violation = await violation_crud.get_violation_by_id(db, violation_id=violation_id, company_id=company_id)
    if not violation or not violation.image_path:
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp hình ảnh bằng chứng cho vi phạm này")

    # Quyền xem: Người dùng cùng tổ chức
    if violation.organization_id and current_user.organization_id and violation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập bằng chứng này")

    # Path traversal validation
    safe_path, mime_type = resolve_safe_evidence_path(violation.image_path)

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Tệp hình ảnh bằng chứng không tồn tại trên máy chủ lưu trữ")

    return FileResponse(
        safe_path, 
        media_type=mime_type,
        headers={"X-Content-Type-Options": "nosniff"}
    )
