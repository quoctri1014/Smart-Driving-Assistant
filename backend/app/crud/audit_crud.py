from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
import datetime

from backend.app.models_db.audit_log import AuditLog

async def log_audit_event(
    db: AsyncSession,
    company_id: int,
    user_id: Optional[int],
    user_email: Optional[str],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[dict | str] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """Ghi nhận nhật ký kiểm toán (Audit Event) an toàn"""
    details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, dict) else details
    audit_entry = AuditLog(
        company_id=company_id,
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details_str,
        ip_address=ip_address,
        created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    )
    db.add(audit_entry)
    await db.commit()
    await db.refresh(audit_entry)
    return audit_entry

async def get_audit_logs(
    db: AsyncSession,
    company_id: int,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AuditLog]:
    query = select(AuditLog).where(AuditLog.company_id == company_id)
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
    if action is not None:
        query = query.where(AuditLog.action == action)
    if resource_type is not None:
        query = query.where(AuditLog.resource_type == resource_type)
    clamped_limit = max(1, min(limit, 100))
    query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(skip).limit(clamped_limit)
    result = await db.execute(query)
    return result.scalars().all()
