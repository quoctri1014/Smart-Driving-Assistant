from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from backend.app.database.base import Base

# Bảng liên kết Many-to-Many giữa Role và Permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False) # e.g. 'vehicle.create'
    name = Column(String(200), nullable=False)
    module = Column(String(100), index=True, nullable=False) # e.g. 'vehicle', 'dashboard'
    description = Column(String(500), nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # 'ENTERPRISE_ADMIN', 'FLEET_DISPATCHER', 'FLEET_DRIVER'
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    default_scope = Column(String(50), nullable=False, default="SELF") # 'COMPANY', 'FLEET', 'SELF', 'BRANCH', 'ALL'

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles", lazy="selectin")
