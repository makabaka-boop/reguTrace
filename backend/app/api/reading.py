from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.database import get_db
from backend.app.schemas import ApiResponse
from backend.app.services import ReadingService
from backend.app.utils.security import get_current_user, require_role
from backend.app.models import User

router = APIRouter()


@router.get("/my-status", response_model=ApiResponse)
def get_my_reading_status(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    review_expiry_status: Optional[str] = Query(None, description="复核到期状态：normal/upcoming/overdue"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["employee", "supervisor", "admin"]))
):
    result = ReadingService.get_my_reading_status(db, current_user.id, page, page_size, review_expiry_status)
    return ApiResponse(data=result)


@router.post("/{knowledge_id}", response_model=ApiResponse)
def mark_as_read(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = ReadingService.mark_as_read(db, knowledge_id, current_user.id)
    return ApiResponse(data=result, message="标记已读成功")


@router.delete("/{knowledge_id}", response_model=ApiResponse)
def mark_as_unread(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = ReadingService.mark_as_unread(db, knowledge_id, current_user.id)
    return ApiResponse(data=result, message="标记未读成功")
