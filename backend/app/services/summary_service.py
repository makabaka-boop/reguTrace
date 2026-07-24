from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status
from typing import List, Dict
from backend.app.models import NodeSummary, Category


class SummaryService:
    @staticmethod
    def get_node_summary(db: Session, node_id: int, user_id: int) -> Dict:
        category = db.query(Category).filter(Category.id == node_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类节点不存在"
            )
        
        sql = text("""
            SELECT 
                COALESCE(ns.total_count, 0) as total_count,
                COALESCE(ns.pending_count, 0) as pending_count,
                COUNT(DISTINCT CASE WHEN rs.id IS NULL AND k.review_status != 'rejected' THEN k.id END) as unread_count,
                ns.updated_at
            FROM categories c
            LEFT JOIN node_summaries ns ON c.id = ns.category_id
            LEFT JOIN categories desc_cat ON desc_cat.id = c.id OR desc_cat.path LIKE c.path || '/%'
            LEFT JOIN knowledge k ON k.category_id = desc_cat.id AND k.review_status != 'rejected'
            LEFT JOIN reading_status rs ON rs.knowledge_id = k.id AND rs.user_id = :user_id
            WHERE c.id = :node_id
            GROUP BY c.id, ns.total_count, ns.pending_count, ns.updated_at
        """)
        
        result = db.execute(sql, {"node_id": node_id, "user_id": user_id}).fetchone()
        
        if not result:
            return {
                "category_id": node_id,
                "total_count": 0,
                "unread_count": 0,
                "pending_count": 0,
                "updated_at": None
            }
        
        return {
            "category_id": node_id,
            "total_count": result.total_count or 0,
            "unread_count": result.unread_count or 0,
            "pending_count": result.pending_count or 0,
            "updated_at": result.updated_at
        }

    @staticmethod
    def get_all_nodes_summary(db: Session, user_id: int) -> List[Dict]:
        sql = text("""
            SELECT 
                c.id as category_id,
                COALESCE(ns.total_count, 0) as total_count,
                COALESCE(ns.pending_count, 0) as pending_count,
                COUNT(DISTINCT CASE WHEN rs.id IS NULL AND k.review_status != 'rejected' THEN k.id END) as unread_count,
                ns.updated_at
            FROM categories c
            LEFT JOIN node_summaries ns ON c.id = ns.category_id
            LEFT JOIN categories desc_cat ON desc_cat.id = c.id OR desc_cat.path LIKE c.path || '/%'
            LEFT JOIN knowledge k ON k.category_id = desc_cat.id AND k.review_status != 'rejected'
            LEFT JOIN reading_status rs ON rs.knowledge_id = k.id AND rs.user_id = :user_id
            WHERE c.is_active = 1
            GROUP BY c.id, ns.total_count, ns.pending_count, ns.updated_at
            ORDER BY c.path
        """)
        
        results = db.execute(sql, {"user_id": user_id}).fetchall()
        
        return [
            {
                "category_id": row.category_id,
                "total_count": row.total_count or 0,
                "unread_count": row.unread_count or 0,
                "pending_count": row.pending_count or 0,
                "updated_at": row.updated_at
            }
            for row in results
        ]

    @staticmethod
    def rebuild_all_summaries(db: Session):
        db.execute(text("DELETE FROM node_summaries"))
        
        sql = text("""
            INSERT INTO node_summaries (category_id, total_count, pending_count, updated_at)
            SELECT 
                c.id,
                (SELECT COUNT(*) FROM knowledge k 
                 INNER JOIN categories cat ON k.category_id = cat.id 
                 WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
                 AND k.review_status != 'rejected'),
                (SELECT COUNT(*) FROM knowledge k 
                 INNER JOIN categories cat ON k.category_id = cat.id 
                 WHERE (cat.id = c.id OR cat.path LIKE c.path || '/%')
                 AND k.review_status = 'pending'),
                CURRENT_TIMESTAMP
            FROM categories c
        """)
        
        db.execute(sql)
        db.commit()
        
        return {"message": "汇总数据已重建"}
