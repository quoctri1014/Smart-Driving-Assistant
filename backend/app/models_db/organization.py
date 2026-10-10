from sqlalchemy import Column, Integer, String, DateTime
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
