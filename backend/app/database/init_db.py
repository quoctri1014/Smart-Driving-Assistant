import asyncio
from backend.app.database.session import engine
from backend.app.database.base import Base
# Import all models to ensure they are registered with Base
from backend.app.models_db.driver import Driver
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.driving_session import DrivingSession
from backend.app.models_db.violation import Violation

async def init_db():
    async with engine.begin() as conn:
        # Create all tables
        # await conn.run_sync(Base.metadata.drop_all) # Dùng cẩn thận
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
