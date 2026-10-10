from backend.app.database.base import Base
from backend.app.models_db.organization import Organization
from backend.app.models_db.organization_structure import (
    Branch,
    Fleet,
    FleetDispatcher,
    FleetDriver,
    VehicleAssignment,
)
from backend.app.models_db.rbac import Role, Permission, role_permissions
from backend.app.models_db.driver import Driver
from backend.app.models_db.driving_session import DrivingSession
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.violation import Violation
from backend.app.models_db.violation_review import ViolationReview
from backend.app.models_db.trip_event import TripEvent
from backend.app.models_db.device_health import DeviceHealth
from backend.app.models_db.audit_log import AuditLog
from backend.app.models_db.notification import Notification
from backend.app.models_db.ai_config import AIConfig
from backend.app.models_db.journey import Journey
from backend.app.models_db.coaching import CoachingAssignment

__all__ = [
    "Base",
    "Organization",
    "Branch",
    "Fleet",
    "FleetDispatcher",
    "FleetDriver",
    "VehicleAssignment",
    "Role",
    "Permission",
    "role_permissions",
    "Driver",
    "DrivingSession",
    "Vehicle",
    "Violation",
    "ViolationReview",
    "TripEvent",
    "DeviceHealth",
    "AuditLog",
    "Notification",
    "AIConfig",
    "Journey",
    "CoachingAssignment",
]
