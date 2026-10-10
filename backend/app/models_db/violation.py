from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Index
from sqlalchemy.orm import relationship, synonym
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    organization_id = synonym("company_id")

    fleet_id = Column(Integer, ForeignKey("fleets.id", ondelete="SET NULL"), nullable=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("driving_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id", ondelete="SET NULL"), nullable=True, index=True)
    
    violation_type = Column(String(100), index=True, nullable=False) # 'drowsy', 'no_seatbelt', 'collision_danger', 'helmet_violation', 'speed_limit'
    severity = Column(String(50), default="WARNING", nullable=False) # 'INFO', 'WARNING', 'CRITICAL'
    
    # Tách biệt Review State & Incident Resolution State
    review_status = Column(String(50), default="PENDING_REVIEW", nullable=False, index=True) # PENDING_REVIEW, NEEDS_EVIDENCE, CONFIRMED, FALSE_POSITIVE
    resolution_status = Column(String(50), default="OPEN", nullable=False, index=True) # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    status = Column(String(50), default="PENDING_REVIEW", nullable=False, index=True) # Backward-compatibility synonym
    
    # AI Telemetry & Metadata
    confidence = Column(Float, nullable=True) # Nullable float: 0.0 -> 1.0 (Không fake số)
    source_module = Column(String(100), nullable=True) # 'dms_eye_tracker', 'helmet_detector', 'speed_monitor', etc.
    model_version = Column(String(50), default="yolov8n-traffic-v2.1", nullable=True)
    speed_kph = Column(Float, nullable=True)
    speed_limit_kph = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True)
    image_path = Column(String(500), nullable=True)
    
    detected_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True) # Backward compatibility
    
    # Review & Incident resolution
    reviewed_by = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Optimistic Concurrency Control
    version = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_violations_comp_detected", "company_id", "detected_at"),
        Index("ix_violations_comp_rev_detected", "company_id", "review_status", "detected_at"),
        Index("ix_violations_fleet_detected", "fleet_id", "detected_at"),
        Index("ix_violations_driver_detected", "driver_id", "detected_at"),
    )

    vehicle = relationship("Vehicle", back_populates="violations")
    session = relationship("DrivingSession", back_populates="violations")
    journey = relationship("Journey", back_populates="violations")
    driver = relationship("Driver", foreign_keys=[driver_id])
    reviewer = relationship("Driver", foreign_keys=[reviewed_by])
    reviews = relationship("ViolationReview", back_populates="violation", cascade="all, delete-orphan")
