from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship, synonym
from backend.app.database.base import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    organization_id = synonym("company_id")
    
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    fleet_id = Column(Integer, ForeignKey("fleets.id", ondelete="SET NULL"), nullable=True, index=True)
    license_plate = Column(String(50), unique=True, index=True, nullable=False)
    vehicle_type = Column(String(50), default="car", nullable=False) # car, truck, bus, motorbike
    status = Column(String(30), default="active", nullable=False) # active, maintenance, inactive

    __table_args__ = (
        Index("ix_vehicles_company_fleet", "company_id", "fleet_id"),
    )

    # Quan hệ
    fleet = relationship("Fleet", back_populates="vehicles")
    violations = relationship("Violation", back_populates="vehicle")
    assignments = relationship("VehicleAssignment", back_populates="vehicle", cascade="all, delete-orphan")
