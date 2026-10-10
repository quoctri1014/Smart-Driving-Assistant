from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index, Float
from sqlalchemy.orm import relationship, synonym
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now
from backend.app.models_db.rbac import Role


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    organization_id = synonym("company_id")
    
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="FLEET_DRIVER", index=True) # "ENTERPRISE_ADMIN", "FLEET_DISPATCHER", "FLEET_DRIVER"
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, index=True)
    safety_score = Column(Float, default=100.0, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    __table_args__ = (
        Index("ix_drivers_company_role", "company_id", "role"),
    )

    # Quan hệ với Role trong RBAC
    role_rel = relationship("Role", lazy="selectin")

    # Quan hệ 1-nhiều với DrivingSession
    sessions = relationship("DrivingSession", back_populates="driver", cascade="all, delete-orphan")
