from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    fleet_id = Column(Integer, ForeignKey("fleets.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 12 AI Module Sensitivity & Thresholds
    drowsiness_threshold_frames = Column(Integer, default=15, nullable=False)
    collision_warning_distance_m = Column(Float, default=15.0, nullable=False)
    collision_clear_frames = Column(Integer, default=8, nullable=False)
    speed_limit_buffer_kmh = Column(Float, default=5.0, nullable=False)
    dms_mandatory_during_trip = Column(Boolean, default=True, nullable=False) # Không cho phép tài xế tắt DMS trong chuyến đi
    allow_temporary_mute_minutes = Column(Integer, default=5, nullable=False)
    
    updated_by = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
