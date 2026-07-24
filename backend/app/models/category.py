from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50))
    parent_id = Column(Integer, ForeignKey("categories.id"))
    group_id = Column(Integer, ForeignKey("user_groups.id"))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    level = Column(Integer, default=1)
    path = Column(String(500), default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    parent = relationship("Category", remote_side=[id], backref="children")
    group = relationship("UserGroup", back_populates="categories")
    knowledge_items = relationship("Knowledge", back_populates="category")
    summary = relationship("NodeSummary", back_populates="category", uselist=False)
