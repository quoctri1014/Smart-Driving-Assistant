"""Add tenant boundaries without assigning unknown legacy data to customers."""
import asyncio
from sqlalchemy import text
from backend.app.database.session import engine
from backend.app.database.init_db import init_db

async def migrate():
    await init_db()
    async with engine.begin() as conn:
        for table in ("drivers", "vehicles", "driving_sessions", "violations"):
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id)"))
            await conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_organization_id ON {table}(organization_id)"))
        await conn.execute(text("ALTER TABLE drivers ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        await conn.execute(text("ALTER TABLE violations ADD COLUMN IF NOT EXISTS driver_id INTEGER REFERENCES drivers(id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_violations_driver_id ON violations(driver_id)"))
    print("Migration complete. Legacy rows without organization ownership remain inaccessible.")

if __name__ == "__main__":
    asyncio.run(migrate())
