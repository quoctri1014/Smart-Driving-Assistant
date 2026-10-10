"""Provision a real organization and its first administrator; never seed data."""
import asyncio
from getpass import getpass
from backend.app.database.session import async_session_maker
from backend.app.models_db.organization import Organization
from backend.app.models_db.driver import Driver
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.driving_session import DrivingSession
from backend.app.models_db.violation import Violation
from backend.app.auth.security import get_password_hash

async def create(name, email, full_name, password):
    if not all((name.strip(), email.strip(), full_name.strip())) or not 12 <= len(password.encode()) <= 72:
        raise ValueError("Real organization details and a 12-72 byte password are required")
    async with async_session_maker() as db:
        async with db.begin():
            organization = Organization(name=name.strip())
            db.add(organization)
            await db.flush()
            db.add(Driver(organization_id=organization.id, email=email.strip().lower(), full_name=full_name.strip(),
                          password_hash=get_password_hash(password), role="admin"))
    print("Organization and administrator created.")

if __name__ == "__main__":
    asyncio.run(create(input("Organization name: "), input("Admin email: "), input("Admin full name: "), getpass("Admin password: ")))
