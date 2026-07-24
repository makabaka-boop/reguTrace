import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from backend.app.services.knowledge_service import (
    KnowledgeService,
    calculate_next_review_date,
    get_review_expiry_status
)
from backend.app.schemas import KnowledgeCreate, KnowledgeUpdate


class TestCalculateNextReviewDate:

    def test_never_cycle_returns_none(self):
        assert calculate_next_review_date('never') is None

    def test_empty_cycle_returns_none(self):
        assert calculate_next_review_date('') is None
        assert calculate_next_review_date(None) is None

    def test_1month_cycle(self):
        base = datetime(2024, 1, 15)
        result = calculate_next_review_date('1month', base)
        assert result == datetime(2024, 2, 15)

    def test_3months_cycle(self):
        base = datetime(2024, 1, 15)
        result = calculate_next_review_date('3months', base)
        assert result == datetime(2024, 4, 15)

    def test_6months_cycle(self):
        base = datetime(2024, 1, 15)
        result = calculate_next_review_date('6months', base)
        assert result == datetime(2024, 7, 15)

    def test_1year_cycle(self):
        base = datetime(2024, 1, 15)
        result = calculate_next_review_date('1year', base)
        assert result == datetime(2025, 1, 15)

    def test_unknown_cycle_returns_none(self):
        assert calculate_next_review_date('unknown') is None

    def test_uses_current_time_when_no_base(self):
        result = calculate_next_review_date('1month')
        assert result is not None
        assert result > datetime.now()


class TestGetReviewExpiryStatus:

    def test_pending_returns_none(self):
        assert get_review_expiry_status(datetime.now() + timedelta(days=10), 'pending') is None

    def test_no_date_returns_none(self):
        assert get_review_expiry_status(None, 'approved') is None

    def test_overdue_status(self):
        past_date = datetime.now() - timedelta(days=5)
        assert get_review_expiry_status(past_date, 'approved') == 'overdue'

    def test_upcoming_status(self):
        near_future = datetime.now() + timedelta(days=15)
        assert get_review_expiry_status(near_future, 'approved') == 'upcoming'

    def test_upcoming_boundary_30_days(self):
        boundary = datetime.now() + timedelta(days=30)
        assert get_review_expiry_status(boundary, 'approved') == 'upcoming'

    def test_normal_status(self):
        far_future = datetime.now() + timedelta(days=60)
        assert get_review_expiry_status(far_future, 'approved') == 'normal'


class TestKnowledgeService:

    def test_get_knowledge_list_basic(self, db, pending_knowledge, approved_knowledge, rejected_knowledge):
        result = KnowledgeService.get_knowledge_list(db, page=1, page_size=10)
        assert result["total"] == 2
        assert len(result["items"]) == 2
        titles = [item["title"] for item in result["items"]]
        assert "被驳回制度" not in titles

    def test_get_knowledge_list_with_category_filter(self, db, root_category, child_category, pending_knowledge, approved_knowledge):
        result = KnowledgeService.get_knowledge_list(db, category_id=root_category.id, page=1, page_size=10)
        assert result["total"] == 2

    def test_get_knowledge_list_with_keyword(self, db, pending_knowledge, approved_knowledge):
        result = KnowledgeService.get_knowledge_list(db, keyword="考勤", page=1, page_size=10)
        assert result["total"] == 1
        assert result["items"][0]["title"] == "员工考勤管理办法"

    def test_get_knowledge_list_with_review_status(self, db, pending_knowledge, approved_knowledge):
        result = KnowledgeService.get_knowledge_list(db, review_status="pending", page=1, page_size=10)
        assert result["total"] == 1
        assert result["items"][0]["review_status"] == "pending"

    def test_get_knowledge_list_overdue_filter(self, db, overdue_knowledge, approved_knowledge, upcoming_knowledge):
        result = KnowledgeService.get_knowledge_list(db, review_expiry_status="overdue", page=1, page_size=10)
        assert result["total"] == 1
        assert result["items"][0]["title"] == "已到期制度"

    def test_get_knowledge_list_upcoming_filter(self, db, overdue_knowledge, approved_knowledge, upcoming_knowledge):
        result = KnowledgeService.get_knowledge_list(db, review_expiry_status="upcoming", page=1, page_size=10)
        assert result["total"] == 1
        assert result["items"][0]["title"] == "即将到期制度"

    def test_get_knowledge_list_pagination(self, db, pending_knowledge, approved_knowledge, overdue_knowledge, upcoming_knowledge):
        result = KnowledgeService.get_knowledge_list(db, page=1, page_size=2)
        assert result["total"] == 4
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 2

    def test_get_knowledge_by_id_success(self, db, pending_knowledge):
        result = KnowledgeService.get_knowledge_by_id(db, pending_knowledge.id)
        assert result["id"] == pending_knowledge.id
        assert result["title"] == "员工考勤管理办法"
        assert "review_expiry_status" in result

    def test_get_knowledge_by_id_not_found(self, db):
        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService.get_knowledge_by_id(db, 99999)
        assert exc_info.value.status_code == 404

    def test_create_knowledge_success(self, db, child_category, test_employee):
        data = KnowledgeCreate(
            title="新制度标题",
            content="<p>新制度内容</p>",
            category_id=child_category.id,
            suggested_review_cycle="3months"
        )
        result = KnowledgeService.create_knowledge(db, data, test_employee.id)
        assert result.title == "新制度标题"
        assert result.review_status == "pending"
        assert result.suggested_review_cycle == "3months"
        assert result.submitter_id == test_employee.id

    def test_create_knowledge_category_not_found(self, db, test_employee):
        data = KnowledgeCreate(
            title="测试制度",
            content="内容",
            category_id=99999
        )
        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService.create_knowledge(db, data, test_employee.id)
        assert exc_info.value.status_code == 404
        assert "制度目录不存在" in exc_info.value.detail

    def test_create_knowledge_inactive_category(self, db, inactive_category, test_employee):
        data = KnowledgeCreate(
            title="测试制度",
            content="内容",
            category_id=inactive_category.id
        )
        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService.create_knowledge(db, data, test_employee.id)
        assert exc_info.value.status_code == 400
        assert "已停用" in exc_info.value.detail

    def test_create_knowledge_default_cycle(self, db, child_category, test_employee):
        data = KnowledgeCreate(
            title="默认周期制度",
            content="内容",
            category_id=child_category.id
        )
        result = KnowledgeService.create_knowledge(db, data, test_employee.id)
        assert result.suggested_review_cycle == "6months"

    def test_update_knowledge_success(self, db, pending_knowledge, test_employee):
        update_data = KnowledgeUpdate(title="更新后的标题")
        result = KnowledgeService.update_knowledge(db, pending_knowledge.id, update_data, test_employee.id)
        assert result.title == "更新后的标题"
        assert result.review_status == "pending"

    def test_update_knowledge_not_owner(self, db, pending_knowledge, test_admin):
        update_data = KnowledgeUpdate(title="恶意更新")
        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService.update_knowledge(db, pending_knowledge.id, update_data, test_admin.id)
        assert exc_info.value.status_code == 403

    def test_delete_knowledge_success(self, db, pending_knowledge, test_employee):
        KnowledgeService.delete_knowledge(db, pending_knowledge.id, test_employee.id)
        with pytest.raises(HTTPException):
            KnowledgeService.get_knowledge_by_id(db, pending_knowledge.id)

    def test_delete_knowledge_not_owner(self, db, pending_knowledge, test_admin):
        with pytest.raises(HTTPException) as exc_info:
            KnowledgeService.delete_knowledge(db, pending_knowledge.id, test_admin.id)
        assert exc_info.value.status_code == 403

    def test_get_my_knowledge(self, db, pending_knowledge, approved_knowledge, test_employee, test_admin):
        result = KnowledgeService.get_my_knowledge(db, submitter_id=test_employee.id, page=1, page_size=10)
        assert result["total"] == 2

    def test_get_knowledge_with_reading_status(self, db, approved_knowledge, test_employee):
        result = KnowledgeService.get_knowledge_by_id(db, approved_knowledge.id, user_id=test_employee.id)
        assert result["is_read"] is False

    def test_get_knowledge_list_excludes_rejected(self, db, rejected_knowledge, approved_knowledge):
        result = KnowledgeService.get_knowledge_list(db, page=1, page_size=10)
        titles = [i["title"] for i in result["items"]]
        assert "被驳回制度" not in titles
