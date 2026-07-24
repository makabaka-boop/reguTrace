from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GroupBase(BaseModel):
    name: str = Field(..., description="小组名称")
    description: Optional[str] = Field(None, description="描述")


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, description="小组名称")
    description: Optional[str] = Field(None, description="描述")


class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
