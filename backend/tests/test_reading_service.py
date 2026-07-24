"""阅读确认服务单元测试：标记已读/未读、我的阅读记录查询与筛选。"""
import pytest
from fastapi import HTTPException

from backend.app.services.reading_service import ReadingService
from backend.app.models import ReadingStatus


class TestMarkAsRead:
    def test_creates_reading_record(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]
        result = ReadingService.mark_as_read(db_session, target.id, users["employee"].id)
        assert result["message"] == "标记已读成功"
        record = db_session.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == target.id,
            ReadingStatus.user_id == users["employee"].id,
        ).first()
        assert record is not None
        assert record.is_read is True
        assert record.read_at is not None

    def test_idempotent_updates_existing(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]
        uid = users["employee"].id
        ReadingService.mark_as_read(db_session, target.id, uid)
        ReadingService.mark_as_read(db_session, target.id, uid)
        count = db_session.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == target.id,
            ReadingStatus.user_id == uid,
        ).count()
        assert count == 1  # 不会重复插入

    def test_remark_after_unread(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]
        uid = users["employee"].id
        ReadingService.mark_as_read(db_session, target.id, uid)
        ReadingService.mark_as_unread(db_session, target.id, uid)
        ReadingService.mark_as_read(db_session, target.id, uid)
        record = db_session.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == target.id, ReadingStatus.user_id == uid
        ).first()
        assert record is not None and record.is_read is True

    def test_nonexistent_knowledge_raises_404(self, db_session, users):
        with pytest.raises(HTTPException) as exc:
            ReadingService.mark_as_read(db_session, 99999, users["employee"].id)
        assert exc.value.status_code == 404


class TestMarkAsUnread:
    def test_deletes_reading_record(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]
        uid = users["employee"].id
        ReadingService.mark_as_read(db_session, target.id, uid)
        result = ReadingService.mark_as_unread(db_session, target.id, uid)
        assert result["message"] == "标记未读成功"
        record = db_session.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == target.id, ReadingStatus.user_id == uid
        ).first()
        assert record is None

    def test_unread_when_no_record_is_noop(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]
        # 未曾标记已读，直接标记未读也不报错
        result = ReadingService.mark_as_unread(db_session, target.id, users["employee"].id)
        assert result["message"] == "标记未读成功"


class TestGetMyReadingStatus:
    def test_returns_only_read_items(self, db_session, knowledge_set, users):
        uid = users["employee"].id
        ReadingService.mark_as_read(db_session, knowledge_set["normal"].id, uid)
        ReadingService.mark_as_read(db_session, knowledge_set["overdue"].id, uid)
        result = ReadingService.get_my_reading_status(db_session, uid, page_size=50)
        assert result["total"] == 2
        titles = {i["knowledge_title"] for i in result["items"]}
        assert titles == {"正常制度", "已到期制度"}

    def test_filter_by_expiry_status(self, db_session, knowledge_set, users):
        uid = users["employee"].id
        for key in ("normal", "overdue", "upcoming"):
            ReadingService.mark_as_read(db_session, knowledge_set[key].id, uid)
        result = ReadingService.get_my_reading_status(
            db_session, uid, review_expiry_status="overdue", page_size=50
        )
        assert result["total"] == 1
        assert result["items"][0]["knowledge_title"] == "已到期制度"
        assert result["items"][0]["review_expiry_status"] == "overdue"

    def test_pagination(self, db_session, knowledge_set, users):
        uid = users["employee"].id
        for key in ("normal", "overdue", "upcoming"):
            ReadingService.mark_as_read(db_session, knowledge_set[key].id, uid)
        page = ReadingService.get_my_reading_status(db_session, uid, page=1, page_size=2)
        assert len(page["items"]) == 2
        assert page["total"] == 3
