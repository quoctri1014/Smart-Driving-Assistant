from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class DeviceHealth(Base):
    __tablename__ = "device_health"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    fleet_id = Column(Integer, ForeignKey("fleets.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status = Column(String(50), default="ONLINE", nullable=False, index=True) # 'ONLINE', 'DEGRADED', 'OFFLINE', 'UNKNOWN'
    
    # 7 Subsystems
    road_camera_status = Column(String(50), default="UNKNOWN", nullable=False) # 'ONLINE', 'DEGRADED', 'OFFLINE', 'UNKNOWN'
    cabin_camera_status = Column(String(50), default="UNKNOWN", nullable=False)
    gps_status = Column(String(50), default="UNKNOWN", nullable=False)
    dms_status = Column(String(50), default="UNKNOWN", nullable=False)
    network_status = Column(String(50), default="UNKNOWN", nullable=False)
    storage_status = Column(String(50), default="UNKNOWN", nullable=False)
    
    firmware_version = Column(String(50), default="v2.4.1", nullable=True)
    last_heartbeat_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    vehicle = relationship("Vehicle")
    fleet = relationship("Fleet")
    heartbeats = relationship("DeviceHeartbeat", back_populates="device", cascade="all, delete-orphan")


class DeviceHeartbeat(Base):
    __tablename__ = "device_heartbeats"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), ForeignKey("device_health.device_id", ondelete="CASCADE"), nullable=False, index=True)
    heartbeat_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    metrics_json = Column(Text, nullable=True) # Chỉ lưu telemetry thật nếu phần cứng cung cấp

    device = relationship("DeviceHealth", back_populates="heartbeats")
