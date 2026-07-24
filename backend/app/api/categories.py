from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.database import get_db
from backend.app.schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeNode,
    CategoryMoveRequest, CategoryMergeRequest, CategoryCopyRequest,
    ApiResponse
)
from backend.app.services import CategoryService
from backend.app.utils.security import get_current_user, require_role
from backend.app.models import User

router = APIRouter()


@router.get("", response_model=ApiResponse)
def get_categories(
    include_inactive: bool = Query(False, description="是否包含已停用节点"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tree = CategoryService.get_all_categories(db, include_inactive)
    return ApiResponse(data=tree)


@router.get("/{category_id}", response_model=ApiResponse[CategoryResponse])
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = CategoryService.get_category_by_id(db, category_id)
    return ApiResponse(data=category)


@router.get("/list", response_model=ApiResponse)
def get_category_list(
    group_id: Optional[int] = Query(None, description="小组ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = CategoryService.get_category_list(db, group_id)
    return ApiResponse(data=categories)


@router.post("", response_model=ApiResponse[CategoryResponse])
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    category = CategoryService.create_category(db, category_data)
    return ApiResponse(data=category, message="创建成功")


@router.put("/{category_id}", response_model=ApiResponse[CategoryResponse])
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    category = CategoryService.update_category(db, category_id, category_data)
    return ApiResponse(data=category, message="更新成功")


@router.delete("/{category_id}", response_model=ApiResponse)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    CategoryService.delete_category(db, category_id)
    return ApiResponse(message="删除成功")


@router.post("/{category_id}/move", response_model=ApiResponse[CategoryResponse])
def move_category(
    category_id: int,
    move_data: CategoryMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    category = CategoryService.move_category(db, category_id, move_data.target_parent_id)
    return ApiResponse(data=category, message="移动成功")


@router.post("/{category_id}/merge", response_model=ApiResponse)
def merge_category(
    category_id: int,
    merge_data: CategoryMergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    CategoryService.merge_category(db, category_id, merge_data.target_category_id)
    return ApiResponse(message="合并成功")


@router.post("/{category_id}/copy", response_model=ApiResponse)
def copy_category(
    category_id: int,
    copy_data: CategoryCopyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    result = CategoryService.copy_category(
        db, category_id, copy_data.target_group_id, copy_data.target_parent_id
    )
    return ApiResponse(data=result, message="复制成功")


@router.post("/{category_id}/deactivate", response_model=ApiResponse[CategoryResponse])
def deactivate_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    category = CategoryService.deactivate_category(db, category_id)
    return ApiResponse(data=category, message="停用成功")
