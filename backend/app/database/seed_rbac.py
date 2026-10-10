"""
Database Seed & Migration Script for RBAC, Organization & Fleet Structure
Khởi tạo và đồng bộ Permissions, Roles, Default Organization, Branch, Fleet, Vehicles và Users
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.session import engine, AsyncSessionLocal
from backend.app.database.base import Base
from backend.app.models_db.rbac import Role, Permission
from backend.app.models_db.organization import Organization
from backend.app.models_db.organization_structure import (
    Branch,
    Fleet,
    FleetDispatcher,
    FleetDriver,
    VehicleAssignment
)
from backend.app.models_db.driver import Driver
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.driving_session import DrivingSession
from backend.app.models_db.violation import Violation
from backend.app.models_db.violation_review import ViolationReview
from backend.app.models_db.trip_event import TripEvent
from backend.app.models_db.device_health import DeviceHealth, DeviceHeartbeat
from backend.app.models_db.audit_log import AuditLog
from backend.app.models_db.ai_config import AIConfig
from backend.app.models_db.notification import Notification
from backend.app.auth.security import get_password_hash
from backend.app.auth.permissions_registry import ALL_PERMISSIONS, DEFAULT_ROLE_DEFINITIONS
from backend.app.auth.rbac_service import normalize_role_code

logger = logging.getLogger(__name__)

async def seed_rbac_data(db: AsyncSession):
    """Đồng bộ toàn bộ Permissions, Roles, Organization, Branches, Fleets vào Database"""
    logger.info("Syncing RBAC, Organization, and Fleet structure...")

    # 1. Đảm bảo Default Organization
    org_res = await db.execute(select(Organization).limit(1))
    default_org = org_res.scalars().first()
    if not default_org:
        default_org = Organization(name="VinaFleet Enterprise")
        db.add(default_org)
        await db.commit()
        await db.refresh(default_org)
        logger.info(f"Created default organization: {default_org.name}")

    # 2. Đảm bảo Default Branches
    branch_res = await db.execute(select(Branch).where(Branch.company_id == default_org.id))
    branches = branch_res.scalars().all()
    if not branches:
        b1 = Branch(company_id=default_org.id, name="Chi Nhánh Miền Bắc", code="HN-HQ", status="active")
        b2 = Branch(company_id=default_org.id, name="Chi Nhánh Miền Nam", code="HCM-HQ", status="active")
        db.add_all([b1, b2])
        await db.commit()
        await db.refresh(b1)
        await db.refresh(b2)
        branches = [b1, b2]

    # 3. Đảm bảo Default Fleets
    fleet_res = await db.execute(select(Fleet).where(Fleet.company_id == default_org.id))
    fleets = fleet_res.scalars().all()
    if not fleets:
        f1 = Fleet(company_id=default_org.id, branch_id=branches[0].id, name="Đội Xe Giao Vận Hà Nội", code="FLEET-HN-01", status="active")
        f2 = Fleet(company_id=default_org.id, branch_id=branches[1].id, name="Đội Xe Đường Dài Bắc - Nam", code="FLEET-EXP-02", status="active")
        db.add_all([f1, f2])
        await db.commit()
        await db.refresh(f1)
        await db.refresh(f2)
        fleets = [f1, f2]

    # 4. Đồng bộ Permissions
    existing_perms_res = await db.execute(select(Permission))
    existing_perms_map = {p.code: p for p in existing_perms_res.scalars().all()}

    for p_def in ALL_PERMISSIONS:
        code = p_def["code"]
        if code in existing_perms_map:
            perm = existing_perms_map[code]
            perm.name = p_def["name"]
            perm.module = p_def["module"]
            perm.description = p_def.get("description")
        else:
            new_perm = Permission(
                code=code,
                name=p_def["name"],
                module=p_def["module"],
                description=p_def.get("description")
            )
            db.add(new_perm)
            existing_perms_map[code] = new_perm
    
    await db.commit()

    all_perms_res = await db.execute(select(Permission))
    all_perms_dict = {p.code: p for p in all_perms_res.scalars().all()}

    # 5. Đồng bộ 3 Default Roles
    for role_code, r_def in DEFAULT_ROLE_DEFINITIONS.items():
        role_res = await db.execute(select(Role).where(Role.code == role_code))
        role_obj = role_res.scalars().first()

        target_perms = [all_perms_dict[code] for code in r_def["permissions"] if code in all_perms_dict]

        if not role_obj:
            role_obj = Role(
                code=role_code,
                name=r_def["name"],
                description=r_def.get("description"),
                default_scope=r_def["default_scope"],
                permissions=target_perms
            )
            db.add(role_obj)
            logger.info(f"Created role: {role_code}")
        else:
            role_obj.name = r_def["name"]
            role_obj.description = r_def.get("description")
            role_obj.default_scope = r_def["default_scope"]
            role_obj.permissions = target_perms

    await db.commit()

    # 6. Cập nhật các tài khoản Driver hiện hữu
    roles_res = await db.execute(select(Role))
    roles_map = {r.code: r for r in roles_res.scalars().all()}

    drivers_res = await db.execute(select(Driver))
    drivers_list = drivers_res.scalars().all()

    for d in drivers_list:
        normalized = normalize_role_code(d.role)
        d.role = normalized
        if normalized in roles_map:
            d.role_id = roles_map[normalized].id
        if d.company_id is None and default_org:
            d.company_id = default_org.id

    # 7. Đảm bảo có tài khoản Admin & Dispatcher & Driver mẫu
    if not drivers_list:
        admin_role = roles_map.get("ENTERPRISE_ADMIN")
        disp_role = roles_map.get("FLEET_DISPATCHER")
        drv_role = roles_map.get("FLEET_DRIVER")

        admin_driver = Driver(
            email="admin@vinafleet.com",
            password_hash=get_password_hash("password"),
            full_name="Quản Trị Viên Doanh Nghiệp",
            role="ENTERPRISE_ADMIN",
            role_id=admin_role.id if admin_role else None,
            company_id=default_org.id,
            is_active=True
        )
        disp_driver = Driver(
            email="dispatcher@vinafleet.com",
            password_hash=get_password_hash("password"),
            full_name="Điều Độ Viên Hà Nội",
            role="FLEET_DISPATCHER",
            role_id=disp_role.id if disp_role else None,
            company_id=default_org.id,
            is_active=True
        )
        drv_driver = Driver(
            email="driver1@example.com",
            password_hash=get_password_hash("password"),
            full_name="Nguyễn Văn Lái Xe",
            role="FLEET_DRIVER",
            role_id=drv_role.id if drv_role else None,
            company_id=default_org.id,
            is_active=True
        )
        db.add_all([admin_driver, disp_driver, drv_driver])
        await db.commit()
        await db.refresh(disp_driver)
        await db.refresh(drv_driver)

        # Gán Dispatcher và Driver vào Fleet 1
        db.add(FleetDispatcher(fleet_id=fleets[0].id, user_id=disp_driver.id))
        db.add(FleetDriver(fleet_id=fleets[0].id, driver_id=drv_driver.id))
        await db.commit()

    await db.commit()
    logger.info("RBAC, Organization & Fleet sync completed successfully.")

async def migrate_columns(conn):
    """Tự động thêm các cột mới vào bảng nếu chưa có (Hỗ trợ SQLite / PostgreSQL)"""
    statements = [
        "ALTER TABLE drivers ADD COLUMN company_id INTEGER REFERENCES organizations(id)",
        "ALTER TABLE drivers ADD COLUMN branch_id INTEGER REFERENCES branches(id)",
        "ALTER TABLE vehicles ADD COLUMN company_id INTEGER REFERENCES organizations(id)",
        "ALTER TABLE vehicles ADD COLUMN branch_id INTEGER REFERENCES branches(id)",
        "ALTER TABLE vehicles ADD COLUMN fleet_id INTEGER REFERENCES fleets(id)",
        "ALTER TABLE vehicles ADD COLUMN status VARCHAR(30) DEFAULT 'active'",
        "ALTER TABLE violations ADD COLUMN company_id INTEGER REFERENCES organizations(id)",
        "ALTER TABLE violations ADD COLUMN fleet_id INTEGER REFERENCES fleets(id)",
        "ALTER TABLE violations ADD COLUMN status VARCHAR(50) DEFAULT 'PENDING_REVIEW'",
        "ALTER TABLE violations ADD COLUMN review_status VARCHAR(50) DEFAULT 'PENDING_REVIEW'",
        "ALTER TABLE violations ADD COLUMN resolution_status VARCHAR(50) DEFAULT 'OPEN'",
        "ALTER TABLE violations ADD COLUMN confidence REAL",
        "ALTER TABLE violations ADD COLUMN source_module VARCHAR(100)",
        "ALTER TABLE violations ADD COLUMN model_version VARCHAR(50)",
        "ALTER TABLE violations ADD COLUMN speed_kph REAL",
        "ALTER TABLE violations ADD COLUMN speed_limit_kph REAL",
        "ALTER TABLE violations ADD COLUMN latitude REAL",
        "ALTER TABLE violations ADD COLUMN longitude REAL",
        "ALTER TABLE violations ADD COLUMN location_name VARCHAR(255)",
        "ALTER TABLE violations ADD COLUMN detected_at DATETIME",
        "ALTER TABLE violations ADD COLUMN reviewed_by INTEGER REFERENCES drivers(id)",
        "ALTER TABLE violations ADD COLUMN review_notes TEXT",
        "ALTER TABLE violations ADD COLUMN reviewed_at DATETIME",
        "ALTER TABLE violations ADD COLUMN resolved_at DATETIME",
        "ALTER TABLE violations ADD COLUMN version INTEGER DEFAULT 1",
        "ALTER TABLE violations ADD COLUMN updated_at DATETIME",
        "ALTER TABLE driving_sessions ADD COLUMN company_id INTEGER REFERENCES organizations(id)",
        "ALTER TABLE notifications ADD COLUMN dedup_key VARCHAR(255)",
        "ALTER TABLE notifications ADD COLUMN read_at DATETIME",
        "ALTER TABLE notifications ADD COLUMN acknowledged_at DATETIME",
        "ALTER TABLE notifications ADD COLUMN delivery_status VARCHAR(50) DEFAULT 'SENT'",
        "ALTER TABLE notifications ADD COLUMN retry_count INTEGER DEFAULT 0",
        "ALTER TABLE notifications ADD COLUMN last_attempt_at DATETIME",
        "ALTER TABLE audit_logs ADD COLUMN company_id INTEGER REFERENCES organizations(id)",
        "ALTER TABLE audit_logs ADD COLUMN old_value TEXT",
        "ALTER TABLE audit_logs ADD COLUMN new_value TEXT",
    ]
    for stmt in statements:
        try:
            await conn.exec_driver_sql(stmt)
        except Exception:
            pass # Cột đã tồn tại

    # Đồng bộ dữ liệu cũ nếu trước đó có cột organization_id
    sync_queries = [
        "UPDATE drivers SET company_id = organization_id WHERE company_id IS NULL AND organization_id IS NOT NULL",
        "UPDATE vehicles SET company_id = organization_id WHERE company_id IS NULL AND organization_id IS NOT NULL",
        "UPDATE violations SET company_id = organization_id WHERE company_id IS NULL AND organization_id IS NOT NULL",
        "UPDATE driving_sessions SET company_id = organization_id WHERE company_id IS NULL AND organization_id IS NOT NULL",
        "UPDATE audit_logs SET company_id = organization_id WHERE company_id IS NULL AND organization_id IS NOT NULL",
    ]
    for sq in sync_queries:
        try:
            await conn.exec_driver_sql(sq)
        except Exception:
            pass

async def initialize_database():
    """Hàm khởi tạo bảng và seed dữ liệu RBAC & Organization"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await migrate_columns(conn)
    
    async with AsyncSessionLocal() as session:
        await seed_rbac_data(session)

if __name__ == "__main__":
    import asyncio
    asyncio.run(initialize_database())
