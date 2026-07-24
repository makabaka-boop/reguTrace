from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta
from backend.app.models import User
from backend.app.schemas import UserLogin, UserCreate
from backend.app.utils.security import verify_password, create_access_token, hash_password
from backend.app.config import settings


class AuthService:
    @staticmethod
    def login(db: Session, login_data: UserLogin):
        user = db.query(User).filter(User.username == login_data.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        if user.role != login_data.role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="角色不匹配"
            )
        
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "name": user.name,
            "created_at": user.created_at,
            "token": access_token
        }

    @staticmethod
    def create_user(db: Session, user_data: UserCreate):
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        db_user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
            name=user_data.name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_current_user_info(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user
