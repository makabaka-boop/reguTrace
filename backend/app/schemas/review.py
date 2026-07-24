from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReviewRequest(BaseModel):
    remark: Optional[str] = Field(None, description="备注")
    new_category_id: Optional[int] = Field(None, description="调整后的分类ID")


class ReviewBatchRequest(BaseModel):
    knowledge_ids: List[int] = Field(..., description="制度条目ID列表")
    remark: Optional[str] = Field(None, description="备注")


class ReviewRecordResponse(BaseModel):
    id: int
    knowledge_id: int
    knowledge_title: Optional[str] = None
    reviewer_id: int
    reviewer_name: Optional[str] = None
    action: str
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
