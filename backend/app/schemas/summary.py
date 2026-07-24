from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NodeSummaryResponse(BaseModel):
    category_id: int
    total_count: int = Field(..., description="总条目数（含后代）")
    unread_count: int = Field(..., description="当前用户未读数")
    pending_count: int = Field(..., description="待复核数")
    updated_at: Optional[datetime] = None
