from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "企业制度知识复核与阅读追踪系统"
    BACKEND_PORT: int = 8009
    FRONTEND_PORT: int = 8079

    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    DATABASE_URL: str = "sqlite:///./knowledge_base.db"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
