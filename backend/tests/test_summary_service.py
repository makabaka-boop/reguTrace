"""复核汇总服务单元测试：节点汇总（含未读数计算）与汇总重建。"""
import pytest
from fastapi import HTTPException

from backend.app.services.summary_service import SummaryService
from backend.app.services.reading_service import ReadingService


class TestRebuildAndNodeSummary:
    def test_rebuild_populates_counts(self, db_session, knowledge_set, categories):
        result = SummaryService.rebuild_all_summaries(db_session)
        assert result["message"] == "汇总数据已重建"
        # child 目录下：4 条非驳回（overdue/upcoming/normal/pending），其中 1 条 pending
        summary = SummaryService.get_node_summary(
            db_session, categories["child"].id, user_id=1
        )
        assert summary["total_count"] == 4
        assert summary["pending_count"] == 1

    def test_root_aggregates_descendants(self, db_session, knowledge_set, categories):
        SummaryService.rebuild_all_summaries(db_session)
        summary = SummaryService.get_node_summary(
            db_session, categories["root"].id, user_id=1
        )
        # 根节点通过 path 聚合子节点条目
        assert summary["total_count"] == 4

    def test_unread_count_reflects_reading(self, db_session, knowledge_set, categories, users):
        SummaryService.rebuild_all_summaries(db_session)
        uid = users["employee"].id
        # 未读时 4 条（非驳回）均未读
        before = SummaryService.get_node_summary(db_session, categories["child"].id, uid)
        assert before["unread_count"] == 4
        ReadingService.mark_as_read(db_session, knowledge_set["normal"].id, uid)
        after = SummaryService.get_node_summary(db_session, categories["child"].id, uid)
        assert after["unread_count"] == 3


class TestGetAllNodesSummary:
    def test_returns_active_nodes(self, db_session, knowledge_set, categories, users):
        SummaryService.rebuild_all_summaries(db_session)
        result = SummaryService.get_all_nodes_summary(db_session, users["employee"].id)
        ids = {row["category_id"] for row in result}
        # 只返回启用节点：root 与 child，停用目录不在其中
        assert categories["root"].id in ids
        assert categories["child"].id in ids
        assert categories["inactive"].id not in ids

    def test_node_summary_missing_category_raises_404(self, db_session):
        with pytest.raises(HTTPException) as exc:
            SummaryService.get_node_summary(db_session, 99999, user_id=1)
        assert exc.value.status_code == 404
