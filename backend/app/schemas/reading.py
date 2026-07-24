from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReadingStatusResponse(BaseModel):
    id: int
    knowledge_id: int
    knowledge_title: Optional[str] = None
    user_id: int
    is_read: bool
    read_at: datetime

    class Config:
        from_attributes = True
