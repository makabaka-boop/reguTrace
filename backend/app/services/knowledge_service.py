from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from backend.app.models import Knowledge, Category, User, ReadingStatus
from backend.app.schemas import KnowledgeCreate, KnowledgeUpdate


def calculate_next_review_date(cycle: str, from_date: Optional[datetime] = None) -> Optional[datetime]:
    if cycle == 'never' or not cycle:
        return None
    base_date = from_date or datetime.now()
    if cycle == '1month':
        return base_date + relativedelta(months=1)
    elif cycle == '3months':
        return base_date + relativedelta(months=3)
    elif cycle == '6months':
        return base_date + relativedelta(months=6)
    elif cycle == '1year':
        return base_date + relativedelta(years=1)
    return None


def get_review_expiry_status(next_review_date: Optional[datetime], review_status: str) -> Optional[str]:
    if review_status != 'approved' or next_review_date is None:
        return None
    now = datetime.now()
    if now > next_review_date:
        return 'overdue'
    elif (next_review_date - now).days <= 30:
        return 'upcoming'
    else:
        return 'normal'


class KnowledgeService:
    @staticmethod
    def get_knowledge_list(
        db: Session,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10,
        user_id: Optional[int] = None,
        review_status: Optional[str] = None,
        keyword: Optional[str] = None,
        review_expiry_status: Optional[str] = None
    ):
        query = db.query(Knowledge).filter(Knowledge.review_status != 'rejected')
        
        if category_id is not None:
            category = db.query(Category).filter(Category.id == category_id).first()
            if category:
                query = query.join(Category).filter(
                    (Category.id == category_id) | 
                    (Category.path.like(f"{category.path}/%"))
                )
        
        if review_status:
            query = query.filter(Knowledge.review_status == review_status)
        
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                (Knowledge.title.like(keyword_pattern)) |
                (Knowledge.content.like(keyword_pattern))
            )
        
        if review_expiry_status:
            now = datetime.now()
            if review_expiry_status == 'overdue':
                query = query.filter(
                    Knowledge.review_status == 'approved',
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date < now
                )
            elif review_expiry_status == 'upcoming':
                thirty_days_later = now + timedelta(days=30)
                query = query.filter(
                    Knowledge.review_status == 'approved',
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date >= now,
                    Knowledge.next_review_date <= thirty_days_later
                )
            elif review_expiry_status == 'normal':
                thirty_days_later = now + timedelta(days=30)
                query = query.filter(
                    Knowledge.review_status == 'approved',
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date > thirty_days_later
                )
        
        total = query.count()
        items = query.order_by(Knowledge.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        result = []
        for item in items:
            is_read = None
            if user_id:
                reading = db.query(ReadingStatus).filter(
                    ReadingStatus.knowledge_id == item.id,
                    ReadingStatus.user_id == user_id
                ).first()
                is_read = reading is not None and reading.is_read
            
            expiry_status = get_review_expiry_status(item.next_review_date, item.review_status)
            
            result.append({
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "submitter_id": item.submitter_id,
                "submitter_name": item.submitter.name if item.submitter else None,
                "review_status": item.review_status,
                "reject_reason": item.reject_reason,
                "is_read": is_read,
                "suggested_review_cycle": item.suggested_review_cycle,
                "next_review_date": item.next_review_date,
                "review_expiry_status": expiry_status,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            })
        
        return {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_knowledge_by_id(db: Session, knowledge_id: int, user_id: Optional[int] = None):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="制度条目不存在"
            )
        
        is_read = None
        if user_id:
            reading = db.query(ReadingStatus).filter(
                ReadingStatus.knowledge_id == knowledge_id,
                ReadingStatus.user_id == user_id
            ).first()
            is_read = reading is not None and reading.is_read
        
        expiry_status = get_review_expiry_status(knowledge.next_review_date, knowledge.review_status)
        
        return {
            "id": knowledge.id,
            "title": knowledge.title,
            "content": knowledge.content,
            "category_id": knowledge.category_id,
            "category_name": knowledge.category.name if knowledge.category else None,
            "submitter_id": knowledge.submitter_id,
            "submitter_name": knowledge.submitter.name if knowledge.submitter else None,
            "review_status": knowledge.review_status,
            "reject_reason": knowledge.reject_reason,
            "is_read": is_read,
            "suggested_review_cycle": knowledge.suggested_review_cycle,
            "next_review_date": knowledge.next_review_date,
            "review_expiry_status": expiry_status,
            "created_at": knowledge.created_at,
            "updated_at": knowledge.updated_at
        }

    @staticmethod
    def create_knowledge(db: Session, knowledge_data: KnowledgeCreate, submitter_id: int):
        category = db.query(Category).filter(Category.id == knowledge_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="制度目录不存在"
            )
        if not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该制度目录已停用"
            )
        
        valid_cycles = ['1month', '3months', '6months', '1year', 'never']
        cycle = knowledge_data.suggested_review_cycle or '6months'
        if cycle not in valid_cycles:
            cycle = '6months'
        
        db_knowledge = Knowledge(
            title=knowledge_data.title,
            content=knowledge_data.content,
            category_id=knowledge_data.category_id,
            submitter_id=submitter_id,
            review_status="pending",
            suggested_review_cycle=cycle
        )
        db.add(db_knowledge)
        db.commit()
        db.refresh(db_knowledge)
        return db_knowledge

    @staticmethod
    def update_knowledge(db: Session, knowledge_id: int, knowledge_data: KnowledgeUpdate, user_id: int):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="制度条目不存在"
            )
        
        if knowledge.submitter_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能编辑自己提交的制度条目"
            )
        
        if knowledge_data.title is not None:
            knowledge.title = knowledge_data.title
        if knowledge_data.content is not None:
            knowledge.content = knowledge_data.content
        if knowledge_data.category_id is not None:
            category = db.query(Category).filter(Category.id == knowledge_data.category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="制度目录不存在"
                )
            if not category.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该制度目录已停用"
                )
            knowledge.category_id = knowledge_data.category_id
        
        if knowledge_data.suggested_review_cycle is not None:
            valid_cycles = ['1month', '3months', '6months', '1year', 'never']
            if knowledge_data.suggested_review_cycle in valid_cycles:
                knowledge.suggested_review_cycle = knowledge_data.suggested_review_cycle
        
        knowledge.review_status = "pending"
        knowledge.reject_reason = None
        
        db.commit()
        db.refresh(knowledge)
        return knowledge

    @staticmethod
    def delete_knowledge(db: Session, knowledge_id: int, user_id: int):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="制度条目不存在"
            )
        
        if knowledge.submitter_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能删除自己提交的制度条目"
            )
        
        db.query(ReadingStatus).filter(ReadingStatus.knowledge_id == knowledge_id).delete()
        
        db.delete(knowledge)
        db.commit()

    @staticmethod
    def get_my_knowledge(db: Session, submitter_id: int, page: int = 1, page_size: int = 10, review_expiry_status: Optional[str] = None):
        query = db.query(Knowledge).filter(Knowledge.submitter_id == submitter_id)
        
        if review_expiry_status:
            now = datetime.now()
            if review_expiry_status == 'overdue':
                query = query.filter(
                    Knowledge.review_status == 'approved',
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date < now
                )
            elif review_expiry_status == 'upcoming':
                thirty_days_later = now + timedelta(days=30)
                query = query.filter(
                    Knowledge.review_status == 'approved',
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date >= now,
                    Knowledge.next_review_date <= thirty_days_later
                )
            elif review_expiry_status == 'normal':
                thirty_days_later = now + timedelta(days=30)
                query = query.filter(
                    Knowledge.review_status == 'approved',
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date > thirty_days_later
                )
        
        total = query.count()
        items = query.order_by(Knowledge.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        result = []
        for item in items:
            expiry_status = get_review_expiry_status(item.next_review_date, item.review_status)
            result.append({
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "submitter_id": item.submitter_id,
                "submitter_name": item.submitter.name if item.submitter else None,
                "review_status": item.review_status,
                "reject_reason": item.reject_reason,
                "is_read": None,
                "suggested_review_cycle": item.suggested_review_cycle,
                "next_review_date": item.next_review_date,
                "review_expiry_status": expiry_status,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            })
        
        return {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_all_for_export(db: Session, category_id: Optional[int] = None, review_status: Optional[str] = None):
        query = db.query(Knowledge).filter(Knowledge.review_status != 'rejected')
        
        if category_id is not None:
            category = db.query(Category).filter(Category.id == category_id).first()
            if category:
                query = query.join(Category).filter(
                    (Category.id == category_id) | 
                    (Category.path.like(f"{category.path}/%"))
                )
        
        if review_status:
            query = query.filter(Knowledge.review_status == review_status)
        
        items = query.order_by(Knowledge.created_at.desc()).all()
        
        result = []
        for item in items:
            result.append({
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category_id": item.category_id,
                "category_name": item.category.name if item.category else None,
                "submitter_id": item.submitter_id,
                "submitter_name": item.submitter.name if item.submitter else None,
                "review_status": item.review_status,
                "reject_reason": item.reject_reason,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            })
        
        return result
