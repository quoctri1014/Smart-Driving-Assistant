from sqlalchemy import Column, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.database.base import Base
import datetime

class DrivingSession(Base):
    __tablename__ = "driving_sessions"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_minutes = Column(Float, default=0.0)

    driver = relationship("Driver", back_populates="sessions")
    # Vi phạm của người lái (driver-facing) trong phiên này
    violations = relationship("Violation", back_populates="session")
