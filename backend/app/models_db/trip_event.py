from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, BigInteger, Text, Index
from sqlalchemy.orm import relationship
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class TripEvent(Base):
    __tablename__ = "trip_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("driving_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True) 
    # Types: TRIP_STARTED, SPEED_WARNING, UNSAFE_DISTANCE, SAFE_DISTANCE_RESTORED, 
    # DROWSINESS_WARNING, DRIVER_RECOVERED, COLLISION_WARNING, SEATBELT_WARNING, TRIP_ENDED
    
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    video_offset_ms = Column(BigInteger, nullable=True) # Offset mili-giây tính từ lúc bắt đầu quay video
    sequence_num = Column(Integer, default=1, nullable=False) # Deterministic ordering
    severity = Column(String(50), default="INFO", nullable=False) # 'INFO', 'WARNING', 'CRITICAL', 'SAFE'
    
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id", ondelete="SET NULL"), nullable=True)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    metadata_json = Column(Text, nullable=True) # JSON schema theo event_type
    
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_trip_events_session_time", "session_id", "timestamp"),
        Index("ix_trip_events_session_seq_time", "session_id", "sequence_num", "timestamp"),
    )

    session = relationship("DrivingSession", back_populates="events")
    violation = relationship("Violation")
