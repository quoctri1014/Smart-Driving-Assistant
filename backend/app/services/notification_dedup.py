import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.app.models_db.notification import Notification

COOLDOWN_SECONDS = 45

def build_dedup_key(event_type: str, vehicle_id: Optional[int], trip_id: Optional[int], severity: str) -> str:
    """Tạo khóa chống spam deduplication: {event_type}:{vehicle_id}:{trip_id}:{severity}"""
    v_id = vehicle_id if vehicle_id is not None else "any"
    t_id = trip_id if trip_id is not None else "any"
    return f"{event_type}:{v_id}:{t_id}:{severity.upper()}"

async def should_send_notification(
    db: AsyncSession,
    company_id: int,
    user_id: int,
    dedup_key: str,
    severity: str
) -> bool:
    """
    Kiểm tra cơ chế throttle/cooldown chống gửi lặp notification mỗi frame AI:
    - Nếu cùng dedup_key đã gửi trong vòng 45s: Bỏ qua (False).
    - Nếu mức độ nguy hiểm leo thang (escalation lên CRITICAL): Cho phép bypass cooldown (True).
    - Tính toán thời gian độc lập với phương ngữ Database (PostgreSQL / SQLite agnostic).
    """
    query = select(Notification).where(
        and_(
            Notification.company_id == company_id,
            Notification.user_id == user_id,
            Notification.dedup_key == dedup_key
        )
    ).order_by(Notification.created_at.desc()).limit(1)

    result = await db.execute(query)
    recent = result.scalars().first()

    if not recent or not recent.created_at:
        return True

    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    created_dt = recent.created_at.replace(tzinfo=None) if hasattr(recent.created_at, "tzinfo") and recent.created_at.tzinfo else recent.created_at
    
    elapsed_seconds = abs((now - created_dt).total_seconds())
    cooldown = 15 if severity.upper() == "CRITICAL" else COOLDOWN_SECONDS

    return elapsed_seconds >= cooldown
