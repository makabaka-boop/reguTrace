from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.database import get_db
from backend.app.services import KnowledgeService
from backend.app.utils.security import require_role
from backend.app.utils.export import export_knowledge_to_excel
from backend.app.models import User
from datetime import datetime

router = APIRouter()


@router.get("/knowledge")
def export_knowledge(
    category_id: Optional[int] = Query(None, description="分类ID"),
    review_status: Optional[str] = Query(None, description="复核状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["supervisor", "admin"]))
):
    data = KnowledgeService.get_all_for_export(db, category_id, review_status)
    excel_file = export_knowledge_to_excel(data)
    
    filename = f"知识清单_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
