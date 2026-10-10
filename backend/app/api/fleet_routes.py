from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from backend.app.database.session import get_db
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.auth.security import get_password_hash
from backend.app.auth.rbac_service import (
    apply_data_scope,
    normalize_role_code,
    can_access_resource
)
from backend.app.models_db.driver import Driver
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.driving_session import DrivingSession
from backend.app.models_db.violation import Violation
from backend.app.models_db.rbac import Role
from backend.app.crud.audit_crud import log_audit_event

from backend.app.auth.dependencies import require_manager, get_optional_current_user

router = APIRouter()

@router.get("/ai-status")
async def ai_status(user=Depends(get_optional_current_user)):
    from backend.app.core.pipeline_runner import SharedAIModels
    from backend.app.core.ai_benchmark import get_ai_benchmark_summary
    models = SharedAIModels._instance
    benchmark_data = get_ai_benchmark_summary()
    return {
        "models": [
            {"name": "Vehicle Detection (YOLOv8 Nano)", "loaded": bool(models and models.detector)},
            {"name": "Tracking (ByteTrack + Kalman 2D)", "loaded": True},
            {"name": "Speed Estimator (Homography + Kalman)", "loaded": True},
            {"name": "Safe Distance (TT 31/2019/TT-BGTVT)", "loaded": True},
            {"name": "Traffic Sign QCVN 41:2019 (Voting 5-frame)", "loaded": bool(models and models.sign_recognition)},
            {"name": "Plate OCR (Deskew + Regex VN)", "loaded": bool(models and models.plate_reader)},
            {"name": "DMS Drowsiness (Auto-Calibration 10s)", "loaded": True},
            {"name": "Seatbelt Checker", "loaded": True},
            {"name": "Driving Timer (4h Fatigue limit)", "loaded": True},
            {"name": "Decision Engine (Priority Arbiter)", "loaded": True},
            {"name": "Vietnamese Voice Generator", "loaded": True},
            {"name": "Dedicated Helmet Detector", "loaded": bool(models and models.helmet_checker and models.helmet_checker.enabled)},
        ], 
        "fps": benchmark_data.get("fps_achieved"), 
        "latency_ms": benchmark_data.get("overall_latency_ms"),
        "benchmark": benchmark_data
    }

class DriverCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "FLEET_DRIVER"
    branch_id: Optional[int] = None

class VehicleCreate(BaseModel):
    license_plate: str
    vehicle_type: str = "car"
    fleet_id: Optional[int] = None
    branch_id: Optional[int] = None

class VehicleUpdate(BaseModel):
    vehicle_type: Optional[str] = None
    status: Optional[str] = None
    fleet_id: Optional[int] = None
    branch_id: Optional[int] = None

@router.get("/drivers")
async def get_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Driver = Depends(require_permission("driver.view")),
    db: AsyncSession = Depends(get_db)
):
    query = select(Driver).order_by(Driver.id.asc())
    query = apply_data_scope(query, Driver, current_user, db)
    
    result = await db.execute(query.offset(skip).limit(limit))
    drivers_list = result.scalars().all()
    return [
        {
            "id": d.id,
            "email": d.email,
            "full_name": d.full_name or "Tài Xế Doanh Nghiệp",
            "role": d.role,
            "is_active": d.is_active,
            "branch_id": d.branch_id,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "total_trips": 0
        }
        for d in drivers_list
    ]

@router.get("/drivers/{driver_id}")
async def get_driver_detail(
    driver_id: int,
    current_user: Driver = Depends(require_permission("driver.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    driver = (await db.execute(select(Driver).where(and_(Driver.id == driver_id, Driver.organization_id == company_id)))).scalars().first()
    if not driver:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài xế")
    
    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=driver.organization_id,
        resource_driver_id=driver.id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập thông tin tài xế này")

    return {
        "id": driver.id,
        "email": driver.email,
        "full_name": driver.full_name,
        "role": driver.role,
        "is_active": driver.is_active,
        "branch_id": driver.branch_id,
        "created_at": driver.created_at.isoformat() if driver.created_at else None
    }

@router.patch("/drivers/{driver_id}/disable")
async def disable_driver_account(
    driver_id: int,
    disable: bool = True,
    current_user: Driver = Depends(require_permission("driver.disable")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    driver = (await db.execute(select(Driver).where(and_(Driver.id == driver_id, Driver.organization_id == company_id)))).scalars().first()
    if not driver:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản người dùng")

    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=driver.organization_id,
        resource_driver_id=driver.id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền quản lý tài khoản này")

    driver.is_active = not disable
    await db.commit()

    # Ghi Audit Log
    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="USER_DISABLE" if disable else "USER_ENABLE",
        resource_type="driver",
        resource_id=driver.id,
        details={"target_email": driver.email, "is_active": driver.is_active}
    )

    return {"message": f"Tài khoản {driver.email} đã được {'vô hiệu hóa' if disable else 'kích hoạt lại'}", "is_active": driver.is_active}

@router.post("/drivers")
async def create_driver(
    payload: DriverCreate,
    current_user: Driver = Depends(require_permission("driver.create")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    exist = (await db.execute(select(Driver).where(Driver.email == payload.email.strip().lower()))).scalars().first()
    if exist:
        raise HTTPException(status_code=400, detail="Email này đã được sử dụng")
    
    normalized_role = normalize_role_code(payload.role)
    role_obj = (await db.execute(select(Role).where(Role.code == normalized_role))).scalars().first()

    new_d = Driver(
        email=payload.email.strip().lower(),
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=normalized_role,
        role_id=role_obj.id if role_obj else None,
        organization_id=company_id,
        branch_id=payload.branch_id,
        is_active=True
    )
    db.add(new_d)
    await db.commit()
    await db.refresh(new_d)

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="USER_CREATE",
        resource_type="driver",
        resource_id=new_d.id,
        details={"email": new_d.email, "role": new_d.role}
    )

    return {
        "id": new_d.id,
        "email": new_d.email,
        "full_name": new_d.full_name,
        "role": new_d.role
    }

@router.get("/vehicles")
async def get_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Driver = Depends(require_permission("vehicle.view")),
    db: AsyncSession = Depends(get_db)
):
    query = select(Vehicle).order_by(Vehicle.id.asc())
    query = apply_data_scope(query, Vehicle, current_user, db)
    
    result = await db.execute(query.offset(skip).limit(limit))
    vehicles_list = result.scalars().all()
    return [
        {
            "id": v.id,
            "license_plate": v.license_plate,
            "vehicle_type": v.vehicle_type or "car",
            "fleet_id": v.fleet_id,
            "branch_id": v.branch_id,
            "status": v.status
        }
        for v in vehicles_list
    ]

@router.get("/vehicles/{vehicle_id}")
async def get_vehicle_detail(
    vehicle_id: int,
    current_user: Driver = Depends(require_permission("vehicle.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    vehicle = (await db.execute(select(Vehicle).where(and_(Vehicle.id == vehicle_id, Vehicle.organization_id == company_id)))).scalars().first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy phương tiện")

    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=vehicle.organization_id,
        resource_fleet_id=vehicle.fleet_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập phương tiện này")

    return {
        "id": vehicle.id,
        "license_plate": vehicle.license_plate,
        "vehicle_type": vehicle.vehicle_type,
        "fleet_id": vehicle.fleet_id,
        "branch_id": vehicle.branch_id,
        "status": vehicle.status
    }

@router.patch("/vehicles/{vehicle_id}")
@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    current_user: Driver = Depends(require_permission("vehicle.update")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    vehicle = (await db.execute(select(Vehicle).where(and_(Vehicle.id == vehicle_id, Vehicle.organization_id == company_id)))).scalars().first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy phương tiện")

    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=vehicle.organization_id,
        resource_fleet_id=vehicle.fleet_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa đổi thông tin phương tiện này")

    if payload.vehicle_type is not None:
        vehicle.vehicle_type = payload.vehicle_type
    if payload.status is not None:
        vehicle.status = payload.status
    if payload.fleet_id is not None:
        vehicle.fleet_id = payload.fleet_id
    if payload.branch_id is not None:
        vehicle.branch_id = payload.branch_id

    await db.commit()
    await db.refresh(vehicle)

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="VEHICLE_UPDATE",
        resource_type="vehicle",
        resource_id=vehicle.id,
        details=payload.model_dump(exclude_unset=True)
    )

    return {"message": "Cập nhật phương tiện thành công", "id": vehicle.id}

@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: int,
    current_user: Driver = Depends(require_permission("vehicle.update")),
    db: AsyncSession = Depends(get_db)
):
    """Xóa hoặc loại bỏ phương tiện khỏi danh mục quản lý đội xe"""
    company_id = current_user.organization_id or 1
    vehicle = (await db.execute(select(Vehicle).where(and_(Vehicle.id == vehicle_id, Vehicle.organization_id == company_id)))).scalars().first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Không tìm thấy phương tiện")

    is_allowed = await can_access_resource(
        user=current_user,
        resource_company_id=vehicle.organization_id,
        resource_fleet_id=vehicle.fleet_id,
        db=db
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Bạn không có quyền quản lý phương tiện này")

    vehicle.status = "deleted"
    await db.commit()

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="VEHICLE_DELETE",
        resource_type="vehicle",
        resource_id=vehicle.id,
        details={"license_plate": vehicle.license_plate}
    )
    return None

@router.post("/vehicles")
async def create_vehicle(
    payload: VehicleCreate,
    current_user: Driver = Depends(require_permission("vehicle.create")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    exist = (await db.execute(select(Vehicle).where(Vehicle.license_plate == payload.license_plate.strip().upper()))).scalars().first()
    if exist:
        raise HTTPException(status_code=400, detail="Biển số xe này đã được đăng ký trong hệ thống")
    
    new_v = Vehicle(
        license_plate=payload.license_plate.strip().upper(),
        vehicle_type=payload.vehicle_type or "car",
        fleet_id=payload.fleet_id,
        branch_id=payload.branch_id,
        status="active",
        organization_id=company_id
    )
    db.add(new_v)
    await db.commit()
    await db.refresh(new_v)

    await log_audit_event(
        db=db,
        company_id=company_id,
        user_id=current_user.id,
        user_email=current_user.email,
        action="VEHICLE_CREATE",
        resource_type="vehicle",
        resource_id=new_v.id,
        details={"license_plate": new_v.license_plate, "type": new_v.vehicle_type}
    )

    return {"id": new_v.id, "license_plate": new_v.license_plate, "vehicle_type": new_v.vehicle_type}

@router.get("/summary")
async def get_summary(
    current_user: Driver = Depends(require_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db)
):
    try:
        driver_query = apply_data_scope(select(func.count(Driver.id)), Driver, current_user, db)
        vehicle_query = apply_data_scope(select(func.count(Vehicle.id)), Vehicle, current_user, db)
        session_stats_query = apply_data_scope(select(func.count(DrivingSession.id), func.coalesce(func.sum(DrivingSession.total_minutes), 0.0)), DrivingSession, current_user, db)
        violation_query = apply_data_scope(select(func.count(Violation.id)), Violation, current_user, db)

        d_cnt = (await db.execute(driver_query)).scalar() or 0
        v_cnt = (await db.execute(vehicle_query)).scalar() or 0
        s_row = (await db.execute(session_stats_query)).first()
        s_cnt = s_row[0] if s_row else 0
        total_mins = s_row[1] if s_row else 0.0
        viol_cnt = (await db.execute(violation_query)).scalar() or 0

        group_query = select(Violation.violation_type, func.count(Violation.id)).group_by(Violation.violation_type)
        group_query = apply_data_scope(group_query, Violation, current_user, db)
        groups = (await db.execute(group_query)).all()
        breakdown = {t: c for t, c in groups}

        return {
            "total_drivers": d_cnt,
            "total_vehicles": v_cnt,
            "total_sessions": s_cnt,
            "total_violations": viol_cnt,
            "total_driving_hours": round(total_mins / 60.0, 1),
            "safety_score": max(50, 100 - min(viol_cnt * 2, 50)),
            "violation_breakdown": breakdown
        }
    except Exception:
        return {
            "total_drivers": 0,
            "total_vehicles": 0,
            "total_sessions": 0,
            "total_violations": 0,
            "total_driving_hours": 0.0,
            "safety_score": 100,
            "violation_breakdown": {}
        }
