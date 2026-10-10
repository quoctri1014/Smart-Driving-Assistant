from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
import datetime

from backend.app.database.session import get_db
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.auth.rbac_service import (
    get_data_scope,
    get_dispatcher_fleet_ids,
    normalize_role_code
)
from backend.app.auth.scopes import DataScope
from backend.app.models_db.driver import Driver
from backend.app.crud import organization_crud

router = APIRouter()

# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class BranchCreate(BaseModel):
    name: str
    code: Optional[str] = None
    status: str = "active"

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    status: Optional[str] = None

class FleetCreate(BaseModel):
    name: str
    branch_id: Optional[int] = None
    code: Optional[str] = None
    status: str = "active"

class FleetUpdate(BaseModel):
    name: Optional[str] = None
    branch_id: Optional[int] = None
    code: Optional[str] = None
    status: Optional[str] = None

class DispatcherAssignPayload(BaseModel):
    user_id: int

class DriverAssignPayload(BaseModel):
    driver_id: int

class VehicleAssignPayload(BaseModel):
    vehicle_id: int
    driver_id: int
    notes: Optional[str] = None

class AssignmentEndPayload(BaseModel):
    notes: Optional[str] = None


# ==========================================
# 1. BRANCH ROUTES
# ==========================================

@router.get("/branches")
async def list_branches(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Driver = Depends(require_permission("fleet.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    branches = await organization_crud.get_branches(db, company_id=company_id, skip=skip, limit=limit)
    return [
        {
            "id": b.id,
            "company_id": b.company_id,
            "name": b.name,
            "code": b.code,
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None
        }
        for b in branches
    ]

@router.post("/branches", status_code=status.HTTP_201_CREATED)
async def create_branch(
    payload: BranchCreate,
    current_user: Driver = Depends(require_permission("fleet.create")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    branch = await organization_crud.create_branch(
        db, company_id=company_id, name=payload.name, code=payload.code, status_val=payload.status
    )
    return {
        "id": branch.id,
        "company_id": branch.company_id,
        "name": branch.name,
        "code": branch.code,
        "status": branch.status,
        "created_at": branch.created_at.isoformat()
    }

@router.get("/branches/{branch_id}")
async def get_branch(
    branch_id: int,
    current_user: Driver = Depends(require_permission("fleet.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    branch = await organization_crud.get_branch_by_id(db, branch_id=branch_id, company_id=company_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Không tìm thấy chi nhánh")
    return {
        "id": branch.id,
        "company_id": branch.company_id,
        "name": branch.name,
        "code": branch.code,
        "status": branch.status,
        "created_at": branch.created_at.isoformat()
    }

@router.patch("/branches/{branch_id}")
async def update_branch(
    branch_id: int,
    payload: BranchUpdate,
    current_user: Driver = Depends(require_permission("fleet.update")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    branch = await organization_crud.update_branch(
        db, branch_id=branch_id, company_id=company_id,
        name=payload.name, code=payload.code, status_val=payload.status
    )
    return {
        "id": branch.id,
        "company_id": branch.company_id,
        "name": branch.name,
        "code": branch.code,
        "status": branch.status
    }


# ==========================================
# 2. FLEET ROUTES
# ==========================================

@router.get("/fleets")
async def list_fleets(
    branch_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Driver = Depends(require_permission("fleet.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    scope = get_data_scope(current_user)

    allowed_fleet_ids = None
    if scope == DataScope.FLEET.value:
        allowed_fleet_ids = await get_dispatcher_fleet_ids(db, current_user.id)

    fleets = await organization_crud.get_fleets(
        db,
        company_id=company_id,
        branch_id=branch_id,
        allowed_fleet_ids=allowed_fleet_ids,
        skip=skip,
        limit=limit
    )
    return [
        {
            "id": f.id,
            "company_id": f.company_id,
            "branch_id": f.branch_id,
            "name": f.name,
            "code": f.code,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None
        }
        for f in fleets
    ]

@router.post("/fleets", status_code=status.HTTP_201_CREATED)
async def create_fleet(
    payload: FleetCreate,
    current_user: Driver = Depends(require_permission("fleet.create")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    fleet = await organization_crud.create_fleet(
        db,
        company_id=company_id,
        branch_id=payload.branch_id,
        name=payload.name,
        code=payload.code,
        status_val=payload.status
    )
    return {
        "id": fleet.id,
        "company_id": fleet.company_id,
        "branch_id": fleet.branch_id,
        "name": fleet.name,
        "code": fleet.code,
        "status": fleet.status,
        "created_at": fleet.created_at.isoformat()
    }

@router.get("/fleets/{fleet_id}")
async def get_fleet(
    fleet_id: int,
    current_user: Driver = Depends(require_permission("fleet.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    scope = get_data_scope(current_user)
    if scope == DataScope.FLEET.value:
        allowed = await get_dispatcher_fleet_ids(db, current_user.id)
        if fleet_id not in allowed:
            raise HTTPException(status_code=403, detail="Bạn không được phân công quản lý đội xe này")

    fleet = await organization_crud.get_fleet_by_id(db, fleet_id=fleet_id, company_id=company_id)
    if not fleet:
        raise HTTPException(status_code=404, detail="Không tìm thấy đội xe")
    return {
        "id": fleet.id,
        "company_id": fleet.company_id,
        "branch_id": fleet.branch_id,
        "name": fleet.name,
        "code": fleet.code,
        "status": fleet.status,
        "created_at": fleet.created_at.isoformat()
    }

@router.patch("/fleets/{fleet_id}")
async def update_fleet(
    fleet_id: int,
    payload: FleetUpdate,
    current_user: Driver = Depends(require_permission("fleet.update")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    fleet = await organization_crud.update_fleet(
        db,
        fleet_id=fleet_id,
        company_id=company_id,
        name=payload.name,
        branch_id=payload.branch_id,
        code=payload.code,
        status_val=payload.status
    )
    return {
        "id": fleet.id,
        "company_id": fleet.company_id,
        "branch_id": fleet.branch_id,
        "name": fleet.name,
        "code": fleet.code,
        "status": fleet.status
    }

@router.get("/fleets/{fleet_id}/members")
async def get_fleet_members(
    fleet_id: int,
    current_user: Driver = Depends(require_permission("fleet.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    return await organization_crud.get_fleet_members(db, fleet_id=fleet_id, company_id=company_id)

@router.post("/fleets/{fleet_id}/dispatchers")
async def assign_dispatcher(
    fleet_id: int,
    payload: DispatcherAssignPayload,
    current_user: Driver = Depends(require_permission("fleet.manage_members")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    assignment = await organization_crud.assign_dispatcher_to_fleet(
        db, fleet_id=fleet_id, user_id=payload.user_id, company_id=company_id
    )
    return {"message": "Gán Điều Độ Viên vào đội xe thành công", "id": assignment.id, "fleet_id": assignment.fleet_id, "user_id": assignment.user_id}

@router.delete("/fleets/{fleet_id}/dispatchers/{user_id}")
async def remove_dispatcher(
    fleet_id: int,
    user_id: int,
    current_user: Driver = Depends(require_permission("fleet.manage_members")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    success = await organization_crud.remove_dispatcher_from_fleet(
        db, fleet_id=fleet_id, user_id=user_id, company_id=company_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi phân công")
    return {"message": "Gỡ bỏ Điều Độ Viên khỏi đội xe thành công"}

@router.post("/fleets/{fleet_id}/drivers")
async def assign_driver(
    fleet_id: int,
    payload: DriverAssignPayload,
    current_user: Driver = Depends(require_permission("fleet.manage_members")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    assignment = await organization_crud.assign_driver_to_fleet(
        db, fleet_id=fleet_id, driver_id=payload.driver_id, company_id=company_id
    )
    return {"message": "Gán Tài Xế vào đội xe thành công", "id": assignment.id, "fleet_id": assignment.fleet_id, "driver_id": assignment.driver_id}

@router.delete("/fleets/{fleet_id}/drivers/{driver_id}")
async def remove_driver(
    fleet_id: int,
    driver_id: int,
    current_user: Driver = Depends(require_permission("fleet.manage_members")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    success = await organization_crud.remove_driver_from_fleet(
        db, fleet_id=fleet_id, driver_id=driver_id, company_id=company_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi phân công tài xế")
    return {"message": "Gỡ bỏ Tài Xế khỏi đội xe thành công"}


# ==========================================
# 3. VEHICLE ASSIGNMENTS & HISTORICAL TRACKING
# ==========================================

@router.get("/vehicle-assignments")
async def list_vehicle_assignments(
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    status_val: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Driver = Depends(require_permission("vehicle.view")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    scope = get_data_scope(current_user)

    # Nếu là tài xế: chỉ xem assignment của chính mình
    if scope == DataScope.SELF.value:
        driver_id = current_user.id

    assignments = await organization_crud.get_vehicle_assignments(
        db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        status_val=status_val,
        skip=skip,
        limit=limit
    )
    return [
        {
            "id": a.id,
            "company_id": a.company_id,
            "vehicle_id": a.vehicle_id,
            "driver_id": a.driver_id,
            "driver_name": a.driver.full_name if a.driver else None,
            "license_plate": a.vehicle.license_plate if a.vehicle else None,
            "assigned_from": a.assigned_from.isoformat() if a.assigned_from else None,
            "assigned_to": a.assigned_to.isoformat() if a.assigned_to else None,
            "status": a.status,
            "notes": a.notes
        }
        for a in assignments
    ]

@router.post("/vehicle-assignments", status_code=status.HTTP_201_CREATED)
async def create_vehicle_assignment(
    payload: VehicleAssignPayload,
    current_user: Driver = Depends(require_permission("vehicle.assign_driver")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    assignment = await organization_crud.assign_vehicle_to_driver(
        db,
        company_id=company_id,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        assigned_by=current_user.id,
        notes=payload.notes
    )
    return {
        "id": assignment.id,
        "company_id": assignment.company_id,
        "vehicle_id": assignment.vehicle_id,
        "driver_id": assignment.driver_id,
        "assigned_from": assignment.assigned_from.isoformat(),
        "status": assignment.status,
        "message": "Bàn giao phương tiện cho tài xế thành công"
    }

@router.patch("/vehicle-assignments/{assignment_id}/end")
async def end_assignment(
    assignment_id: int,
    payload: AssignmentEndPayload,
    current_user: Driver = Depends(require_permission("vehicle.assign_driver")),
    db: AsyncSession = Depends(get_db)
):
    company_id = current_user.organization_id or 1
    assignment = await organization_crud.end_vehicle_assignment(
        db,
        assignment_id=assignment_id,
        company_id=company_id,
        notes=payload.notes
    )
    return {
        "id": assignment.id,
        "status": assignment.status,
        "assigned_to": assignment.assigned_to.isoformat() if assignment.assigned_to else None,
        "message": "Kết thúc bàn giao phương tiện thành công"
    }

@router.get("/vehicle-assignments/current")
async def get_my_current_assignment(
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lấy thông tin xe mà tài xế hiện đang nhận bàn giao (Active)"""
    vehicle = await organization_crud.get_current_vehicle_for_driver(db, current_user.id)
    if not vehicle:
        return {"assigned": False, "vehicle": None}
    return {
        "assigned": True,
        "vehicle": {
            "id": vehicle.id,
            "license_plate": vehicle.license_plate,
            "vehicle_type": vehicle.vehicle_type,
            "status": vehicle.status
        }
    }


class OrganizationSettingsUpdate(BaseModel):
    name: Optional[str] = None
    subscription_plan: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None

@router.get("/organizations/settings")
async def get_organization_settings(
    current_user: Driver = Depends(require_permission("fleet.view")),
    db: AsyncSession = Depends(get_db)
):
    """Lấy thông tin cấu hình của doanh nghiệp vận tải"""
    from sqlalchemy import select
    from backend.app.models_db.organization import Organization
    company_id = current_user.organization_id or 1
    org = (await db.execute(select(Organization).where(Organization.id == company_id))).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin doanh nghiệp")

    return {
        "id": org.id,
        "name": org.name,
        "subscription_plan": "enterprise",
        "max_vehicles": 50,
        "contact_email": getattr(current_user, "email", "contact@vinafleet.com"),
        "contact_phone": "1900-6868",
        "created_at": org.created_at.isoformat() if org.created_at else None
    }

@router.put("/organizations/settings")
async def update_organization_settings(
    payload: OrganizationSettingsUpdate,
    current_user: Driver = Depends(require_permission("fleet.create")),
    db: AsyncSession = Depends(get_db)
):
    """Cập nhật thông tin công ty và cấu hình gói dịch vụ"""
    from sqlalchemy import select
    from backend.app.models_db.organization import Organization
    company_id = current_user.organization_id or 1
    org = (await db.execute(select(Organization).where(Organization.id == company_id))).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin doanh nghiệp")

    if payload.name:
        org.name = payload.name
        await db.commit()
        await db.refresh(org)

    return {
        "message": "Cập nhật thông tin doanh nghiệp thành công",
        "id": org.id,
        "name": org.name,
        "subscription_plan": payload.subscription_plan or "enterprise"
    }

