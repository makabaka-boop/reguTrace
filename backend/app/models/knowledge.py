from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_status = Column(String(20), default="pending")
    reject_reason = Column(Text)
    suggested_review_cycle = Column(String(20), default="6months")
    next_review_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="knowledge_items")
    submitter = relationship("User", back_populates="knowledge_submitted")
    reading_statuses = relationship("ReadingStatus", back_populates="knowledge")
    review_records = relationship("ReviewRecord", back_populates="knowledge")
