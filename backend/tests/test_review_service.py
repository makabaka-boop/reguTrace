import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from backend.app.services.review_service import ReviewService
from backend.app.schemas import ReviewRequest, ReviewBatchRequest


class TestReviewService:

    def test_get_pending_list(self, db, pending_knowledge, approved_knowledge):
        result = ReviewService.get_pending_list(db, page=1, page_size=10)
        assert result["total"] == 1
        assert result["items"][0]["title"] == "员工考勤管理办法"
        assert result["items"][0]["review_status"] == "pending"

    def test_get_pending_list_empty(self, db, approved_knowledge):
        result = ReviewService.get_pending_list(db, page=1, page_size=10)
        assert result["total"] == 0

    def test_approve_knowledge_success(self, db, pending_knowledge, test_supervisor):
        review_data = ReviewRequest(remark="审批通过")
        result = ReviewService.approve_knowledge(db, pending_knowledge.id, test_supervisor.id, review_data)

        assert result.review_status == "approved"
        assert result.reject_reason is None
        assert result.next_review_date is not None

    def test_approve_with_category_change(self, db, pending_knowledge, root_category, test_supervisor):
        review_data = ReviewRequest(new_category_id=root_category.id)
        result = ReviewService.approve_knowledge(db, pending_knowledge.id, test_supervisor.id, review_data)
        assert result.category_id == root_category.id

    def test_approve_already_approved(self, db, approved_knowledge, test_supervisor):
        review_data = ReviewRequest()
        with pytest.raises(HTTPException) as exc_info:
            ReviewService.approve_knowledge(db, approved_knowledge.id, test_supervisor.id, review_data)
        assert exc_info.value.status_code == 400
        assert "已复核" in exc_info.value.detail

    def test_approve_nonexistent_knowledge(self, db, test_supervisor):
        review_data = ReviewRequest()
        with pytest.raises(HTTPException) as exc_info:
            ReviewService.approve_knowledge(db, 99999, test_supervisor.id, review_data)
        assert exc_info.value.status_code == 404

    def test_reject_knowledge_success(self, db, pending_knowledge, test_supervisor):
        review_data = ReviewRequest(remark="内容不完善，请补充")
        result = ReviewService.reject_knowledge(db, pending_knowledge.id, test_supervisor.id, review_data)

        assert result.review_status == "rejected"
        assert result.reject_reason == "内容不完善，请补充"

    def test_reject_already_processed(self, db, approved_knowledge, test_supervisor):
        review_data = ReviewRequest(remark="test")
        with pytest.raises(HTTPException) as exc_info:
            ReviewService.reject_knowledge(db, approved_knowledge.id, test_supervisor.id, review_data)
        assert exc_info.value.status_code == 400

    def test_batch_approve(self, db, pending_knowledge, test_supervisor, child_category, test_employee):
        from backend.app.models import Knowledge
        k2 = Knowledge(
            title="第二条待审",
            content="内容2",
            category_id=child_category.id,
            submitter_id=test_employee.id,
            review_status="pending",
            suggested_review_cycle="6months"
        )
        db.add(k2)
        db.commit()
        db.refresh(k2)

        batch_data = ReviewBatchRequest(knowledge_ids=[pending_knowledge.id, k2.id], remark="批量通过")
        result = ReviewService.batch_approve(db, test_supervisor.id, batch_data)
        assert "批量通过" in result["message"]

        db.refresh(pending_knowledge)
        db.refresh(k2)
        assert pending_knowledge.review_status == "approved"
        assert k2.review_status == "approved"

    def test_batch_reject(self, db, pending_knowledge, test_supervisor, child_category, test_employee):
        from backend.app.models import Knowledge
        k2 = Knowledge(
            title="第二条待审",
            content="内容2",
            category_id=child_category.id,
            submitter_id=test_employee.id,
            review_status="pending",
            suggested_review_cycle="6months"
        )
        db.add(k2)
        db.commit()
        db.refresh(k2)

        batch_data = ReviewBatchRequest(knowledge_ids=[pending_knowledge.id, k2.id], remark="批量驳回")
        result = ReviewService.batch_reject(db, test_supervisor.id, batch_data)
        assert "批量驳回" in result["message"]

        db.refresh(pending_knowledge)
        db.refresh(k2)
        assert pending_knowledge.review_status == "rejected"
        assert k2.review_status == "rejected"

    def test_get_statistics_empty(self, db):
        stats = ReviewService.get_statistics(db)
        assert stats["pending_count"] == 0
        assert stats["approved_count"] == 0
        assert stats["rejected_count"] == 0
        assert stats["overdue_count"] == 0
        assert stats["upcoming_count"] == 0

    def test_get_statistics_with_data(self, db, pending_knowledge, approved_knowledge, rejected_knowledge, overdue_knowledge, upcoming_knowledge):
        stats = ReviewService.get_statistics(db)
        assert stats["pending_count"] == 1
        assert stats["approved_count"] == 3
        assert stats["rejected_count"] == 1
        assert stats["overdue_count"] == 1
        assert stats["upcoming_count"] == 1

    def test_approve_sets_correct_next_review_date(self, db, pending_knowledge, test_supervisor):
        pending_knowledge.suggested_review_cycle = "1year"
        db.commit()

        review_data = ReviewRequest()
        result = ReviewService.approve_knowledge(db, pending_knowledge.id, test_supervisor.id, review_data)

        expected = datetime.now() + timedelta(days=365)
        assert result.next_review_date is not None
        diff = abs((result.next_review_date - expected).total_seconds())
        assert diff < 5
