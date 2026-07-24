from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.database import Base


class ReadingStatus(Base):
    __tablename__ = "reading_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_read = Column(Boolean, default=True)
    read_at = Column(DateTime, server_default=func.now())

    knowledge = relationship("Knowledge", back_populates="reading_statuses")
    user = relationship("User", back_populates="reading_statuses")
