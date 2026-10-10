from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Index
from sqlalchemy.orm import relationship, synonym
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now


class Journey(Base):
    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = synonym("company_id")

    journey_code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=True)

    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=False, index=True)
    dispatcher_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)

    # State Machine: PLANNED -> CHECKLIST -> ACTIVE -> COMPLETED / CANCELLED
    status = Column(String(30), default="PLANNED", nullable=False, index=True)

    start_location = Column(String(255), nullable=True)
    destination = Column(String(255), nullable=True)

    planned_start_time = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(Text, nullable=True)

    # Pre-Trip Checklist
    checklist_status = Column(String(30), default="PENDING", nullable=False)  # 'PENDING', 'PASSED', 'FAILED'
    checklist_data = Column(Text, nullable=True)  # JSON formatted details
    checklist_submitted_at = Column(DateTime, nullable=True)

    # Liên kết với DrivingSession của hệ thống telemetry
    session_id = Column(Integer, ForeignKey("driving_sessions.id", ondelete="SET NULL"), nullable=True, index=True)

    safety_score = Column(Float, default=100.0, nullable=False)
    total_distance_km = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_journeys_company_status", "company_id", "status"),
        Index("ix_journeys_driver_status", "driver_id", "status"),
        Index("ix_journeys_vehicle_status", "vehicle_id", "status"),
    )

    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id])
    driver = relationship("Driver", foreign_keys=[driver_id])
    dispatcher = relationship("Driver", foreign_keys=[dispatcher_id])
    session = relationship("DrivingSession", foreign_keys=[session_id])
    violations = relationship("Violation", back_populates="journey")
