import asyncio
import os
from backend.app.database.session import async_session_maker, engine
from backend.app.database.base import Base
from backend.app.models_db.driver import Driver
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.driving_session import DrivingSession
from backend.app.models_db.violation import Violation
from backend.app.auth.security import get_password_hash
from datetime import datetime, timedelta

async def seed_data():
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session_maker() as db:
        print("Seeding Driver...")
        driver = Driver(
            email="demo@example.com",
            password_hash=get_password_hash("password123"),
            full_name="Tài Xế Demo"
        )
        db.add(driver)
        await db.commit()
        await db.refresh(driver)
        
        print("Seeding Vehicle...")
        vehicle = Vehicle(
            license_plate="30A-123.45",
            vehicle_type="car"
        )
        db.add(vehicle)
        await db.commit()
        await db.refresh(vehicle)
        
        print("Seeding Driving Session...")
        session = DrivingSession(
            driver_id=driver.id,
            start_time=datetime.utcnow() - timedelta(hours=2),
            end_time=datetime.utcnow(),
            total_minutes=120.0
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        print("Seeding Violations...")
        v1 = Violation(
            violation_type="drowsy",
            severity="critical",
            timestamp=datetime.utcnow() - timedelta(minutes=30),
            session_id=session.id
        )
        v2 = Violation(
            violation_type="collision",
            severity="warning",
            timestamp=datetime.utcnow() - timedelta(minutes=10),
            vehicle_id=vehicle.id
        )
        db.add_all([v1, v2])
        await db.commit()
        
    print("Seeding complete! Use email: demo@example.com, password: password123")

if __name__ == "__main__":
    asyncio.run(seed_data())
