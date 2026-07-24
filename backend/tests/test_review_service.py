"""复核统计服务单元测试：待复核列表、通过/驳回、批量复核、统计与到期计算。"""
from datetime import datetime

import pytest
from fastapi import HTTPException

from backend.app.services.review_service import ReviewService
from backend.app.schemas import ReviewRequest, ReviewBatchRequest
from backend.app.models import ReviewRecord


class TestGetPendingList:
    def test_returns_only_pending(self, db_session, knowledge_set):
        result = ReviewService.get_pending_list(db_session, page_size=50)
        assert result["total"] == 1
        assert result["items"][0]["title"] == "待复核制度"


class TestApproveKnowledge:
    def test_approve_sets_status_and_next_review_date(self, db_session, knowledge_set, users):
        target = knowledge_set["pending"]
        updated = ReviewService.approve_knowledge(
            db_session, target.id, users["supervisor"].id, ReviewRequest(remark="通过")
        )
        assert updated.review_status == "approved"
        assert updated.reject_reason is None
        # cycle 默认 6months，应计算出下次复核时间
        assert updated.next_review_date is not None
        assert updated.next_review_date > datetime.now()

    def test_approve_records_review_action(self, db_session, knowledge_set, users):
        target = knowledge_set["pending"]
        ReviewService.approve_knowledge(
            db_session, target.id, users["supervisor"].id, ReviewRequest()
        )
        record = db_session.query(ReviewRecord).filter(
            ReviewRecord.knowledge_id == target.id
        ).first()
        assert record is not None and record.action == "approve"

    def test_approve_with_new_category(self, db_session, knowledge_set, users, categories):
        target = knowledge_set["pending"]
        updated = ReviewService.approve_knowledge(
            db_session, target.id, users["supervisor"].id,
            ReviewRequest(new_category_id=categories["root"].id),
        )
        assert updated.category_id == categories["root"].id

    def test_approve_nonexistent_raises_404(self, db_session, users):
        with pytest.raises(HTTPException) as exc:
            ReviewService.approve_knowledge(db_session, 99999, users["supervisor"].id, ReviewRequest())
        assert exc.value.status_code == 404

    def test_approve_already_reviewed_raises_400(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]  # 已 approved
        with pytest.raises(HTTPException) as exc:
            ReviewService.approve_knowledge(db_session, target.id, users["supervisor"].id, ReviewRequest())
        assert exc.value.status_code == 400

    def test_approve_new_category_not_found_raises_404(self, db_session, knowledge_set, users):
        target = knowledge_set["pending"]
        with pytest.raises(HTTPException) as exc:
            ReviewService.approve_knowledge(
                db_session, target.id, users["supervisor"].id,
                ReviewRequest(new_category_id=99999),
            )
        assert exc.value.status_code == 404


class TestRejectKnowledge:
    def test_reject_sets_status_and_reason(self, db_session, knowledge_set, users):
        target = knowledge_set["pending"]
        updated = ReviewService.reject_knowledge(
            db_session, target.id, users["supervisor"].id, ReviewRequest(remark="不合规")
        )
        assert updated.review_status == "rejected"
        assert updated.reject_reason == "不合规"

    def test_reject_already_reviewed_raises_400(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]
        with pytest.raises(HTTPException) as exc:
            ReviewService.reject_knowledge(db_session, target.id, users["supervisor"].id, ReviewRequest())
        assert exc.value.status_code == 400


class TestBatchReview:
    def test_batch_approve_only_pending(self, db_session, knowledge_set, users, make_knowledge):
        p2 = make_knowledge(title="待复核2", category=knowledge_set["pending"].category,
                            submitter=users["employee"], review_status="pending")
        ids = [knowledge_set["pending"].id, p2.id, knowledge_set["normal"].id]
        result = ReviewService.batch_approve(
            db_session, users["supervisor"].id, ReviewBatchRequest(knowledge_ids=ids, remark="批量")
        )
        assert "批量通过" in result["message"]
        db_session.refresh(knowledge_set["pending"])
        db_session.refresh(p2)
        assert knowledge_set["pending"].review_status == "approved"
        assert p2.review_status == "approved"

    def test_batch_reject_only_pending(self, db_session, knowledge_set, users):
        ids = [knowledge_set["pending"].id, knowledge_set["normal"].id]
        ReviewService.batch_reject(
            db_session, users["supervisor"].id, ReviewBatchRequest(knowledge_ids=ids, remark="批量驳回")
        )
        db_session.refresh(knowledge_set["pending"])
        db_session.refresh(knowledge_set["normal"])
        assert knowledge_set["pending"].review_status == "rejected"
        # 已 approved 的不受影响
        assert knowledge_set["normal"].review_status == "approved"


class TestGetStatistics:
    def test_counts_by_status_and_expiry(self, db_session, knowledge_set):
        stats = ReviewService.get_statistics(db_session)
        # knowledge_set: 3 approved(overdue/upcoming/normal) + 1 pending + 1 rejected
        assert stats["pending_count"] == 1
        assert stats["approved_count"] == 3
        assert stats["rejected_count"] == 1
        assert stats["overdue_count"] == 1
        assert stats["upcoming_count"] == 1
