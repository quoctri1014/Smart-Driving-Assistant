from sqlalchemy import Column, Integer, DateTime, ForeignKey, Float, Index, text
from sqlalchemy.orm import relationship, synonym
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class DrivingSession(Base):
    __tablename__ = "driving_sessions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    organization_id = synonym("company_id")
    
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime, default=utc_now, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True, index=True)
    total_minutes = Column(Float, default=0.0)

    __table_args__ = (
        # DB-Level Invariant: Mỗi tài xế chỉ có tối đa 1 chuyến đi đang hoạt động (end_time IS NULL)
        Index(
            "uq_active_session_per_driver",
            "driver_id",
            unique=True,
            sqlite_where=text("end_time IS NULL"),
            postgresql_where=text("end_time IS NULL")
        ),
        Index("ix_driving_sessions_company_start", "company_id", "start_time"),
    )

    driver = relationship("Driver", back_populates="sessions")
    violations = relationship("Violation", back_populates="session")
    events = relationship("TripEvent", back_populates="session", cascade="all, delete-orphan")
