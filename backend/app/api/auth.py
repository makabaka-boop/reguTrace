from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import UserLogin, UserResponse, ApiResponse
from backend.app.services import AuthService
from backend.app.utils.security import get_current_user, require_role
from backend.app.models import User

router = APIRouter()


@router.post("/login", response_model=ApiResponse[UserResponse])
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    result = AuthService.login(db, login_data)
    return ApiResponse(data=result, message="登录成功")


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(data={
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "name": current_user.name,
        "created_at": current_user.created_at
    })


@router.post("/logout", response_model=ApiResponse)
def logout():
    return ApiResponse(message="登出成功")
