from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.database.base import Base
import datetime

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    violation_type = Column(String, index=True, nullable=False) # e.g., 'drowsy', 'no_seatbelt', 'collision_danger', 'helmet_violation'
    severity = Column(String, default="warning") # 'warning', 'critical'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    image_path = Column(String, nullable=True) # Đường dẫn file ảnh
    
    # ForeignKey tuỳ chọn (có thể là lỗi của phương tiện hoặc lỗi của tài xế)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("driving_sessions.id"), nullable=True)

    vehicle = relationship("Vehicle", back_populates="violations")
    session = relationship("DrivingSession", back_populates="violations")
