from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from backend.app.database.base import Base
import datetime

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="driver", index=True) # "driver" or "admin"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Quan hệ 1-nhiều với DrivingSession
    sessions = relationship("DrivingSession", back_populates="driver", cascade="all, delete-orphan")
