from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend.app.models import ReadingStatus
from backend.app.services.reading_service import ReadingService


class TestMarkAsRead:
    def test_mark_read_creates_record(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        k = make_knowledge(category_id=cat.id, submitter_id=user.id, review_status="approved")

        result = ReadingService.mark_as_read(db, k.id, user.id)
        assert result["message"] == "标记已读成功"

        rs = (
            db.query(ReadingStatus)
            .filter(
                ReadingStatus.knowledge_id == k.id,
                ReadingStatus.user_id == user.id,
            )
            .first()
        )
        assert rs is not None
        assert rs.is_read is True

    def test_mark_read_idempotent_update(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        k = make_knowledge(category_id=cat.id, submitter_id=user.id, review_status="approved")

        ReadingService.mark_as_read(db, k.id, user.id)
        ReadingService.mark_as_unread(db, k.id, user.id)
        ReadingService.mark_as_read(db, k.id, user.id)

        count = (
            db.query(ReadingStatus)
            .filter(
                ReadingStatus.knowledge_id == k.id,
                ReadingStatus.user_id == user.id,
            )
            .count()
        )
        assert count == 1

    def test_mark_read_knowledge_not_found(self, db, make_user):
        user = make_user()
        with pytest.raises(HTTPException) as exc:
            ReadingService.mark_as_read(db, 99999, user.id)
        assert exc.value.status_code == 404


class TestMarkAsUnread:
    def test_mark_unread_deletes_record(self, db, make_category, make_user, make_knowledge, make_reading):
        cat = make_category()
        user = make_user()
        k = make_knowledge(category_id=cat.id, submitter_id=user.id, review_status="approved")
        make_reading(k.id, user.id, is_read=True)

        result = ReadingService.mark_as_unread(db, k.id, user.id)
        assert result["message"] == "标记未读成功"

        rs = (
            db.query(ReadingStatus)
            .filter(
                ReadingStatus.knowledge_id == k.id,
                ReadingStatus.user_id == user.id,
            )
            .first()
        )
        assert rs is None

    def test_mark_unread_when_no_record_is_noop(self, db, make_user):
        user = make_user()
        result = ReadingService.mark_as_unread(db, 12345, user.id)
        assert result["message"] == "标记未读成功"


class TestMyReadingStatus:
    def test_returns_only_own_read_items(self, db, make_category, make_user, make_knowledge, make_reading):
        cat = make_category()
        u1 = make_user(username="u1")
        u2 = make_user(username="u2")
        k1 = make_knowledge(title="k1", category_id=cat.id, submitter_id=u1.id, review_status="approved")
        k2 = make_knowledge(title="k2", category_id=cat.id, submitter_id=u1.id, review_status="approved")
        make_reading(k1.id, u1.id, is_read=True)
        make_reading(k2.id, u2.id, is_read=True)

        result = ReadingService.get_my_reading_status(db, u1.id)
        ids = {item["knowledge_id"] for item in result["items"]}
        assert k1.id in ids
        assert k2.id not in ids
        assert result["total"] == 1

    def test_filter_by_expiry_status(self, db, make_category, make_user, make_knowledge, make_reading):
        cat = make_category()
        user = make_user()
        overdue = make_knowledge(
            title="overdue",
            category_id=cat.id,
            submitter_id=user.id,
            review_status="approved",
            next_review_date=datetime.now() - timedelta(days=40),
        )
        upcoming = make_knowledge(
            title="upcoming",
            category_id=cat.id,
            submitter_id=user.id,
            review_status="approved",
            next_review_date=datetime.now() + timedelta(days=10),
        )
        make_reading(overdue.id, user.id, is_read=True)
        make_reading(upcoming.id, user.id, is_read=True)

        result = ReadingService.get_my_reading_status(db, user.id, review_expiry_status="overdue")
        ids = {item["knowledge_id"] for item in result["items"]}
        assert overdue.id in ids
        assert upcoming.id not in ids

    def test_pagination(self, db, make_category, make_user, make_knowledge, make_reading):
        cat = make_category()
        user = make_user()
        for i in range(4):
            k = make_knowledge(
                title=f"k{i}",
                category_id=cat.id,
                submitter_id=user.id,
                review_status="approved",
            )
            make_reading(k.id, user.id, is_read=True)

        page1 = ReadingService.get_my_reading_status(db, user.id, page=1, page_size=2)
        assert len(page1["items"]) == 2
        assert page1["total"] == 4
