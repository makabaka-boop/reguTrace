from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from backend.app.models import Knowledge, ReviewRecord, Category
from backend.app.schemas import ReviewRequest, ReviewBatchRequest
from backend.app.services.knowledge_service import calculate_next_review_date, get_review_expiry_status


class ReviewService:
    @staticmethod
    def get_pending_list(db: Session, page: int = 1, page_size: int = 10, review_expiry_status: Optional[str] = None):
        query = db.query(Knowledge).filter(Knowledge.review_status == "pending")
        
        if review_expiry_status:
            now = datetime.now()
            if review_expiry_status == 'overdue':
                query = query.filter(
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date < now
                )
            elif review_expiry_status == 'upcoming':
                thirty_days_later = now + timedelta(days=30)
                query = query.filter(
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date >= now,
                    Knowledge.next_review_date <= thirty_days_later
                )
            elif review_expiry_status == 'normal':
                thirty_days_later = now + timedelta(days=30)
                query = query.filter(
                    Knowledge.next_review_date.isnot(None),
                    Knowledge.next_review_date > thirty_days_later
                )
        
        total = query.count()
        items = query.order_by(Knowledge.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()
        
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
    def approve_knowledge(db: Session, knowledge_id: int, reviewer_id: int, review_data: ReviewRequest):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="制度条目不存在"
            )
        
        if knowledge.review_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该制度条目已复核"
            )
        
        if review_data.new_category_id is not None:
            category = db.query(Category).filter(Category.id == review_data.new_category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="新制度目录不存在"
                )
            knowledge.category_id = review_data.new_category_id
        
        knowledge.review_status = "approved"
        knowledge.reject_reason = None
        
        next_review = calculate_next_review_date(knowledge.suggested_review_cycle)
        knowledge.next_review_date = next_review
        
        review_record = ReviewRecord(
            knowledge_id=knowledge_id,
            reviewer_id=reviewer_id,
            action="approve",
            remark=review_data.remark
        )
        db.add(review_record)
        
        db.commit()
        db.refresh(knowledge)
        return knowledge

    @staticmethod
    def reject_knowledge(db: Session, knowledge_id: int, reviewer_id: int, review_data: ReviewRequest):
        knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="制度条目不存在"
            )
        
        if knowledge.review_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该制度条目已复核"
            )
        
        knowledge.review_status = "rejected"
        knowledge.reject_reason = review_data.remark
        
        review_record = ReviewRecord(
            knowledge_id=knowledge_id,
            reviewer_id=reviewer_id,
            action="reject",
            remark=review_data.remark
        )
        db.add(review_record)
        
        db.commit()
        db.refresh(knowledge)
        return knowledge

    @staticmethod
    def batch_approve(db: Session, reviewer_id: int, batch_data: ReviewBatchRequest):
        for kid in batch_data.knowledge_ids:
            try:
                knowledge = db.query(Knowledge).filter(Knowledge.id == kid).first()
                if knowledge and knowledge.review_status == "pending":
                    knowledge.review_status = "approved"
                    knowledge.reject_reason = None
                    
                    next_review = calculate_next_review_date(knowledge.suggested_review_cycle)
                    knowledge.next_review_date = next_review
                    
                    review_record = ReviewRecord(
                        knowledge_id=kid,
                        reviewer_id=reviewer_id,
                        action="approve",
                        remark=batch_data.remark
                    )
                    db.add(review_record)
            except Exception as e:
                continue
        
        db.commit()
        return {"message": f"批量通过 {len(batch_data.knowledge_ids)} 条记录"}

    @staticmethod
    def batch_reject(db: Session, reviewer_id: int, batch_data: ReviewBatchRequest):
        for kid in batch_data.knowledge_ids:
            try:
                knowledge = db.query(Knowledge).filter(Knowledge.id == kid).first()
                if knowledge and knowledge.review_status == "pending":
                    knowledge.review_status = "rejected"
                    knowledge.reject_reason = batch_data.remark
                    
                    review_record = ReviewRecord(
                        knowledge_id=kid,
                        reviewer_id=reviewer_id,
                        action="reject",
                        remark=batch_data.remark
                    )
                    db.add(review_record)
            except Exception as e:
                continue
        
        db.commit()
        return {"message": f"批量驳回 {len(batch_data.knowledge_ids)} 条记录"}

    @staticmethod
    def get_statistics(db: Session):
        pending_count = db.query(Knowledge).filter(Knowledge.review_status == "pending").count()
        approved_count = db.query(Knowledge).filter(Knowledge.review_status == "approved").count()
        rejected_count = db.query(Knowledge).filter(Knowledge.review_status == "rejected").count()
        
        now = datetime.now()
        thirty_days_later = now + timedelta(days=30)
        
        upcoming_count = db.query(Knowledge).filter(
            Knowledge.review_status == "approved",
            Knowledge.next_review_date.isnot(None),
            Knowledge.next_review_date >= now,
            Knowledge.next_review_date <= thirty_days_later
        ).count()
        
        overdue_count = db.query(Knowledge).filter(
            Knowledge.review_status == "approved",
            Knowledge.next_review_date.isnot(None),
            Knowledge.next_review_date < now
        ).count()
        
        return {
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "upcoming_count": upcoming_count,
            "overdue_count": overdue_count
        }
