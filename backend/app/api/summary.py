from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import NodeSummaryResponse, ApiResponse
from backend.app.services import SummaryService
from backend.app.utils.security import get_current_user, require_role
from backend.app.models import User

router = APIRouter()


@router.get("/node/{node_id}", response_model=ApiResponse[NodeSummaryResponse])
def get_node_summary(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = SummaryService.get_node_summary(db, node_id, current_user.id)
    return ApiResponse(data=result)


@router.get("/all-nodes", response_model=ApiResponse)
def get_all_nodes_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = SummaryService.get_all_nodes_summary(db, current_user.id)
    return ApiResponse(data=result)


@router.post("/rebuild", response_model=ApiResponse)
def rebuild_summaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    result = SummaryService.rebuild_all_summaries(db)
    return ApiResponse(data=result, message="重建成功")
