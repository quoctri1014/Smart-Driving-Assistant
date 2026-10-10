from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from backend.app.database.base import Base
from backend.app.utils.datetime_utils import utc_now

class ViolationReview(Base):
    __tablename__ = "violation_reviews"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    action = Column(String(50), nullable=False) # 'CONFIRM', 'FALSE_POSITIVE', 'NEED_EVIDENCE', 'REOPEN', 'RESOLVE'
    old_review_status = Column(String(50), nullable=False)
    new_review_status = Column(String(50), nullable=False)
    old_resolution_status = Column(String(50), nullable=False)
    new_resolution_status = Column(String(50), nullable=False)
    
    note = Column(Text, nullable=False) # Bắt buộc giải trình (min 5 chars)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    __table_args__ = (
        Index("ix_violation_reviews_viol_created", "violation_id", "created_at"),
    )

    violation = relationship("Violation", back_populates="reviews")
    reviewer = relationship("Driver", foreign_keys=[reviewer_id])
