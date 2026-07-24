from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Optional
from backend.app.models import ReadingStatus, Knowledge
from backend.app.services.knowledge_service import get_review_expiry_status


class ReadingService:
    @staticmethod
    def mark_as_read(db: Session, knowledge_id: int, user_id: int):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="制度条目不存在"
            )
        
        existing = db.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == knowledge_id,
            ReadingStatus.user_id == user_id
        ).first()
        
        if existing:
            existing.is_read = True
            existing.read_at = datetime.now()
        else:
            reading = ReadingStatus(
                knowledge_id=knowledge_id,
                user_id=user_id,
                is_read=True,
                read_at=datetime.now()
            )
            db.add(reading)
        
        db.commit()
        return {"message": "标记已读成功"}

    @staticmethod
    def mark_as_unread(db: Session, knowledge_id: int, user_id: int):
        reading = db.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == knowledge_id,
            ReadingStatus.user_id == user_id
        ).first()
        
        if reading:
            db.delete(reading)
            db.commit()
        
        return {"message": "标记未读成功"}

    @staticmethod
    def get_my_reading_status(db: Session, user_id: int, page: int = 1, page_size: int = 10, review_expiry_status: Optional[str] = None):
        query = db.query(ReadingStatus).filter(
            ReadingStatus.user_id == user_id,
            ReadingStatus.is_read == True
        ).join(Knowledge)
        
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
        items = query.order_by(ReadingStatus.read_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        result = []
        for item in items:
            expiry_status = get_review_expiry_status(item.knowledge.next_review_date, item.knowledge.review_status) if item.knowledge else None
            result.append({
                "id": item.id,
                "knowledge_id": item.knowledge_id,
                "knowledge_title": item.knowledge.title if item.knowledge else None,
                "user_id": item.user_id,
                "is_read": item.is_read,
                "read_at": item.read_at,
                "review_status": item.knowledge.review_status if item.knowledge else None,
                "suggested_review_cycle": item.knowledge.suggested_review_cycle if item.knowledge else None,
                "next_review_date": item.knowledge.next_review_date if item.knowledge else None,
                "review_expiry_status": expiry_status
            })
        
        return {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size
        }
