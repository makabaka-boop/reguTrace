import pytest
from fastapi import HTTPException
from backend.app.services.reading_service import ReadingService
from backend.app.models import ReadingStatus


class TestReadingService:

    def test_mark_as_read_new_record(self, db, approved_knowledge, test_employee):
        result = ReadingService.mark_as_read(db, approved_knowledge.id, test_employee.id)
        assert "成功" in result["message"]

        reading = db.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == approved_knowledge.id,
            ReadingStatus.user_id == test_employee.id
        ).first()
        assert reading is not None
        assert reading.is_read is True
        assert reading.read_at is not None

    def test_mark_as_read_existing_record(self, db, approved_knowledge, test_employee):
        ReadingService.mark_as_read(db, approved_knowledge.id, test_employee.id)
        ReadingService.mark_as_read(db, approved_knowledge.id, test_employee.id)

        count = db.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == approved_knowledge.id,
            ReadingStatus.user_id == test_employee.id
        ).count()
        assert count == 1

    def test_mark_as_read_nonexistent_knowledge(self, db, test_employee):
        with pytest.raises(HTTPException) as exc_info:
            ReadingService.mark_as_read(db, 99999, test_employee.id)
        assert exc_info.value.status_code == 404
        assert "制度条目不存在" in exc_info.value.detail

    def test_mark_as_unread_existing(self, db, approved_knowledge, test_employee):
        ReadingService.mark_as_read(db, approved_knowledge.id, test_employee.id)
        result = ReadingService.mark_as_unread(db, approved_knowledge.id, test_employee.id)
        assert "成功" in result["message"]

        reading = db.query(ReadingStatus).filter(
            ReadingStatus.knowledge_id == approved_knowledge.id,
            ReadingStatus.user_id == test_employee.id
        ).first()
        assert reading is None

    def test_mark_as_unread_nonexistent_record(self, db, approved_knowledge, test_employee):
        result = ReadingService.mark_as_unread(db, approved_knowledge.id, test_employee.id)
        assert "成功" in result["message"]

    def test_get_my_reading_status_empty(self, db, test_employee):
        result = ReadingService.get_my_reading_status(db, test_employee.id, page=1, page_size=10)
        assert result["total"] == 0
        assert result["items"] == []

    def test_get_my_reading_status_with_data(self, db, approved_knowledge, upcoming_knowledge, test_employee):
        ReadingService.mark_as_read(db, approved_knowledge.id, test_employee.id)
        ReadingService.mark_as_read(db, upcoming_knowledge.id, test_employee.id)

        result = ReadingService.get_my_reading_status(db, test_employee.id, page=1, page_size=10)
        assert result["total"] == 2
        assert len(result["items"]) == 2

        for item in result["items"]:
            assert item["is_read"] is True
            assert item["knowledge_title"] is not None
            assert "review_expiry_status" in item

    def test_get_my_reading_status_pagination(self, db, approved_knowledge, upcoming_knowledge, overdue_knowledge, test_employee):
        for k in [approved_knowledge, upcoming_knowledge, overdue_knowledge]:
            ReadingService.mark_as_read(db, k.id, test_employee.id)

        result = ReadingService.get_my_reading_status(db, test_employee.id, page=1, page_size=2)
        assert result["total"] == 3
        assert len(result["items"]) == 2
        assert result["page"] == 1

    def test_get_my_reading_status_overdue_filter(self, db, approved_knowledge, overdue_knowledge, test_employee):
        ReadingService.mark_as_read(db, approved_knowledge.id, test_employee.id)
        ReadingService.mark_as_read(db, overdue_knowledge.id, test_employee.id)

        result = ReadingService.get_my_reading_status(db, test_employee.id, review_expiry_status="overdue")
        assert result["total"] == 1
        assert result["items"][0]["knowledge_id"] == overdue_knowledge.id

    def test_get_my_reading_status_upcoming_filter(self, db, approved_knowledge, upcoming_knowledge, test_employee):
        ReadingService.mark_as_read(db, approved_knowledge.id, test_employee.id)
        ReadingService.mark_as_read(db, upcoming_knowledge.id, test_employee.id)

        result = ReadingService.get_my_reading_status(db, test_employee.id, review_expiry_status="upcoming")
        assert result["total"] == 1
        assert result["items"][0]["knowledge_id"] == upcoming_knowledge.id

    def test_read_then_unread_flow(self, db, approved_knowledge, test_employee):
        ReadingService.mark_as_read(db, approved_knowledge.id, test_employee.id)
        r1 = ReadingService.get_my_reading_status(db, test_employee.id)
        assert r1["total"] == 1

        ReadingService.mark_as_unread(db, approved_knowledge.id, test_employee.id)
        r2 = ReadingService.get_my_reading_status(db, test_employee.id)
        assert r2["total"] == 0
