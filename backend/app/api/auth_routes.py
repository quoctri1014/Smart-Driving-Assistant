from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from backend.app.database.session import get_db
from backend.app.models_db.driver import Driver
from backend.app.models_db.rbac import Role, Permission
from backend.app.models_db.organization import Organization
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.app.auth.rbac_service import (
    normalize_role_code,
    get_user_permissions,
    get_data_scope
)

router = APIRouter()

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "FLEET_DRIVER"
    organization_id: Optional[int] = 1

@router.post("/register")
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    exist = (await db.execute(select(Driver).where(Driver.email == email_clean))).scalars().first()
    if exist:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký trên hệ thống")
    
    normalized_role = normalize_role_code(payload.role)
    role_obj = (await db.execute(select(Role).where(Role.code == normalized_role))).scalars().first()
    
    new_user = Driver(
        email=email_clean,
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=normalized_role,
        role_id=role_obj.id if role_obj else None,
        organization_id=payload.organization_id or 1,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    permissions = list(await get_user_permissions(new_user, db))
    data_scope = get_data_scope(new_user)

    token = create_access_token(
        {
            "sub": new_user.email,
            "user_id": new_user.id,
            "role": new_user.role,
            "org_id": new_user.organization_id,
            "full_name": new_user.full_name
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": new_user.role,
        "role_code": normalized_role,
        "data_scope": data_scope,
        "permissions": permissions,
        "full_name": new_user.full_name
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    email_clean = form_data.username.strip().lower()
    user = (await db.execute(select(Driver).where(Driver.email == email_clean))).scalars().first()
    
    # Auto-seed demo accounts nếu mới khởi tạo DB
    if not user:
        if email_clean in ["admin@vinafleet.com", "admin@example.com", "driver1@example.com", "driver@vinafleet.com", "driver@example.com", "demo@example.com", "dispatcher@vinafleet.com"]:
            default_org = (await db.execute(select(Organization).limit(1))).scalars().first()
            org_id = default_org.id if default_org else 1

            is_admin = "admin" in email_clean
            is_dispatcher = "dispatcher" in email_clean
            
            assigned_role_code = "ENTERPRISE_ADMIN" if is_admin else ("FLEET_DISPATCHER" if is_dispatcher else "FLEET_DRIVER")
            role_obj = (await db.execute(select(Role).where(Role.code == assigned_role_code))).scalars().first()

            user = Driver(
                email=email_clean,
                password_hash=get_password_hash("password123"),
                full_name="Quản Trị Viên Doanh Nghiệp" if is_admin else ("Điều Độ Viên Đội Xe" if is_dispatcher else "Tài Xế Doanh Nghiệp"),
                role=assigned_role_code,
                role_id=role_obj.id if role_obj else None,
                organization_id=org_id,
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác")
    else:
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Tài khoản này đã bị vô hiệu hóa")
        
        # Cho phép password hoặc mật khẩu demo 'password', 'password123', '123456'
        if not verify_password(form_data.password, user.password_hash) and form_data.password not in ("password", "password123", "123456"):
            raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác")

    # Đảm bảo role_code chuẩn
    normalized_role = normalize_role_code(user.role)
    if user.role != normalized_role:
        user.role = normalized_role
        await db.commit()

    permissions = list(await get_user_permissions(user, db))
    data_scope = get_data_scope(user)

    token = create_access_token(
        {
            "sub": user.email,
            "user_id": user.id,
            "role": user.role,
            "org_id": user.organization_id,
            "full_name": user.full_name
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "role_code": normalized_role,
        "data_scope": data_scope,
        "permissions": permissions,
        "full_name": user.full_name,
        "email": user.email
    }

@router.post("/refresh")
async def refresh_token(
    current_user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Làm mới mã phiên đăng nhập (Access Token JWT)"""
    permissions = list(await get_user_permissions(current_user, db))
    data_scope = get_data_scope(current_user)
    normalized_role = normalize_role_code(current_user.role)

    token = create_access_token(
        {
            "sub": current_user.email,
            "user_id": current_user.id,
            "role": current_user.role,
            "org_id": current_user.organization_id,
            "full_name": current_user.full_name
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": current_user.role,
        "role_code": normalized_role,
        "data_scope": data_scope,
        "permissions": permissions,
        "full_name": current_user.full_name,
        "email": current_user.email
    }

@router.get("/me")
async def get_my_profile(
    user: Driver = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lấy thông tin tài khoản hiện tại kèm Data Scope và danh sách quyền (Permissions)"""
    permissions = list(await get_user_permissions(user, db))
    data_scope = get_data_scope(user)
    normalized_role = normalize_role_code(user.role)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name or "Người Dùng",
        "role": user.role,
        "role_code": normalized_role,
        "organization_id": user.organization_id,
        "data_scope": data_scope,
        "permissions": permissions,
        "is_active": user.is_active
    }

@router.get("/permissions")
async def list_permissions(
    user: Driver = Depends(require_permission("role.view")),
    db: AsyncSession = Depends(get_db)
):
    """Danh mục toàn bộ permissions trong hệ thống (Dành cho Quản trị viên)"""
    result = await db.execute(select(Permission).order_by(Permission.module.asc(), Permission.code.asc()))
    perms = result.scalars().all()
    return [
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "module": p.module,
            "description": p.description
        }
        for p in perms
    ]

@router.get("/roles")
async def list_roles(
    user: Driver = Depends(require_permission("role.view")),
    db: AsyncSession = Depends(get_db)
):
    """Danh mục toàn bộ roles và quyền gán (Dành cho Quản trị viên)"""
    result = await db.execute(select(Role).order_by(Role.id.asc()))
    roles = result.scalars().all()
    return [
        {
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "default_scope": r.default_scope,
            "permissions": [p.code for p in r.permissions] if r.permissions else []
        }
        for r in roles
    ]
