from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String, unique=True, index=True, nullable=False)
    vehicle_type = Column(String, nullable=True) # car, truck, bus, motorbike

    # Quan hệ 1-nhiều với Violation (road-facing)
    violations = relationship("Violation", back_populates="vehicle")
