"""分类服务单元测试：分类树构建、增删改、停用、约束校验。"""
import pytest
from fastapi import HTTPException

from backend.app.services.category_service import CategoryService
from backend.app.schemas import CategoryCreate, CategoryUpdate
from backend.app.models import Category


class TestBuildCategoryTree:
    def test_builds_nested_structure(self, db_session, categories):
        # 取所有分类（含停用）构建树
        all_cats = db_session.query(Category).order_by(Category.sort_order).all()
        tree = CategoryService.build_category_tree(all_cats)
        assert len(tree) == 1  # 只有一个根
        root = tree[0]
        assert root["name"] == "人事制度"
        assert len(root["children"]) == 2

    def test_children_sorted_by_sort_order(self, db_session, categories):
        all_cats = db_session.query(Category).all()
        tree = CategoryService.build_category_tree(all_cats)
        children = tree[0]["children"]
        orders = [c["sort_order"] for c in children]
        assert orders == sorted(orders)

    def test_empty_input_returns_empty_list(self):
        assert CategoryService.build_category_tree([]) == []

    def test_root_nodes_sorted(self, db_session, group):
        b = Category(name="B", parent_id=None, group_id=group.id, sort_order=2, level=1)
        a = Category(name="A", parent_id=None, group_id=group.id, sort_order=1, level=1)
        db_session.add_all([b, a])
        db_session.flush()
        b.path, a.path = str(b.id), str(a.id)
        db_session.commit()
        tree = CategoryService.build_category_tree([b, a])
        assert [n["name"] for n in tree] == ["A", "B"]


class TestGetAllCategories:
    def test_excludes_inactive_by_default(self, db_session, categories):
        tree = CategoryService.get_all_categories(db_session)
        children = tree[0]["children"]
        names = [c["name"] for c in children]
        assert "已停用目录" not in names

    def test_include_inactive(self, db_session, categories):
        tree = CategoryService.get_all_categories(db_session, include_inactive=True)
        names = [c["name"] for c in tree[0]["children"]]
        assert "已停用目录" in names


class TestGetCategoryById:
    def test_success(self, db_session, categories):
        cat = CategoryService.get_category_by_id(db_session, categories["root"].id)
        assert cat.name == "人事制度"

    def test_not_found_raises_404(self, db_session):
        with pytest.raises(HTTPException) as exc:
            CategoryService.get_category_by_id(db_session, 99999)
        assert exc.value.status_code == 404


class TestCreateCategory:
    def test_create_root_sets_level_and_path(self, db_session, group):
        cat = CategoryService.create_category(
            db_session, CategoryCreate(name="财务制度", group_id=group.id, sort_order=1)
        )
        assert cat.level == 1
        assert cat.path == str(cat.id)

    def test_create_child_inherits_path(self, db_session, categories, group):
        parent = categories["root"]
        cat = CategoryService.create_category(
            db_session,
            CategoryCreate(name="子目录", parent_id=parent.id, group_id=group.id),
        )
        assert cat.level == parent.level + 1
        # 服务实现的 path 规则：父 path 后先追加父 id，再追加自身 id
        assert cat.path == f"{parent.path}/{parent.id}/{cat.id}"
        assert cat.path.endswith(str(cat.id))

    def test_create_generates_summary(self, db_session, group):
        from backend.app.models import NodeSummary
        cat = CategoryService.create_category(
            db_session, CategoryCreate(name="有汇总", group_id=group.id)
        )
        summary = db_session.query(NodeSummary).filter(NodeSummary.category_id == cat.id).first()
        assert summary is not None


class TestUpdateCategory:
    def test_update_name_and_active(self, db_session, categories):
        updated = CategoryService.update_category(
            db_session, categories["child"].id,
            CategoryUpdate(name="新名称", is_active=False),
        )
        assert updated.name == "新名称"
        assert updated.is_active is False


class TestDeactivateCategory:
    def test_deactivate(self, db_session, categories):
        updated = CategoryService.deactivate_category(db_session, categories["child"].id)
        assert updated.is_active is False


class TestDeleteCategory:
    def test_delete_leaf_success(self, db_session, categories):
        target = categories["inactive"]
        CategoryService.delete_category(db_session, target.id)
        assert db_session.query(Category).filter(Category.id == target.id).first() is None

    def test_cannot_delete_with_children(self, db_session, categories):
        with pytest.raises(HTTPException) as exc:
            CategoryService.delete_category(db_session, categories["root"].id)
        assert exc.value.status_code == 400
        assert "子分类" in exc.value.detail

    def test_cannot_delete_with_knowledge(self, db_session, categories, users, make_knowledge):
        make_knowledge(title="占位", category=categories["child"], submitter=users["employee"])
        with pytest.raises(HTTPException) as exc:
            CategoryService.delete_category(db_session, categories["child"].id)
        assert exc.value.status_code == 400
        assert "制度条目" in exc.value.detail


class TestGetCategoryList:
    def test_filter_active_and_group(self, db_session, categories, group):
        result = CategoryService.get_category_list(db_session, group_id=group.id)
        names = [c.name for c in result]
        assert "已停用目录" not in names  # 仅返回启用项
        assert "人事制度" in names
