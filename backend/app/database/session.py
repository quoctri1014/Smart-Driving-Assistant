import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./trafficguard.db")

# Cấu hình engine linh hoạt cho SQLite và PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
AsyncSessionLocal = async_session_maker

async def get_db():
    async with async_session_maker() as session:
        yield session
