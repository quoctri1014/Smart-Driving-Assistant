"""
Authorization & RBAC Service
Cung cấp các abstraction để kiểm tra quyền và áp dụng Data Scope cho toàn bộ hệ thống TRAFFICGUARD
Hỗ trợ đa tầng: COMPANY -> BRANCH -> FLEET -> VEHICLE -> DRIVER ASSIGNMENT
"""

from typing import Set, List, Optional, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models_db.driver import Driver
from backend.app.models_db.rbac import Role, Permission
from backend.app.models_db.organization_structure import FleetDispatcher
from backend.app.auth.scopes import DataScope
from backend.app.auth.permissions_registry import DEFAULT_ROLE_DEFINITIONS

ROLE_ALIAS_MAPPING = {
    "admin": "ENTERPRISE_ADMIN",
    "enterprise_admin": "ENTERPRISE_ADMIN",
    "ENTERPRISE_ADMIN": "ENTERPRISE_ADMIN",
    "dispatcher": "FLEET_DISPATCHER",
    "manager": "FLEET_DISPATCHER",
    "safety_manager": "FLEET_DISPATCHER",
    "fleet_dispatcher": "FLEET_DISPATCHER",
    "FLEET_DISPATCHER": "FLEET_DISPATCHER",
    "driver": "FLEET_DRIVER",
    "fleet_driver": "FLEET_DRIVER",
    "FLEET_DRIVER": "FLEET_DRIVER",
    "user": "FLEET_DRIVER"
}

def normalize_role_code(raw_role: Optional[str]) -> str:
    if not raw_role:
        return "FLEET_DRIVER"
    return ROLE_ALIAS_MAPPING.get(raw_role.strip(), raw_role.strip().upper())

def get_default_permissions_for_role(role_code: str) -> Set[str]:
    normalized = normalize_role_code(role_code)
    role_def = DEFAULT_ROLE_DEFINITIONS.get(normalized)
    if role_def:
        return set(role_def["permissions"])
    return set()

def get_data_scope(user: Optional[Driver]) -> str:
    """Xác định Data Scope của người dùng"""
    if not user:
        return DataScope.SELF.value
    
    if hasattr(user, "role_rel") and user.role_rel and user.role_rel.default_scope:
        return user.role_rel.default_scope
    
    normalized = normalize_role_code(user.role)
    role_def = DEFAULT_ROLE_DEFINITIONS.get(normalized)
    if role_def:
        return role_def.get("default_scope", DataScope.SELF.value)
    
    return DataScope.SELF.value

async def get_user_permissions(user: Optional[Driver], db: Optional[AsyncSession] = None) -> Set[str]:
    if not user:
        return set()

    if hasattr(user, "role_rel") and user.role_rel and user.role_rel.permissions:
        return {p.code for p in user.role_rel.permissions}

    if db is not None and user.role_id:
        result = await db.execute(
            select(Role).where(Role.id == user.role_id)
        )
        role = result.scalars().first()
        if role and role.permissions:
            return {p.code for p in role.permissions}

    normalized = normalize_role_code(user.role)
    return get_default_permissions_for_role(normalized)

async def has_permission(user: Driver, permission: str, db: Optional[AsyncSession] = None) -> bool:
    if not user or not user.is_active:
        return False
    
    normalized_role = normalize_role_code(user.role)
    if normalized_role == "ENTERPRISE_ADMIN":
        return True

    user_perms = await get_user_permissions(user, db)
    return permission in user_perms

async def has_any_permission(user: Driver, permissions: List[str], db: Optional[AsyncSession] = None) -> bool:
    if not user or not user.is_active:
        return False
    
    normalized_role = normalize_role_code(user.role)
    if normalized_role == "ENTERPRISE_ADMIN":
        return True

    user_perms = await get_user_permissions(user, db)
    return any(p in user_perms for p in permissions)

async def get_dispatcher_fleet_ids(db: AsyncSession, user_id: int) -> List[int]:
    """Lấy danh sách các Fleet IDs mà Dispatcher được phân công quản lý"""
    query = select(FleetDispatcher.fleet_id).where(
        and_(
            FleetDispatcher.user_id == user_id,
            FleetDispatcher.removed_at.is_(None)
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all())

def apply_data_scope(
    query: Any,
    model: Any,
    user: Driver,
    db: Optional[AsyncSession] = None,
    allowed_fleet_ids: Optional[List[int]] = None
) -> Any:
    """
    Áp dụng bộ lọc Data Scope đa tầng cho SQLAlchemy query:
    1. Scope SELF (FLEET_DRIVER):
       - Chỉ thấy dữ liệu của chính mình (driver_id == user.id hoặc id == user.id).
    2. Scope FLEET (FLEET_DISPATCHER):
       - Lọc theo organization_id VÀ danh sách fleet_id được phân công (nếu model có fleet_id).
    3. Scope COMPANY (ENTERPRISE_ADMIN):
       - Lọc toàn bộ trong phạm vi organization_id của doanh nghiệp.
    """
    if not user:
        return query

    scope = get_data_scope(user)

    # 1. Scope SELF: tài xế chỉ xem dữ liệu cá nhân
    if scope == DataScope.SELF.value:
        if hasattr(model, "driver_id"):
            query = query.where(model.driver_id == user.id)
        elif hasattr(model, "id") and model.__name__ == "Driver":
            query = query.where(model.id == user.id)
        return query

    # 2. Base Company isolation: Luôn luôn cô lập theo organization_id của user
    if hasattr(model, "organization_id") and user.organization_id is not None:
        query = query.where(model.organization_id == user.organization_id)
    elif hasattr(model, "company_id") and user.organization_id is not None:
        query = query.where(model.company_id == user.organization_id)

    # 3. Scope FLEET: Lọc thêm theo fleet_id nếu có
    if scope == DataScope.FLEET.value and allowed_fleet_ids is not None:
        if hasattr(model, "fleet_id"):
            query = query.where(model.fleet_id.in_(allowed_fleet_ids))

    return query

async def can_access_resource(
    user: Driver,
    resource_company_id: Optional[int],
    resource_fleet_id: Optional[int] = None,
    resource_driver_id: Optional[int] = None,
    db: Optional[AsyncSession] = None
) -> bool:
    """
    Kiểm tra quyền truy cập tài nguyên (Multi-Tenant & Data Scope Protection)
    """
    if not user or not user.is_active:
        return False
    
    # Không thể truy cập tài nguyên thuộc Company khác
    if resource_company_id is not None and user.organization_id != resource_company_id:
        return False

    normalized_role = normalize_role_code(user.role)
    if normalized_role == "ENTERPRISE_ADMIN":
        return True

    # Nếu là Driver: chỉ truy cập tài nguyên của chính mình
    if normalized_role == "FLEET_DRIVER":
        if resource_driver_id is not None:
            return user.id == resource_driver_id
        return True

    # Nếu là Dispatcher: kiểm tra fleet assignment nếu có
    if normalized_role == "FLEET_DISPATCHER" and resource_fleet_id is not None and db is not None:
        fleet_ids = await get_dispatcher_fleet_ids(db, user.id)
        # Nếu chưa gán fleet nào hoặc xe thuộc fleet được gán
        if fleet_ids and resource_fleet_id not in fleet_ids:
            return False

    return True
