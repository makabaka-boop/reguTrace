import pytest
from fastapi import HTTPException

from backend.app.models import NodeSummary
from backend.app.services.summary_service import SummaryService


class TestNodeSummary:
    def test_get_node_summary_counts(
        self, db, make_category, make_user, make_knowledge
    ):
        root = make_category(name="根")
        child = make_category(name="子", parent_id=root.id)
        user = make_user()
        make_knowledge(title="通过", category_id=child.id, submitter_id=user.id, review_status="approved")
        make_knowledge(title="待审", category_id=root.id, submitter_id=user.id, review_status="pending")
        make_knowledge(title="驳回", category_id=child.id, submitter_id=user.id, review_status="rejected")

        summary = SummaryService.get_node_summary(db, root.id, user.id)
        assert summary["category_id"] == root.id
        assert summary["total_count"] == 2
        assert summary["pending_count"] == 1
        assert summary["unread_count"] == 2

    def test_get_node_summary_unread_excludes_read(
        self, db, make_category, make_user, make_knowledge, make_reading
    ):
        cat = make_category(name="分类")
        user = make_user()
        k1 = make_knowledge(title="已读", category_id=cat.id, submitter_id=user.id, review_status="approved")
        k2 = make_knowledge(title="未读", category_id=cat.id, submitter_id=user.id, review_status="approved")
        make_reading(k1.id, user.id, is_read=True)

        summary = SummaryService.get_node_summary(db, cat.id, user.id)
        assert summary["total_count"] == 2
        assert summary["unread_count"] == 1

    def test_get_node_summary_not_found_category(self, db, make_user):
        user = make_user()
        with pytest.raises(HTTPException) as exc:
            SummaryService.get_node_summary(db, 99999, user.id)
        assert exc.value.status_code == 404

    def test_get_all_nodes_summary(
        self, db, make_category, make_user, make_knowledge
    ):
        c1 = make_category(name="A")
        c2 = make_category(name="B")
        user = make_user()
        make_knowledge(title="k", category_id=c1.id, submitter_id=user.id, review_status="approved")

        results = SummaryService.get_all_nodes_summary(db, user.id)
        by_cat = {r["category_id"]: r for r in results}
        assert by_cat[c1.id]["total_count"] == 1
        assert by_cat[c2.id]["total_count"] == 0

    def test_rebuild_all_summaries(
        self, db, make_category, make_user, make_knowledge
    ):
        c1 = make_category(name="Rebuild")
        user = make_user()
        make_knowledge(title="p", category_id=c1.id, submitter_id=user.id, review_status="pending")
        make_knowledge(title="a", category_id=c1.id, submitter_id=user.id, review_status="approved")

        result = SummaryService.rebuild_all_summaries(db)
        assert "已重建" in result["message"]

        ns = db.query(NodeSummary).filter(NodeSummary.category_id == c1.id).first()
        assert ns is not None
        assert ns.total_count == 2
        assert ns.pending_count == 1
