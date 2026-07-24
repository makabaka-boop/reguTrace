import pytest
from fastapi import HTTPException
from backend.app.services.category_service import CategoryService
from backend.app.models import Category, NodeSummary
from backend.app.schemas import CategoryCreate, CategoryUpdate


class TestBuildCategoryTree:

    def test_empty_list(self):
        result = CategoryService.build_category_tree([])
        assert result == []

    def test_single_root(self, db, test_group):
        cat = Category(name="根目录", code="ROOT", sort_order=1, level=1, path="1", group_id=test_group.id)
        db.add(cat)
        db.commit()
        db.refresh(cat)

        result = CategoryService.build_category_tree([cat])
        assert len(result) == 1
        assert result[0]["name"] == "根目录"
        assert result[0]["children"] == []

    def test_parent_child_structure(self, db, root_category, child_category):
        categories = db.query(Category).order_by(Category.sort_order).all()
        tree = CategoryService.build_category_tree(categories)

        assert len(tree) == 1
        root = tree[0]
        assert root["name"] == "行政制度"
        assert len(root["children"]) == 1
        assert root["children"][0]["name"] == "考勤制度"
        assert root["children"][0]["children"] == []

    def test_sorted_by_sort_order(self, db, test_group):
        cat1 = Category(name="B目录", code="B", sort_order=2, level=1, path="1", group_id=test_group.id)
        cat2 = Category(name="A目录", code="A", sort_order=1, level=1, path="2", group_id=test_group.id)
        db.add_all([cat1, cat2])
        db.commit()

        categories = db.query(Category).all()
        tree = CategoryService.build_category_tree(categories)
        assert tree[0]["name"] == "A目录"
        assert tree[1]["name"] == "B目录"

    def test_multiple_roots(self, db, test_group):
        cat1 = Category(name="根目录1", code="R1", sort_order=1, level=1, path="1", group_id=test_group.id)
        cat2 = Category(name="根目录2", code="R2", sort_order=2, level=1, path="2", group_id=test_group.id)
        db.add_all([cat1, cat2])
        db.commit()

        categories = db.query(Category).all()
        tree = CategoryService.build_category_tree(categories)
        assert len(tree) == 2


class TestCategoryService:

    def test_get_all_categories_active_only(self, db, root_category, child_category, inactive_category):
        tree = CategoryService.get_all_categories(db, include_inactive=False)
        names = []
        def collect(nodes):
            for n in nodes:
                names.append(n["name"])
                collect(n.get("children", []))
        collect(tree)
        assert "已停用目录" not in names
        assert "行政制度" in names

    def test_get_all_categories_include_inactive(self, db, root_category, inactive_category):
        tree = CategoryService.get_all_categories(db, include_inactive=True)
        names = [n["name"] for n in tree]
        assert "已停用目录" in names

    def test_get_category_by_id_success(self, db, root_category):
        result = CategoryService.get_category_by_id(db, root_category.id)
        assert result.name == "行政制度"

    def test_get_category_by_id_not_found(self, db):
        with pytest.raises(HTTPException) as exc_info:
            CategoryService.get_category_by_id(db, 99999)
        assert exc_info.value.status_code == 404
        assert "分类不存在" in exc_info.value.detail

    def test_create_root_category(self, db, test_group):
        data = CategoryCreate(name="新根目录", code="NEW", sort_order=5, group_id=test_group.id)
        result = CategoryService.create_category(db, data)
        assert result.name == "新根目录"
        assert result.level == 1
        assert result.path == str(result.id)
        summary = db.query(NodeSummary).filter(NodeSummary.category_id == result.id).first()
        assert summary is not None
        assert summary.total_count == 0

    def test_create_child_category(self, db, root_category, test_group):
        data = CategoryCreate(name="子目录", code="SUB", parent_id=root_category.id, sort_order=2, group_id=test_group.id)
        result = CategoryService.create_category(db, data)
        assert result.level == 2
        assert result.parent_id == root_category.id
        assert root_category.path in result.path

    def test_update_category_name(self, db, root_category):
        data = CategoryUpdate(name="更新后名称")
        result = CategoryService.update_category(db, root_category.id, data)
        assert result.name == "更新后名称"

    def test_update_category_active_status(self, db, root_category):
        data = CategoryUpdate(is_active=False)
        result = CategoryService.update_category(db, root_category.id, data)
        assert result.is_active is False

    def test_delete_category_success(self, db, root_category):
        cat = Category(name="待删除", code="DEL", sort_order=10, level=1, path="99", group_id=root_category.group_id)
        db.add(cat)
        db.flush()
        cat.path = str(cat.id)
        db.commit()
        db.refresh(cat)
        summary = NodeSummary(category_id=cat.id, total_count=0, pending_count=0)
        db.add(summary)
        db.commit()

        CategoryService.delete_category(db, cat.id)
        with pytest.raises(HTTPException):
            CategoryService.get_category_by_id(db, cat.id)

    def test_delete_category_with_children_fails(self, db, root_category, child_category):
        with pytest.raises(HTTPException) as exc_info:
            CategoryService.delete_category(db, root_category.id)
        assert exc_info.value.status_code == 400
        assert "子分类" in exc_info.value.detail

    def test_deactivate_category(self, db, root_category):
        result = CategoryService.deactivate_category(db, root_category.id)
        assert result.is_active is False

    def test_get_category_list_by_group(self, db, root_category, test_group):
        result = CategoryService.get_category_list(db, group_id=test_group.id)
        assert len(result) >= 1
        for cat in result:
            assert cat.group_id == test_group.id
