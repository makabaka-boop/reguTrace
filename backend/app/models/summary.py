from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.database import Base


class NodeSummary(Base):
    __tablename__ = "node_summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), unique=True, nullable=False)
    total_count = Column(Integer, default=0)
    pending_count = Column(Integer, default=0)
    updated_at = Column(DateTime, server_default=func.now())

    category = relationship("Category", back_populates="summary")
