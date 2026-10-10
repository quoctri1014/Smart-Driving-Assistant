from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=True, index=True)
    status = Column(String(20), default="active", nullable=False) # 'active', 'inactive'
    created_at = Column(DateTime, default=utc_now, nullable=False)

    company = relationship("Organization", foreign_keys=[company_id])
    fleets = relationship("Fleet", back_populates="branch", cascade="all, delete-orphan")

class Fleet(Base):
    __tablename__ = "fleets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=True, index=True)
    status = Column(String(20), default="active", nullable=False) # 'active', 'inactive'
    created_at = Column(DateTime, default=utc_now, nullable=False)

    branch = relationship("Branch", back_populates="fleets")
    company = relationship("Organization", foreign_keys=[company_id])
    vehicles = relationship("Vehicle", back_populates="fleet")
    dispatchers = relationship("FleetDispatcher", back_populates="fleet", cascade="all, delete-orphan")
    drivers = relationship("FleetDriver", back_populates="fleet", cascade="all, delete-orphan")

class FleetDispatcher(Base):
    __tablename__ = "fleet_dispatchers"

    id = Column(Integer, primary_key=True, index=True)
    fleet_id = Column(Integer, ForeignKey("fleets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=utc_now, nullable=False)
    removed_at = Column(DateTime, nullable=True)

    fleet = relationship("Fleet", back_populates="dispatchers")
    user = relationship("Driver", foreign_keys=[user_id])

class FleetDriver(Base):
    __tablename__ = "fleet_drivers"

    id = Column(Integer, primary_key=True, index=True)
    fleet_id = Column(Integer, ForeignKey("fleets.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=utc_now, nullable=False)
    removed_at = Column(DateTime, nullable=True)

    fleet = relationship("Fleet", back_populates="drivers")
    driver = relationship("Driver", foreign_keys=[driver_id])

class VehicleAssignment(Base):
    __tablename__ = "vehicle_assignments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_from = Column(DateTime, default=utc_now, nullable=False, index=True)
    assigned_to = Column(DateTime, nullable=True, index=True)
    assigned_by = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), default="active", nullable=False, index=True) # 'active', 'ended', 'cancelled'
    notes = Column(String(500), nullable=True)

    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id])
    driver = relationship("Driver", foreign_keys=[driver_id])
    assigner = relationship("Driver", foreign_keys=[assigned_by])
