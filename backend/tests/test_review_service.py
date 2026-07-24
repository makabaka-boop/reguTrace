from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend.app.models import ReviewRecord
from backend.app.schemas import ReviewRequest, ReviewBatchRequest
from backend.app.services.review_service import ReviewService


class TestPendingList:
    def test_pending_list_only_pending(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        user = make_user()
        k1 = make_knowledge(title="待审", category_id=cat.id, submitter_id=user.id, review_status="pending")
        k2 = make_knowledge(title="已通过", category_id=cat.id, submitter_id=user.id, review_status="approved")

        result = ReviewService.get_pending_list(db)
        ids = {item["id"] for item in result["items"]}
        assert k1.id in ids
        assert k2.id not in ids

    def test_pending_list_pagination(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        user = make_user()
        for i in range(3):
            make_knowledge(title=f"p{i}", category_id=cat.id, submitter_id=user.id, review_status="pending")

        page1 = ReviewService.get_pending_list(db, page=1, page_size=2)
        assert len(page1["items"]) == 2
        assert page1["total"] == 3


class TestApprove:
    def test_approve_sets_approved_and_next_review(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        submitter = make_user(username="sub")
        reviewer = make_user(username="rev", role="supervisor", name="主管")
        k = make_knowledge(
            title="待审",
            category_id=cat.id,
            submitter_id=submitter.id,
            review_status="pending",
            suggested_review_cycle="3months",
        )

        req = ReviewRequest(remark="ok")
        updated = ReviewService.approve_knowledge(db, k.id, reviewer.id, req)

        assert updated.review_status == "approved"
        assert updated.reject_reason is None
        assert updated.next_review_date is not None
        delta = updated.next_review_date - datetime.now()
        assert timedelta(days=80) < delta < timedelta(days=100)

        record = (
            db.query(ReviewRecord)
            .filter(ReviewRecord.knowledge_id == k.id)
            .first()
        )
        assert record is not None
        assert record.action == "approve"
        assert record.reviewer_id == reviewer.id
        assert record.remark == "ok"

    def test_approve_with_new_category(
        self, db, make_category, make_user, make_knowledge
    ):
        c1 = make_category(name="原分类")
        c2 = make_category(name="新分类")
        submitter = make_user(username="sub")
        reviewer = make_user(username="rev", role="supervisor", name="主管")
        k = make_knowledge(category_id=c1.id, submitter_id=submitter.id, review_status="pending")

        req = ReviewRequest(new_category_id=c2.id)
        updated = ReviewService.approve_knowledge(db, k.id, reviewer.id, req)
        assert updated.category_id == c2.id

    def test_approve_not_found(self, db, make_user):
        reviewer = make_user(role="supervisor", name="主管")
        with pytest.raises(HTTPException) as exc:
            ReviewService.approve_knowledge(db, 99999, reviewer.id, ReviewRequest())
        assert exc.value.status_code == 404

    def test_approve_already_reviewed(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        submitter = make_user(username="sub1")
        reviewer = make_user(username="rev1", role="supervisor")
        k = make_knowledge(category_id=cat.id, submitter_id=submitter.id, review_status="approved")

        with pytest.raises(HTTPException) as exc:
            ReviewService.approve_knowledge(db, k.id, reviewer.id, ReviewRequest())
        assert exc.value.status_code == 400
        assert "已复核" in exc.value.detail


class TestReject:
    def test_reject_sets_rejected_and_reason(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        submitter = make_user(username="sub")
        reviewer = make_user(username="rev", role="supervisor")
        k = make_knowledge(category_id=cat.id, submitter_id=submitter.id, review_status="pending")

        req = ReviewRequest(remark="内容不符")
        updated = ReviewService.reject_knowledge(db, k.id, reviewer.id, req)
        assert updated.review_status == "rejected"
        assert updated.reject_reason == "内容不符"

        record = (
            db.query(ReviewRecord)
            .filter(ReviewRecord.knowledge_id == k.id)
            .first()
        )
        assert record.action == "reject"


class TestBatchOperations:
    def test_batch_approve(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        submitter = make_user(username="sub")
        reviewer = make_user(username="rev", role="supervisor")
        k1 = make_knowledge(title="a", category_id=cat.id, submitter_id=submitter.id, review_status="pending")
        k2 = make_knowledge(title="b", category_id=cat.id, submitter_id=submitter.id, review_status="pending")
        k3 = make_knowledge(title="c", category_id=cat.id, submitter_id=submitter.id, review_status="approved")

        req = ReviewBatchRequest(knowledge_ids=[k1.id, k2.id, k3.id], remark="批量")
        result = ReviewService.batch_approve(db, reviewer.id, req)
        assert "批量通过" in result["message"]

        db.refresh(k1)
        db.refresh(k2)
        db.refresh(k3)
        assert k1.review_status == "approved"
        assert k2.review_status == "approved"
        assert k3.review_status == "approved"

    def test_batch_reject(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        submitter = make_user(username="sub2")
        reviewer = make_user(username="rev2", role="supervisor")
        k1 = make_knowledge(category_id=cat.id, submitter_id=submitter.id, review_status="pending")
        k2 = make_knowledge(category_id=cat.id, submitter_id=submitter.id, review_status="pending")

        req = ReviewBatchRequest(knowledge_ids=[k1.id, k2.id], remark="批量驳回")
        result = ReviewService.batch_reject(db, reviewer.id, req)
        assert "批量驳回" in result["message"]

        db.refresh(k1)
        db.refresh(k2)
        assert k1.review_status == "rejected"
        assert k2.review_status == "rejected"


class TestStatistics:
    def test_statistics_counts(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        user = make_user()
        make_knowledge(title="p", category_id=cat.id, submitter_id=user.id, review_status="pending")
        make_knowledge(title="a", category_id=cat.id, submitter_id=user.id, review_status="approved")
        make_knowledge(title="r", category_id=cat.id, submitter_id=user.id, review_status="rejected")
        make_knowledge(
            title="overdue",
            category_id=cat.id,
            submitter_id=user.id,
            review_status="approved",
            next_review_date=datetime.now() - timedelta(days=10),
        )
        make_knowledge(
            title="upcoming",
            category_id=cat.id,
            submitter_id=user.id,
            review_status="approved",
            next_review_date=datetime.now() + timedelta(days=10),
        )

        stats = ReviewService.get_statistics(db)
        assert stats["pending_count"] == 1
        assert stats["approved_count"] == 3
        assert stats["rejected_count"] == 1
        assert stats["overdue_count"] == 1
        assert stats["upcoming_count"] == 1
