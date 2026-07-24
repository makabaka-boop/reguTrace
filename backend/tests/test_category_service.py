import pytest
from fastapi import HTTPException

from backend.app.schemas import CategoryCreate, CategoryUpdate
from backend.app.services.category_service import CategoryService


def _build_cat(id, name, parent_id=None, sort_order=0, is_active=True):
    class _Cat:
        def __init__(self):
            self.id = id
            self.name = name
            self.code = f"C{id}"
            self.parent_id = parent_id
            self.group_id = None
            self.sort_order = sort_order
            self.is_active = is_active
            self.level = 1 if parent_id is None else 2
            self.path = str(id) if parent_id is None else f"{parent_id}/{id}"
            self.created_at = None
            self.updated_at = None

    return _Cat()


class TestBuildCategoryTree:
    def test_empty_list(self):
        assert CategoryService.build_category_tree([]) == []

    def test_single_root(self):
        cats = [_build_cat(1, "根节点")]
        tree = CategoryService.build_category_tree(cats)
        assert len(tree) == 1
        assert tree[0]["id"] == 1
        assert tree[0]["name"] == "根节点"
        assert tree[0]["children"] == []

    def test_parent_child_relationship(self):
        parent = _build_cat(1, "父")
        child = _build_cat(2, "子", parent_id=1)
        tree = CategoryService.build_category_tree([parent, child])
        assert len(tree) == 1
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["id"] == 2
        assert tree[0]["children"][0]["name"] == "子"

    def test_multi_level_tree(self):
        root = _build_cat(1, "根")
        mid = _build_cat(2, "中", parent_id=1)
        leaf = _build_cat(3, "叶", parent_id=2)
        tree = CategoryService.build_category_tree([root, mid, leaf])
        assert tree[0]["id"] == 1
        assert tree[0]["children"][0]["id"] == 2
        assert tree[0]["children"][0]["children"][0]["id"] == 3

    def test_children_sorted_by_sort_order(self):
        root = _build_cat(1, "根")
        c2 = _build_cat(2, "B", parent_id=1, sort_order=20)
        c3 = _build_cat(3, "A", parent_id=1, sort_order=5)
        tree = CategoryService.build_category_tree([root, c2, c3])
        children = tree[0]["children"]
        assert [c["id"] for c in children] == [3, 2]

    def test_roots_sorted_by_sort_order(self):
        r1 = _build_cat(1, "B", sort_order=30)
        r2 = _build_cat(2, "A", sort_order=10)
        tree = CategoryService.build_category_tree([r1, r2])
        assert [n["id"] for n in tree] == [2, 1]

    def test_orphan_child_ignored_gracefully(self):
        child = _build_cat(2, "孤儿", parent_id=999)
        tree = CategoryService.build_category_tree([child])
        assert tree == []


class TestCategoryServiceCRUD:
    def test_get_all_categories_only_active_by_default(self, db, make_category):
        active = make_category(name="启用", is_active=True)
        inactive = make_category(name="停用", is_active=False)

        tree = CategoryService.get_all_categories(db)
        ids = [n["id"] for n in tree]
        assert active.id in ids
        assert inactive.id not in ids

    def test_get_all_categories_include_inactive(self, db, make_category):
        active = make_category(name="启用")
        inactive = make_category(name="停用", is_active=False)

        tree = CategoryService.get_all_categories(db, include_inactive=True)
        ids = [n["id"] for n in tree]
        assert active.id in ids
        assert inactive.id in ids

    def test_get_category_by_id_found(self, db, make_category):
        cat = make_category(name="找我")
        result = CategoryService.get_category_by_id(db, cat.id)
        assert result.id == cat.id
        assert result.name == "找我"

    def test_get_category_by_id_not_found(self, db):
        with pytest.raises(HTTPException) as exc:
            CategoryService.get_category_by_id(db, 99999)
        assert exc.value.status_code == 404

    def test_create_root_category(self, db):
        data = CategoryCreate(name="新根分类", code="ROOT1", sort_order=1)
        cat = CategoryService.create_category(db, data)
        assert cat.id is not None
        assert cat.name == "新根分类"
        assert cat.level == 1
        assert cat.path == str(cat.id)

    def test_create_child_category(self, db, make_category):
        parent = make_category(name="父")
        data = CategoryCreate(name="子", parent_id=parent.id, sort_order=1)
        child = CategoryService.create_category(db, data)
        assert child.parent_id == parent.id
        assert child.level == 2
        assert child.path == f"{parent.path}/{parent.id}/{child.id}"

    def test_update_category_fields(self, db, make_category):
        cat = make_category(name="原名")
        data = CategoryUpdate(name="新名", code="NEW", sort_order=9)
        updated = CategoryService.update_category(db, cat.id, data)
        assert updated.name == "新名"
        assert updated.code == "NEW"
        assert updated.sort_order == 9

    def test_delete_category_with_children_fails(self, db, make_category):
        parent = make_category(name="父")
        make_category(name="子", parent_id=parent.id)
        with pytest.raises(HTTPException) as exc:
            CategoryService.delete_category(db, parent.id)
        assert exc.value.status_code == 400
        assert "子分类" in exc.value.detail

    def test_delete_category_with_knowledge_fails(self, db, make_category, make_user, make_knowledge):
        cat = make_category(name="有制度")
        user = make_user()
        make_knowledge(category_id=cat.id, submitter_id=user.id)
        with pytest.raises(HTTPException) as exc:
            CategoryService.delete_category(db, cat.id)
        assert exc.value.status_code == 400
        assert "制度条目" in exc.value.detail

    def test_delete_empty_category_success(self, db, make_category):
        cat = make_category(name="空分类")
        CategoryService.delete_category(db, cat.id)
        with pytest.raises(HTTPException):
            CategoryService.get_category_by_id(db, cat.id)

    def test_deactivate_category(self, db, make_category):
        cat = make_category(name="即将停用")
        assert cat.is_active is True
        result = CategoryService.deactivate_category(db, cat.id)
        assert result.is_active is False

    def test_move_category_to_own_descendant_fails(self, db, make_category):
        root = make_category(name="根")
        child = make_category(name="子", parent_id=root.id)
        with pytest.raises(HTTPException) as exc:
            CategoryService.move_category(db, root.id, child.id)
        assert exc.value.status_code == 400

    def test_merge_into_self_fails(self, db, make_category):
        cat = make_category(name="自")
        with pytest.raises(HTTPException) as exc:
            CategoryService.merge_category(db, cat.id, cat.id)
        assert "不能合并到自身" in exc.value.detail

    def test_merge_moves_knowledge_and_deletes_source(self, db, make_category, make_user, make_knowledge):
        source = make_category(name="源")
        target = make_category(name="目标")
        user = make_user()
        k = make_knowledge(category_id=source.id, submitter_id=user.id)

        CategoryService.merge_category(db, source.id, target.id)

        from backend.app.models import Knowledge
        moved = db.query(Knowledge).filter(Knowledge.id == k.id).first()
        assert moved.category_id == target.id
        with pytest.raises(HTTPException):
            CategoryService.get_category_by_id(db, source.id)
