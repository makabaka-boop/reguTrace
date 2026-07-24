from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.database import get_db
from backend.app.schemas import (
    ReviewRequest, ReviewBatchRequest, KnowledgeResponse,
    KnowledgeListResponse, ApiResponse
)
from backend.app.services import ReviewService
from backend.app.utils.security import get_current_user, require_role
from backend.app.models import User

router = APIRouter()


@router.get("/statistics", response_model=ApiResponse)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    result = ReviewService.get_statistics(db)
    return ApiResponse(data=result)


@router.get("/pending", response_model=ApiResponse[KnowledgeListResponse])
def get_pending_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    review_expiry_status: Optional[str] = Query(None, description="复核到期状态：normal/upcoming/overdue"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    result = ReviewService.get_pending_list(db, page, page_size, review_expiry_status)
    return ApiResponse(data=result)


@router.post("/{knowledge_id}/approve", response_model=ApiResponse[KnowledgeResponse])
def approve_knowledge(
    knowledge_id: int,
    review_data: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    knowledge = ReviewService.approve_knowledge(db, knowledge_id, current_user.id, review_data)
    return ApiResponse(data=knowledge, message="复核通过")


@router.post("/{knowledge_id}/reject", response_model=ApiResponse[KnowledgeResponse])
def reject_knowledge(
    knowledge_id: int,
    review_data: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    knowledge = ReviewService.reject_knowledge(db, knowledge_id, current_user.id, review_data)
    return ApiResponse(data=knowledge, message="复核驳回")


@router.post("/batch-approve", response_model=ApiResponse)
def batch_approve(
    batch_data: ReviewBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    result = ReviewService.batch_approve(db, current_user.id, batch_data)
    return ApiResponse(data=result, message="批量通过成功")


@router.post("/batch-reject", response_model=ApiResponse)
def batch_reject(
    batch_data: ReviewBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    result = ReviewService.batch_reject(db, current_user.id, batch_data)
    return ApiResponse(data=result, message="批量驳回成功")
