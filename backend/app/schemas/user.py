from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    role: str = Field(..., description="角色")


class UserCreate(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    role: str = Field(..., description="角色")
    name: str = Field(..., description="姓名")


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    name: str
    created_at: datetime
    token: Optional[str] = None

    class Config:
        from_attributes = True
