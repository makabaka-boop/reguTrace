from fastapi import APIRouter
from .auth import router as auth_router
from .categories import router as categories_router
from .knowledge import router as knowledge_router
from .reading import router as reading_router
from .review import router as review_router
from .summary import router as summary_router
from .groups import router as groups_router
from .export import router as export_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(categories_router, prefix="/categories", tags=["分类树"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["制度条目"])
api_router.include_router(reading_router, prefix="/reading", tags=["阅读状态"])
api_router.include_router(review_router, prefix="/review", tags=["到期复核"])
api_router.include_router(summary_router, prefix="/summary", tags=["阅读与复核汇总"])
api_router.include_router(groups_router, prefix="/groups", tags=["责任小组"])
api_router.include_router(export_router, prefix="/export", tags=["数据导出"])
