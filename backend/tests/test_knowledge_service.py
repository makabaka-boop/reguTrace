from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend.app.schemas import KnowledgeCreate, KnowledgeUpdate
from backend.app.services.knowledge_service import (
    KnowledgeService,
    calculate_next_review_date,
    get_review_expiry_status,
)


class TestReviewDateHelpers:
    def test_calculate_next_review_date_never(self):
        assert calculate_next_review_date("never") is None
        assert calculate_next_review_date("") is None

    def test_calculate_next_review_date_cycles(self):
        base = datetime(2025, 1, 15)
        assert calculate_next_review_date("1month", base) == datetime(2025, 2, 15)
        assert calculate_next_review_date("3months", base) == datetime(2025, 4, 15)
        assert calculate_next_review_date("6months", base) == datetime(2025, 7, 15)
        assert calculate_next_review_date("1year", base) == datetime(2026, 1, 15)

    def test_calculate_next_review_date_unknown_cycle_returns_none(self):
        assert calculate_next_review_date("bogus") is None

    def test_get_review_expiry_status_non_approved(self):
        assert get_review_expiry_status(datetime(2020, 1, 1), "pending") is None
        assert get_review_expiry_status(datetime(2020, 1, 1), "rejected") is None

    def test_get_review_expiry_status_no_date(self):
        assert get_review_expiry_status(None, "approved") is None

    def test_get_review_expiry_status_overdue(self):
        past = datetime.now() - timedelta(days=10)
        assert get_review_expiry_status(past, "approved") == "overdue"

    def test_get_review_expiry_status_upcoming(self):
        soon = datetime.now() + timedelta(days=10)
        assert get_review_expiry_status(soon, "approved") == "upcoming"

    def test_get_review_expiry_status_normal(self):
        far = datetime.now() + timedelta(days=120)
        assert get_review_expiry_status(far, "approved") == "normal"


class TestKnowledgeServiceCreate:
    def test_create_knowledge_success(self, db, make_category, make_user):
        cat = make_category(name="财务制度")
        user = make_user(username="emp", role="employee", name="员工")
        data = KnowledgeCreate(
            title="报销制度",
            content="<p>报销规定</p>",
            category_id=cat.id,
            suggested_review_cycle="1year",
        )

        k = KnowledgeService.create_knowledge(db, data, user.id)
        assert k.id is not None
        assert k.title == "报销制度"
        assert k.review_status == "pending"
        assert k.suggested_review_cycle == "1year"
        assert k.submitter_id == user.id

    def test_create_knowledge_default_cycle(self, db, make_category, make_user):
        cat = make_category()
        user = make_user()
        data = KnowledgeCreate(
            title="无周期",
            content="c",
            category_id=cat.id,
            suggested_review_cycle=None,
        )
        k = KnowledgeService.create_knowledge(db, data, user.id)
        assert k.suggested_review_cycle == "6months"

    def test_create_knowledge_invalid_cycle_falls_back(self, db, make_category, make_user):
        cat = make_category()
        user = make_user()
        data = KnowledgeCreate(
            title="bad cycle",
            content="c",
            category_id=cat.id,
            suggested_review_cycle="invalid",
        )
        k = KnowledgeService.create_knowledge(db, data, user.id)
        assert k.suggested_review_cycle == "6months"

    def test_create_knowledge_category_not_found(self, db, make_user):
        user = make_user()
        data = KnowledgeCreate(title="x", content="c", category_id=99999)
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.create_knowledge(db, data, user.id)
        assert exc.value.status_code == 404

    def test_create_knowledge_inactive_category(self, db, make_category, make_user):
        cat = make_category(name="停用", is_active=False)
        user = make_user()
        data = KnowledgeCreate(title="x", content="c", category_id=cat.id)
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.create_knowledge(db, data, user.id)
        assert exc.value.status_code == 400


class TestKnowledgeServiceQuery:
    def test_get_list_excludes_rejected(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        k1 = make_knowledge(title="通过", category_id=cat.id, submitter_id=user.id, review_status="approved")
        k2 = make_knowledge(title="驳回", category_id=cat.id, submitter_id=user.id, review_status="rejected")
        k3 = make_knowledge(title="待审", category_id=cat.id, submitter_id=user.id, review_status="pending")

        result = KnowledgeService.get_knowledge_list(db)
        ids = {item["id"] for item in result["items"]}
        assert k1.id in ids
        assert k3.id in ids
        assert k2.id not in ids
        assert result["total"] >= 2

    def test_get_list_filter_by_review_status(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        make_knowledge(title="a", category_id=cat.id, submitter_id=user.id, review_status="approved")
        make_knowledge(title="b", category_id=cat.id, submitter_id=user.id, review_status="pending")

        result = KnowledgeService.get_knowledge_list(db, review_status="pending")
        assert all(item["review_status"] == "pending" for item in result["items"])

    def test_get_list_keyword_filter(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        make_knowledge(title="财务报销须知", content="普通", category_id=cat.id, submitter_id=user.id, review_status="approved")
        make_knowledge(title="考勤规则", content="财务相关说明", category_id=cat.id, submitter_id=user.id, review_status="approved")
        make_knowledge(title="完全无关", content="xxx", category_id=cat.id, submitter_id=user.id, review_status="approved")

        result = KnowledgeService.get_knowledge_list(db, keyword="财务")
        assert result["total"] == 2

    def test_get_list_category_filter_includes_descendants(self, db, make_category, make_user, make_knowledge):
        root = make_category(name="根")
        child = make_category(name="子", parent_id=root.id)
        user = make_user()
        k_root = make_knowledge(title="根下", category_id=root.id, submitter_id=user.id, review_status="approved")
        k_child = make_knowledge(title="子下", category_id=child.id, submitter_id=user.id, review_status="approved")

        result = KnowledgeService.get_knowledge_list(db, category_id=root.id)
        ids = {item["id"] for item in result["items"]}
        assert k_root.id in ids
        assert k_child.id in ids

    def test_get_list_review_expiry_status_overdue(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        user = make_user()
        overdue = make_knowledge(
            title="已逾期",
            category_id=cat.id,
            submitter_id=user.id,
            review_status="approved",
            next_review_date=datetime.now() - timedelta(days=45),
        )
        normal = make_knowledge(
            title="正常",
            category_id=cat.id,
            submitter_id=user.id,
            review_status="approved",
            next_review_date=datetime.now() + timedelta(days=120),
        )

        result = KnowledgeService.get_knowledge_list(db, review_expiry_status="overdue")
        ids = {item["id"] for item in result["items"]}
        assert overdue.id in ids
        assert normal.id not in ids

    def test_get_list_review_expiry_status_upcoming(
        self, db, make_category, make_user, make_knowledge
    ):
        cat = make_category()
        user = make_user()
        upcoming = make_knowledge(
            title="即将到期",
            category_id=cat.id,
            submitter_id=user.id,
            review_status="approved",
            next_review_date=datetime.now() + timedelta(days=15),
        )
        normal = make_knowledge(
            title="正常",
            category_id=cat.id,
            submitter_id=user.id,
            review_status="approved",
            next_review_date=datetime.now() + timedelta(days=120),
        )
        result = KnowledgeService.get_knowledge_list(db, review_expiry_status="upcoming")
        ids = {item["id"] for item in result["items"]}
        assert upcoming.id in ids
        assert normal.id not in ids

    def test_get_list_with_is_read_flag(self, db, make_category, make_user, make_knowledge, make_reading):
        cat = make_category()
        user = make_user()
        k1 = make_knowledge(title="已读", category_id=cat.id, submitter_id=user.id, review_status="approved")
        k2 = make_knowledge(title="未读", category_id=cat.id, submitter_id=user.id, review_status="approved")
        make_reading(k1.id, user.id, is_read=True)

        result = KnowledgeService.get_knowledge_list(db, user_id=user.id)
        read_map = {item["id"]: item["is_read"] for item in result["items"]}
        assert read_map[k1.id] is True
        assert read_map[k2.id] is False

    def test_get_by_id_success(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        k = make_knowledge(title="详情", category_id=cat.id, submitter_id=user.id, review_status="approved")
        result = KnowledgeService.get_knowledge_by_id(db, k.id)
        assert result["id"] == k.id
        assert result["title"] == "详情"

    def test_get_by_id_not_found(self, db):
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.get_knowledge_by_id(db, 99999)
        assert exc.value.status_code == 404

    def test_pagination(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        for i in range(5):
            make_knowledge(title=f"制度{i}", category_id=cat.id, submitter_id=user.id, review_status="approved")

        page1 = KnowledgeService.get_knowledge_list(db, page=1, page_size=2)
        assert len(page1["items"]) == 2
        assert page1["total"] == 5
        page2 = KnowledgeService.get_knowledge_list(db, page=2, page_size=2)
        assert len(page2["items"]) == 2
        page3 = KnowledgeService.get_knowledge_list(db, page=3, page_size=2)
        assert len(page3["items"]) == 1


class TestKnowledgeServiceUpdateDelete:
    def test_update_own_knowledge(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        k = make_knowledge(title="旧标题", category_id=cat.id, submitter_id=user.id)
        data = KnowledgeUpdate(title="新标题", content="新内容")

        updated = KnowledgeService.update_knowledge(db, k.id, data, user.id)
        assert updated.title == "新标题"
        assert updated.content == "新内容"
        assert updated.review_status == "pending"
        assert updated.reject_reason is None

    def test_update_others_knowledge_forbidden(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        owner = make_user(username="owner")
        other = make_user(username="other")
        k = make_knowledge(title="x", category_id=cat.id, submitter_id=owner.id)
        data = KnowledgeUpdate(title="hack")
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.update_knowledge(db, k.id, data, other.id)
        assert exc.value.status_code == 403

    def test_update_not_found(self, db, make_user):
        user = make_user()
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.update_knowledge(db, 99999, KnowledgeUpdate(title="x"), user.id)
        assert exc.value.status_code == 404

    def test_update_to_inactive_category_fails(self, db, make_category, make_user, make_knowledge):
        active = make_category(name="启用")
        inactive = make_category(name="停用", is_active=False)
        user = make_user()
        k = make_knowledge(category_id=active.id, submitter_id=user.id)
        data = KnowledgeUpdate(category_id=inactive.id)
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.update_knowledge(db, k.id, data, user.id)
        assert exc.value.status_code == 400

    def test_delete_own_knowledge(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        user = make_user()
        k = make_knowledge(category_id=cat.id, submitter_id=user.id)
        KnowledgeService.delete_knowledge(db, k.id, user.id)
        with pytest.raises(HTTPException):
            KnowledgeService.get_knowledge_by_id(db, k.id)

    def test_delete_others_knowledge_forbidden(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        owner = make_user(username="owner")
        other = make_user(username="other")
        k = make_knowledge(category_id=cat.id, submitter_id=owner.id)
        with pytest.raises(HTTPException) as exc:
            KnowledgeService.delete_knowledge(db, k.id, other.id)
        assert exc.value.status_code == 403


class TestKnowledgeServiceMyKnowledge:
    def test_get_my_knowledge_only_own(self, db, make_category, make_user, make_knowledge):
        cat = make_category()
        u1 = make_user(username="u1")
        u2 = make_user(username="u2")
        k1 = make_knowledge(title="u1的", category_id=cat.id, submitter_id=u1.id, review_status="approved")
        k2 = make_knowledge(title="u2的", category_id=cat.id, submitter_id=u2.id, review_status="approved")

        result = KnowledgeService.get_my_knowledge(db, u1.id)
        ids = {item["id"] for item in result["items"]}
        assert k1.id in ids
        assert k2.id not in ids
