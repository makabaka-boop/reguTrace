from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.database import get_db
from backend.app.schemas import (
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse,
    KnowledgeListResponse, ApiResponse
)
from backend.app.services import KnowledgeService
from backend.app.utils.security import get_current_user, require_role
from backend.app.models import User

router = APIRouter()


@router.get("", response_model=ApiResponse[KnowledgeListResponse])
def get_knowledge_list(
    category_id: Optional[int] = Query(None, description="分类ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    review_status: Optional[str] = Query(None, description="复核状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词（标题或内容）"),
    review_expiry_status: Optional[str] = Query(None, description="复核到期状态：normal/upcoming/overdue"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = KnowledgeService.get_knowledge_list(
        db, category_id, page, page_size, current_user.id, review_status, keyword, review_expiry_status
    )
    return ApiResponse(data=result)


@router.get("/my", response_model=ApiResponse[KnowledgeListResponse])
def get_my_knowledge(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    review_expiry_status: Optional[str] = Query(None, description="复核到期状态：normal/upcoming/overdue"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["employee", "supervisor"]))
):
    result = KnowledgeService.get_my_knowledge(db, current_user.id, page, page_size, review_expiry_status)
    return ApiResponse(data=result)


@router.get("/{knowledge_id}", response_model=ApiResponse[KnowledgeResponse])
def get_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = KnowledgeService.get_knowledge_by_id(db, knowledge_id, current_user.id)
    return ApiResponse(data=result)


@router.post("", response_model=ApiResponse[KnowledgeResponse])
def create_knowledge(
    knowledge_data: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["employee", "supervisor"]))
):
    knowledge = KnowledgeService.create_knowledge(db, knowledge_data, current_user.id)
    return ApiResponse(data=knowledge, message="提交成功")


@router.put("/{knowledge_id}", response_model=ApiResponse[KnowledgeResponse])
def update_knowledge(
    knowledge_id: int,
    knowledge_data: KnowledgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["employee", "supervisor"]))
):
    knowledge = KnowledgeService.update_knowledge(db, knowledge_id, knowledge_data, current_user.id)
    return ApiResponse(data=knowledge, message="更新成功")


@router.delete("/{knowledge_id}", response_model=ApiResponse)
def delete_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["employee", "supervisor"]))
):
    KnowledgeService.delete_knowledge(db, knowledge_id, current_user.id)
    return ApiResponse(message="删除成功")
