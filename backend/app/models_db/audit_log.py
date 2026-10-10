from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(200), nullable=True)
    action = Column(String(100), nullable=False, index=True) # e.g. 'ROLE_CHANGE', 'AI_CONFIG_UPDATE', 'VIOLATION_REVIEW', 'VEHICLE_ASSIGN', 'USER_DISABLE'
    resource_type = Column(String(100), nullable=True, index=True) # 'violation', 'user', 'fleet', 'vehicle', 'ai_config'
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True) # JSON hoặc mô tả chi tiết thay đổi
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_logs_company_created", "company_id", "created_at"),
        Index("ix_audit_logs_company_action_created", "company_id", "action", "created_at"),
    )
