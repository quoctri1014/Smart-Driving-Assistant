import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models_db.organization_structure import (
    Branch,
    Fleet,
    FleetDispatcher,
    FleetDriver,
    VehicleAssignment
)
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.driver import Driver
from backend.app.models_db.organization import Organization
from backend.app.utils.datetime_utils import utc_now

# ==========================================
# 1. BRANCH OPERATIONS
# ==========================================

async def get_branches(
    db: AsyncSession,
    company_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Branch]:
    query = select(Branch).where(Branch.company_id == company_id).order_by(Branch.id.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_branch_by_id(db: AsyncSession, branch_id: int, company_id: Optional[int] = None) -> Optional[Branch]:
    query = select(Branch).where(Branch.id == branch_id)
    if company_id is not None:
        query = query.where(Branch.company_id == company_id)
    result = await db.execute(query)
    return result.scalars().first()

async def create_branch(
    db: AsyncSession,
    company_id: int,
    name: str,
    code: Optional[str] = None,
    status_val: str = "active"
) -> Branch:
    new_branch = Branch(
        company_id=company_id,
        name=name.strip(),
        code=code.strip().upper() if code else None,
        status=status_val
    )
    db.add(new_branch)
    await db.commit()
    await db.refresh(new_branch)
    return new_branch

async def update_branch(
    db: AsyncSession,
    branch_id: int,
    company_id: int,
    name: Optional[str] = None,
    code: Optional[str] = None,
    status_val: Optional[str] = None
) -> Branch:
    branch = await get_branch_by_id(db, branch_id, company_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Không tìm thấy chi nhánh")
    if name is not None:
        branch.name = name.strip()
    if code is not None:
        branch.code = code.strip().upper()
    if status_val is not None:
        branch.status = status_val
    await db.commit()
    await db.refresh(branch)
    return branch


# ==========================================
# 2. FLEET OPERATIONS
# ==========================================

async def get_fleets(
    db: AsyncSession,
    company_id: int,
    branch_id: Optional[int] = None,
    allowed_fleet_ids: Optional[List[int]] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Fleet]:
    query = select(Fleet).where(Fleet.company_id == company_id)
    if branch_id is not None:
        query = query.where(Fleet.branch_id == branch_id)
    if allowed_fleet_ids is not None:
        query = query.where(Fleet.id.in_(allowed_fleet_ids))
    query = query.order_by(Fleet.id.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_fleet_by_id(db: AsyncSession, fleet_id: int, company_id: Optional[int] = None) -> Optional[Fleet]:
    query = select(Fleet).where(Fleet.id == fleet_id)
    if company_id is not None:
        query = query.where(Fleet.company_id == company_id)
    result = await db.execute(query)
    return result.scalars().first()

async def create_fleet(
    db: AsyncSession,
    company_id: int,
    name: str,
    branch_id: Optional[int] = None,
    code: Optional[str] = None,
    status_val: str = "active"
) -> Fleet:
    if branch_id is not None:
        branch = await get_branch_by_id(db, branch_id, company_id)
        if not branch:
            raise HTTPException(status_code=400, detail="Chi nhánh chỉ định không tồn tại trong doanh nghiệp")

    new_fleet = Fleet(
        company_id=company_id,
        branch_id=branch_id,
        name=name.strip(),
        code=code.strip().upper() if code else None,
        status=status_val
    )
    db.add(new_fleet)
    await db.commit()
    await db.refresh(new_fleet)
    return new_fleet

async def update_fleet(
    db: AsyncSession,
    fleet_id: int,
    company_id: int,
    name: Optional[str] = None,
    branch_id: Optional[int] = None,
    code: Optional[str] = None,
    status_val: Optional[str] = None
) -> Fleet:
    fleet = await get_fleet_by_id(db, fleet_id, company_id)
    if not fleet:
        raise HTTPException(status_code=404, detail="Không tìm thấy đội xe")
    if branch_id is not None:
        branch = await get_branch_by_id(db, branch_id, company_id)
        if not branch:
            raise HTTPException(status_code=400, detail="Chi nhánh chỉ định không tồn tại trong doanh nghiệp")
        fleet.branch_id = branch_id
    if name is not None:
        fleet.name = name.strip()
    if code is not None:
        fleet.code = code.strip().upper()
    if status_val is not None:
        fleet.status = status_val
    await db.commit()
    await db.refresh(fleet)
    return fleet


# ==========================================
# 3. FLEET DISPATCHER & DRIVER ASSIGNMENTS
# ==========================================

async def get_user_assigned_fleet_ids(db: AsyncSession, user_id: int) -> List[int]:
    """Lấy danh sách ID các đội xe mà Dispatcher được phân công quản lý (active)"""
    query = select(FleetDispatcher.fleet_id).where(
        and_(
            FleetDispatcher.user_id == user_id,
            FleetDispatcher.removed_at.is_(None)
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_driver_fleet_id(db: AsyncSession, driver_id: int) -> Optional[int]:
    """Lấy ID đội xe mà Driver đang trực thuộc (active)"""
    query = select(FleetDriver.fleet_id).where(
        and_(
            FleetDriver.driver_id == driver_id,
            FleetDriver.removed_at.is_(None)
        )
    ).order_by(FleetDriver.assigned_at.desc())
    result = await db.execute(query)
    return result.scalars().first()

async def assign_dispatcher_to_fleet(
    db: AsyncSession,
    fleet_id: int,
    user_id: int,
    company_id: int
) -> FleetDispatcher:
    # 1. Validate Fleet
    fleet = await get_fleet_by_id(db, fleet_id, company_id)
    if not fleet:
        raise HTTPException(status_code=404, detail="Không tìm thấy đội xe trong doanh nghiệp")

    # 2. Validate User & Cross-Company Check
    user = (await db.execute(select(Driver).where(Driver.id == user_id))).scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Người dùng không tồn tại hoặc đã bị vô hiệu hóa")
    if user.organization_id != company_id:
        raise HTTPException(status_code=400, detail="Không thể gán nhân sự thuộc doanh nghiệp khác vào đội xe")

    # 3. Check Duplicate Active Assignment
    exist = (await db.execute(
        select(FleetDispatcher).where(
            and_(
                FleetDispatcher.fleet_id == fleet_id,
                FleetDispatcher.user_id == user_id,
                FleetDispatcher.removed_at.is_(None)
            )
        )
    )).scalars().first()
    if exist:
        return exist

    new_assignment = FleetDispatcher(
        fleet_id=fleet_id,
        user_id=user_id,
        assigned_at=utc_now()
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)
    return new_assignment

async def remove_dispatcher_from_fleet(
    db: AsyncSession,
    fleet_id: int,
    user_id: int,
    company_id: Optional[int] = None
) -> bool:
    if company_id is not None:
        fleet = await get_fleet_by_id(db, fleet_id, company_id)
        if not fleet:
            raise HTTPException(status_code=404, detail="Không tìm thấy đội xe")

    assignment = (await db.execute(
        select(FleetDispatcher).where(
            and_(
                FleetDispatcher.fleet_id == fleet_id,
                FleetDispatcher.user_id == user_id,
                FleetDispatcher.removed_at.is_(None)
            )
        )
    )).scalars().first()
    if not assignment:
        return False
    assignment.removed_at = utc_now()
    await db.commit()
    return True

async def assign_driver_to_fleet(
    db: AsyncSession,
    fleet_id: int,
    driver_id: int,
    company_id: int
) -> FleetDriver:
    # 1. Validate Fleet
    fleet = await get_fleet_by_id(db, fleet_id, company_id)
    if not fleet:
        raise HTTPException(status_code=404, detail="Không tìm thấy đội xe trong doanh nghiệp")

    # 2. Validate Driver & Cross-Company Check
    driver = (await db.execute(select(Driver).where(Driver.id == driver_id))).scalars().first()
    if not driver or not driver.is_active:
        raise HTTPException(status_code=400, detail="Tài xế không tồn tại hoặc đã bị vô hiệu hóa")
    if driver.organization_id != company_id:
        raise HTTPException(status_code=400, detail="Không thể gán tài xế thuộc doanh nghiệp khác vào đội xe")

    # 3. Check Duplicate Active Assignment
    exist = (await db.execute(
        select(FleetDriver).where(
            and_(
                FleetDriver.fleet_id == fleet_id,
                FleetDriver.driver_id == driver_id,
                FleetDriver.removed_at.is_(None)
            )
        )
    )).scalars().first()
    if exist:
        return exist

    new_assignment = FleetDriver(
        fleet_id=fleet_id,
        driver_id=driver_id,
        assigned_at=utc_now()
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)
    return new_assignment

async def remove_driver_from_fleet(
    db: AsyncSession,
    fleet_id: int,
    driver_id: int,
    company_id: Optional[int] = None
) -> bool:
    if company_id is not None:
        fleet = await get_fleet_by_id(db, fleet_id, company_id)
        if not fleet:
            raise HTTPException(status_code=404, detail="Không tìm thấy đội xe")

    assignment = (await db.execute(
        select(FleetDriver).where(
            and_(
                FleetDriver.fleet_id == fleet_id,
                FleetDriver.driver_id == driver_id,
                FleetDriver.removed_at.is_(None)
            )
        )
    )).scalars().first()
    if not assignment:
        return False
    assignment.removed_at = utc_now()
    await db.commit()
    return True

async def get_fleet_members(
    db: AsyncSession,
    fleet_id: int,
    company_id: int
) -> dict:
    fleet = await get_fleet_by_id(db, fleet_id, company_id)
    if not fleet:
        raise HTTPException(status_code=404, detail="Không tìm thấy đội xe")

    dispatchers = (await db.execute(
        select(Driver).join(FleetDispatcher, FleetDispatcher.user_id == Driver.id).where(
            and_(
                FleetDispatcher.fleet_id == fleet_id,
                FleetDispatcher.removed_at.is_(None)
            )
        )
    )).scalars().all()

    drivers = (await db.execute(
        select(Driver).join(FleetDriver, FleetDriver.driver_id == Driver.id).where(
            and_(
                FleetDriver.fleet_id == fleet_id,
                FleetDriver.removed_at.is_(None)
            )
        )
    )).scalars().all()

    vehicles = (await db.execute(
        select(Vehicle).where(Vehicle.fleet_id == fleet_id)
    )).scalars().all()

    return {
        "fleet_id": fleet.id,
        "fleet_name": fleet.name,
        "dispatchers": [{"id": u.id, "email": u.email, "full_name": u.full_name} for u in dispatchers],
        "drivers": [{"id": d.id, "email": d.email, "full_name": d.full_name} for d in drivers],
        "vehicles": [{"id": v.id, "license_plate": v.license_plate, "vehicle_type": v.vehicle_type, "status": v.status} for v in vehicles]
    }


# ==========================================
# 4. VEHICLE ASSIGNMENTS & HISTORICAL RESOLUTION
# ==========================================

async def assign_vehicle_to_driver(
    db: AsyncSession,
    company_id: int,
    vehicle_id: int,
    driver_id: int,
    assigned_by: Optional[int] = None,
    notes: Optional[str] = None
) -> VehicleAssignment:
    """
    Bàn giao phương tiện cho tài xế với các validation nghiêm ngặt:
    - 1 vehicle chỉ có 1 active driver assignment tại một thời điểm
    - 1 driver chỉ có 1 active vehicle assignment tại một thời điểm
    - Vehicle và Driver phải cùng thuộc company_id và đang active
    """
    # 1. Validate Vehicle
    vehicle = (await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))).scalars().first()
    if not vehicle or vehicle.status != "active":
        raise HTTPException(status_code=400, detail="Phương tiện không tồn tại hoặc đang trong trạng thái bảo dưỡng/ngưng hoạt động")
    if vehicle.organization_id != company_id:
        raise HTTPException(status_code=400, detail="Không thể bàn giao phương tiện thuộc doanh nghiệp khác")

    # 2. Validate Driver
    driver = (await db.execute(select(Driver).where(Driver.id == driver_id))).scalars().first()
    if not driver or not driver.is_active:
        raise HTTPException(status_code=400, detail="Tài xế không tồn tại hoặc tài khoản đã bị khóa")
    if driver.organization_id != company_id:
        raise HTTPException(status_code=400, detail="Không thể gán tài xế thuộc doanh nghiệp khác")

    now = utc_now()

    # 3. Check & Auto-end previous active assignments for this vehicle
    active_veh_assignment = (await db.execute(
        select(VehicleAssignment).where(
            and_(
                VehicleAssignment.vehicle_id == vehicle_id,
                VehicleAssignment.status == "active"
            )
        )
    )).scalars().first()
    if active_veh_assignment:
        active_veh_assignment.status = "ended"
        active_veh_assignment.assigned_to = now

    # 4. Check & Auto-end previous active assignments for this driver
    active_driver_assignment = (await db.execute(
        select(VehicleAssignment).where(
            and_(
                VehicleAssignment.driver_id == driver_id,
                VehicleAssignment.status == "active"
            )
        )
    )).scalars().first()
    if active_driver_assignment and active_driver_assignment.id != getattr(active_veh_assignment, "id", None):
        active_driver_assignment.status = "ended"
        active_driver_assignment.assigned_to = now

    # 5. Create new Vehicle Assignment Record
    new_assignment = VehicleAssignment(
        company_id=company_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        assigned_from=now,
        assigned_to=None,
        assigned_by=assigned_by,
        status="active",
        notes=notes
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)
    return new_assignment

async def end_vehicle_assignment(
    db: AsyncSession,
    assignment_id: int,
    company_id: int,
    notes: Optional[str] = None
) -> VehicleAssignment:
    assignment = (await db.execute(
        select(VehicleAssignment).where(
            and_(
                VehicleAssignment.id == assignment_id,
                VehicleAssignment.company_id == company_id
            )
        )
    )).scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi bàn giao phương tiện")
    if assignment.status != "active":
        return assignment
    
    assignment.status = "ended"
    assignment.assigned_to = utc_now()
    if notes:
        assignment.notes = f"{assignment.notes or ''}\n{notes}".strip()
    await db.commit()
    await db.refresh(assignment)
    return assignment

async def get_driver_for_vehicle_at_time(
    db: AsyncSession,
    vehicle_id: int,
    timestamp: datetime.datetime
) -> Optional[int]:
    """
    Historical Resolution:
    Xác định chính xác tài xế nào đang điều khiển xe tại thời điểm timestamp xảy ra sự kiện
    """
    query = select(VehicleAssignment.driver_id).where(
        and_(
            VehicleAssignment.vehicle_id == vehicle_id,
            VehicleAssignment.assigned_from <= timestamp,
            or_(
                VehicleAssignment.assigned_to.is_(None),
                VehicleAssignment.assigned_to >= timestamp
            )
        )
    ).order_by(VehicleAssignment.assigned_from.desc())
    result = await db.execute(query)
    return result.scalars().first()

async def get_current_vehicle_for_driver(
    db: AsyncSession,
    driver_id: int
) -> Optional[Vehicle]:
    """Lấy phương tiện mà tài xế đang được bàn giao (active)"""
    query = select(Vehicle).join(
        VehicleAssignment, VehicleAssignment.vehicle_id == Vehicle.id
    ).where(
        and_(
            VehicleAssignment.driver_id == driver_id,
            VehicleAssignment.status == "active"
        )
    )
    result = await db.execute(query)
    return result.scalars().first()

async def get_vehicle_assignments(
    db: AsyncSession,
    company_id: int,
    vehicle_id: Optional[int] = None,
    driver_id: Optional[int] = None,
    status_val: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[VehicleAssignment]:
    query = select(VehicleAssignment).where(VehicleAssignment.company_id == company_id)
    if vehicle_id is not None:
        query = query.where(VehicleAssignment.vehicle_id == vehicle_id)
    if driver_id is not None:
        query = query.where(VehicleAssignment.driver_id == driver_id)
    if status_val is not None:
        query = query.where(VehicleAssignment.status == status_val)
    query = query.order_by(VehicleAssignment.assigned_from.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
