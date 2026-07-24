"""制度条目服务单元测试：新增/查询/状态筛选/复核到期状态计算等核心逻辑。"""
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend.app.services.knowledge_service import (
    KnowledgeService,
    calculate_next_review_date,
    get_review_expiry_status,
)
from backend.app.schemas import KnowledgeCreate, KnowledgeUpdate


class TestCalculateNextReviewDate:
    def test_never_returns_none(self):
        assert calculate_next_review_date("never") is None

    def test_empty_cycle_returns_none(self):
        assert calculate_next_review_date("") is None

    @pytest.mark.parametrize("cycle,months,years", [
        ("1month", 1, 0),
        ("3months", 3, 0),
        ("6months", 6, 0),
        ("1year", 0, 1),
    ])
    def test_known_cycles(self, cycle, months, years):
        base = datetime(2026, 1, 1)
        result = calculate_next_review_date(cycle, from_date=base)
        expected_year = base.year + years + (months // 12)
        expected_month = base.month + (months % 12)
        assert result.year == expected_year
        assert result.month == expected_month

    def test_unknown_cycle_returns_none(self):
        assert calculate_next_review_date("weird") is None


class TestGetReviewExpiryStatus:
    def test_none_when_not_approved(self):
        assert get_review_expiry_status(datetime.now() + timedelta(days=1), "pending") is None

    def test_none_when_no_date(self):
        assert get_review_expiry_status(None, "approved") is None

    def test_overdue(self):
        assert get_review_expiry_status(datetime.now() - timedelta(days=1), "approved") == "overdue"

    def test_upcoming_within_30_days(self):
        assert get_review_expiry_status(datetime.now() + timedelta(days=10), "approved") == "upcoming"

    def test_normal_beyond_30_days(self):
        assert get_review_expiry_status(datetime.now() + timedelta(days=100), "approved") == "normal"


class TestCreateKnowledge:
    def test_create_defaults_to_pending(self, db_session, categories, users):
        item = KnowledgeService.create_knowledge(
            db_session,
            KnowledgeCreate(title="新制度", content="内容", category_id=categories["child"].id),
            submitter_id=users["employee"].id,
        )
        assert item.id is not None
        assert item.review_status == "pending"
        assert item.suggested_review_cycle == "6months"

    def test_create_with_invalid_cycle_falls_back(self, db_session, categories, users):
        item = KnowledgeService.create_knowledge(
            db_session,
            KnowledgeCreate(title="X", content="Y", category_id=categories["child"].id,
                            suggested_review_cycle="invalid"),
            submitter_id=users["employee"].id,
        )
        assert item.suggested_review_cycle == "6months"

    def test_create_with_nonexistent_category_raises_404(self, db_session, users):
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.create_knowledge(
                db_session,
                KnowledgeCreate(title="X", content="Y", category_id=99999),
                submitter_id=users["employee"].id,
            )
        assert exc.value.status_code == 404

    def test_create_under_inactive_category_raises_400(self, db_session, categories, users):
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.create_knowledge(
                db_session,
                KnowledgeCreate(title="X", content="Y", category_id=categories["inactive"].id),
                submitter_id=users["employee"].id,
            )
        assert exc.value.status_code == 400


class TestGetKnowledgeList:
    def test_excludes_rejected(self, db_session, knowledge_set, users):
        result = KnowledgeService.get_knowledge_list(db_session, page_size=50)
        titles = [i["title"] for i in result["items"]]
        assert "已驳回制度" not in titles
        # overdue/upcoming/normal/pending 共 4 条
        assert result["total"] == 4

    def test_filter_by_review_status(self, db_session, knowledge_set):
        result = KnowledgeService.get_knowledge_list(db_session, review_status="pending", page_size=50)
        assert result["total"] == 1
        assert result["items"][0]["title"] == "待复核制度"

    def test_filter_by_keyword(self, db_session, knowledge_set):
        result = KnowledgeService.get_knowledge_list(db_session, keyword="即将", page_size=50)
        assert result["total"] == 1
        assert result["items"][0]["title"] == "即将到期制度"

    def test_filter_by_category_includes_descendants(self, db_session, knowledge_set, categories):
        # 条目挂在 child 下，通过 root 查询应能借助 path 命中
        result = KnowledgeService.get_knowledge_list(
            db_session, category_id=categories["root"].id, page_size=50
        )
        assert result["total"] == 4

    @pytest.mark.parametrize("expiry,expected_title", [
        ("overdue", "已到期制度"),
        ("upcoming", "即将到期制度"),
        ("normal", "正常制度"),
    ])
    def test_filter_by_review_expiry_status(self, db_session, knowledge_set, expiry, expected_title):
        result = KnowledgeService.get_knowledge_list(
            db_session, review_expiry_status=expiry, page_size=50
        )
        assert result["total"] == 1
        assert result["items"][0]["title"] == expected_title

    def test_is_read_flag_reflects_reading_status(self, db_session, knowledge_set, users):
        from backend.app.services.reading_service import ReadingService
        target = knowledge_set["normal"]
        ReadingService.mark_as_read(db_session, target.id, users["employee"].id)
        result = KnowledgeService.get_knowledge_list(
            db_session, user_id=users["employee"].id, page_size=50
        )
        read_map = {i["title"]: i["is_read"] for i in result["items"]}
        assert read_map["正常制度"] is True
        assert read_map["待复核制度"] is False

    def test_pagination(self, db_session, knowledge_set):
        page1 = KnowledgeService.get_knowledge_list(db_session, page=1, page_size=2)
        assert len(page1["items"]) == 2
        assert page1["total"] == 4


class TestGetKnowledgeById:
    def test_success(self, db_session, knowledge_set):
        target = knowledge_set["normal"]
        result = KnowledgeService.get_knowledge_by_id(db_session, target.id)
        assert result["id"] == target.id
        assert result["review_expiry_status"] == "normal"

    def test_not_found_raises_404(self, db_session):
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.get_knowledge_by_id(db_session, 99999)
        assert exc.value.status_code == 404


class TestUpdateKnowledge:
    def test_owner_can_update_and_reset_to_pending(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]
        updated = KnowledgeService.update_knowledge(
            db_session, target.id, KnowledgeUpdate(title="改后标题"), users["employee"].id
        )
        assert updated.title == "改后标题"
        assert updated.review_status == "pending"
        assert updated.reject_reason is None

    def test_non_owner_cannot_update(self, db_session, knowledge_set, users):
        target = knowledge_set["normal"]
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.update_knowledge(
                db_session, target.id, KnowledgeUpdate(title="x"), users["supervisor"].id
            )
        assert exc.value.status_code == 403

    def test_update_to_inactive_category_raises_400(self, db_session, knowledge_set, users, categories):
        target = knowledge_set["normal"]
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.update_knowledge(
                db_session, target.id,
                KnowledgeUpdate(category_id=categories["inactive"].id),
                users["employee"].id,
            )
        assert exc.value.status_code == 400


class TestDeleteKnowledge:
    def test_owner_can_delete(self, db_session, knowledge_set, users):
        target = knowledge_set["pending"]
        KnowledgeService.delete_knowledge(db_session, target.id, users["employee"].id)
        with pytest.raises(HTTPException):
            KnowledgeService.get_knowledge_by_id(db_session, target.id)

    def test_non_owner_cannot_delete(self, db_session, knowledge_set, users):
        target = knowledge_set["pending"]
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.delete_knowledge(db_session, target.id, users["supervisor"].id)
        assert exc.value.status_code == 403


class TestGetMyKnowledge:
    def test_returns_only_submitter_items(self, db_session, knowledge_set, users):
        result = KnowledgeService.get_my_knowledge(db_session, users["employee"].id, page_size=50)
        # 全部 5 条（含 rejected）都是 employee 提交
        assert result["total"] == 5
        result_other = KnowledgeService.get_my_knowledge(db_session, users["supervisor"].id)
        assert result_other["total"] == 0
