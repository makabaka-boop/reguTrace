from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from backend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    knowledge_submitted = relationship("Knowledge", back_populates="submitter")
    reading_statuses = relationship("ReadingStatus", back_populates="user")
    review_records = relationship("ReviewRecord", back_populates="reviewer")
    groups = relationship("GroupMember", back_populates="user")
