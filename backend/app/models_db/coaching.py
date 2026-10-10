from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Index
from sqlalchemy.orm import relationship, synonym
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now


class CoachingAssignment(Base):
    __tablename__ = "coaching_assignments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = synonym("company_id")

    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    module_type = Column(String(50), default="GENERAL", nullable=False)  # 'DMS_DROWSINESS', 'SPEED_LIMIT', 'SAFE_DISTANCE', 'SEATBELT', 'GENERAL'

    status = Column(String(30), default="ASSIGNED", nullable=False, index=True)  # 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE'
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    driver_notes = Column(Text, nullable=True)
    score_restored = Column(Float, default=0.0)  # Điểm an toàn được phục hồi sau khóa huấn luyện

    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_coaching_company_driver", "company_id", "driver_id"),
        Index("ix_coaching_status", "status"),
    )

    driver = relationship("Driver", foreign_keys=[driver_id])
    assigner = relationship("Driver", foreign_keys=[assigned_by])
    violation = relationship("Violation", foreign_keys=[violation_id])
