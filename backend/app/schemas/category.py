from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str = Field(..., description="分类名称")
    code: Optional[str] = Field(None, description="分类编码")
    parent_id: Optional[int] = Field(None, description="父节点ID")
    group_id: Optional[int] = Field(None, description="责任小组ID")
    sort_order: int = Field(0, description="排序")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, description="分类名称")
    code: Optional[str] = Field(None, description="分类编码")
    group_id: Optional[int] = Field(None, description="责任小组ID")
    sort_order: Optional[int] = Field(None, description="排序")
    is_active: Optional[bool] = Field(None, description="是否启用")


class CategoryResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    parent_id: Optional[int]
    group_id: Optional[int]
    sort_order: int
    is_active: bool
    level: int
    path: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryTreeNode(CategoryResponse):
    children: List["CategoryTreeNode"] = Field(default_factory=list, description="子节点")

    class Config:
        from_attributes = True


CategoryTreeNode.model_rebuild()


class CategoryMoveRequest(BaseModel):
    target_parent_id: int = Field(..., description="目标父节点ID")


class CategoryMergeRequest(BaseModel):
    target_category_id: int = Field(..., description="目标分类节点ID")


class CategoryCopyRequest(BaseModel):
    target_group_id: int = Field(..., description="目标小组ID")
    target_parent_id: Optional[int] = Field(None, description="目标父节点ID")
