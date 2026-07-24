from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import ApiResponse
from backend.app.models import UserGroup, GroupMember, User
from backend.app.utils.security import get_current_user, require_role
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter()


class GroupCreate(BaseModel):
    name: str = Field(..., description="小组名称")
    description: Optional[str] = Field(None, description="小组描述")


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, description="小组名称")
    description: Optional[str] = Field(None, description="小组描述")


class MemberAdd(BaseModel):
    user_id: int = Field(..., description="用户ID")


def serialize_group(group: UserGroup):
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "created_at": group.created_at,
        "updated_at": group.updated_at,
    }


@router.get("", response_model=ApiResponse)
def get_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    groups = db.query(UserGroup).all()
    result = []
    for group in groups:
        members = db.query(GroupMember).filter(GroupMember.group_id == group.id).all()
        member_ids = [m.user_id for m in members]
        users = db.query(User).filter(User.id.in_(member_ids)).all()
        member_list = [{"id": u.id, "name": u.name, "username": u.username, "role": u.role} for u in users]
        result.append({
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "members": member_list
        })
    return ApiResponse(data=result)


@router.post("", response_model=ApiResponse)
def create_group(
    group_data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    group = UserGroup(name=group_data.name, description=group_data.description)
    db.add(group)
    db.commit()
    db.refresh(group)
    return ApiResponse(data=serialize_group(group), message="创建成功")


@router.put("/{group_id}", response_model=ApiResponse)
def update_group(
    group_id: int,
    group_data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        return ApiResponse(code=404, message="小组不存在")
    
    if group_data.name:
        group.name = group_data.name
    if group_data.description:
        group.description = group_data.description
    
    db.commit()
    db.refresh(group)
    return ApiResponse(data=serialize_group(group), message="更新成功")


@router.delete("/{group_id}", response_model=ApiResponse)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        return ApiResponse(code=404, message="小组不存在")
    
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    db.delete(group)
    db.commit()
    return ApiResponse(message="删除成功")


@router.post("/{group_id}/members", response_model=ApiResponse)
def add_member(
    group_id: int,
    member_data: MemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    group = db.query(UserGroup).filter(UserGroup.id == group_id).first()
    if not group:
        return ApiResponse(code=404, message="小组不存在")
    
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        return ApiResponse(code=404, message="用户不存在")
    
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == member_data.user_id
    ).first()
    
    if existing:
        return ApiResponse(code=400, message="用户已在小组中")
    
    member = GroupMember(group_id=group_id, user_id=member_data.user_id)
    db.add(member)
    db.commit()
    return ApiResponse(message="添加成功")


@router.delete("/{group_id}/members/{user_id}", response_model=ApiResponse)
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    
    if not member:
        return ApiResponse(code=404, message="成员不存在")
    
    db.delete(member)
    db.commit()
    return ApiResponse(message="移除成功")
