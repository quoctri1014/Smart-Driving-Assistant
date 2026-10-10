import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
from backend.app.database.base import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)
    severity = Column(String(50), default="INFO", nullable=False) # 'CRITICAL', 'WARNING', 'INFO', 'SAFE', 'SYSTEM'
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    dedup_key = Column(String(255), nullable=True, index=True)
    resource_type = Column(String(50), nullable=True) # 'violation', 'assignment', 'system'
    resource_id = Column(Integer, nullable=True)
    delivery_status = Column(String(50), default="SENT", nullable=False) # 'PENDING', 'SENT', 'FAILED'
    retry_count = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None), nullable=False, index=True)

    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "read_at", "created_at"),
        Index("ix_notifications_user_ack_created", "user_id", "acknowledged_at", "created_at"),
        Index("ix_notifications_company_dedup", "company_id", "user_id", "dedup_key"),
    )
