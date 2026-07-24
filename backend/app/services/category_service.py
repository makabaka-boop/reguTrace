from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from backend.app.models import Category, Knowledge, NodeSummary, UserGroup
from backend.app.schemas import CategoryCreate, CategoryUpdate


class CategoryService:
    @staticmethod
    def build_category_tree(categories: List[Category]) -> List[dict]:
        category_map = {}
        root_categories = []
        
        for cat in categories:
            cat_dict = {
                "id": cat.id,
                "name": cat.name,
                "code": cat.code,
                "parent_id": cat.parent_id,
                "group_id": cat.group_id,
                "sort_order": cat.sort_order,
                "is_active": cat.is_active,
                "level": cat.level,
                "path": cat.path,
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
                "children": []
            }
            category_map[cat.id] = cat_dict
            
            if cat.parent_id is None:
                root_categories.append(cat_dict)
            else:
                if cat.parent_id in category_map:
                    category_map[cat.parent_id]["children"].append(cat_dict)
        
        def sort_children(node):
            node["children"].sort(key=lambda x: x["sort_order"])
            for child in node["children"]:
                sort_children(child)
        
        for root in root_categories:
            sort_children(root)
        
        root_categories.sort(key=lambda x: x["sort_order"])
        return root_categories

    @staticmethod
    def get_all_categories(db: Session, include_inactive: bool = False):
        query = db.query(Category)
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        categories = query.order_by(Category.sort_order).all()
        return CategoryService.build_category_tree(categories)

    @staticmethod
    def get_category_by_id(db: Session, category_id: int):
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分类不存在"
            )
        return category

    @staticmethod
    def _update_descendant_paths(db: Session, parent_id: int, old_parent_path: str, new_parent_path: str, old_level: int, new_level: int):
        descendants = db.query(Category).filter(
            Category.path.like(f"{old_parent_path}/%")
        ).all()
        
        for desc in descendants:
            relative_path = desc.path[len(old_parent_path) + 1:]
            desc.path = f"{new_parent_path}/{relative_path}"
            level_diff = new_level - old_level
            desc.level = desc.level + level_diff
            db.add(desc)

    @staticmethod
    def create_category(db: Session, category_data: CategoryCreate):
        if category_data.parent_id is not None:
            parent = CategoryService.get_category_by_id(db, category_data.parent_id)
            level = parent.level + 1
            path = f"{parent.path}/{parent.id}"
        else:
            level = 1
            path = ""
        
        db_category = Category(
            name=category_data.name,
            code=category_data.code,
            parent_id=category_data.parent_id,
            group_id=category_data.group_id,
            sort_order=category_data.sort_order,
            level=level,
            path=path
        )
        db.add(db_category)
        db.flush()
        
        if path == "":
            db_category.path = str(db_category.id)
        else:
            db_category.path = f"{path}/{db_category.id}"
        
        db.commit()
        db.refresh(db_category)
        
        db_summary = NodeSummary(
            category_id=db_category.id,
            total_count=0,
            pending_count=0
        )
        db.add(db_summary)
        db.commit()
        
        return db_category

    @staticmethod
    def update_category(db: Session, category_id: int, category_data: CategoryUpdate):
        category = CategoryService.get_category_by_id(db, category_id)
        
        if category_data.name is not None:
            category.name = category_data.name
        if category_data.code is not None:
            category.code = category_data.code
        if category_data.group_id is not None:
            category.group_id = category_data.group_id
        if category_data.sort_order is not None:
            category.sort_order = category_data.sort_order
        if category_data.is_active is not None:
            category.is_active = category_data.is_active
        
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete_category(db: Session, category_id: int):
        category = CategoryService.get_category_by_id(db, category_id)
        
        children_count = db.query(Category).filter(Category.parent_id == category_id).count()
        if children_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该分类下有子分类，无法删除"
            )
        
        knowledge_count = db.query(Knowledge).filter(Knowledge.category_id == category_id).count()
        if knowledge_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该制度目录下有制度条目，无法删除"
            )
        
        db_summary = db.query(NodeSummary).filter(NodeSummary.category_id == category_id).first()
        if db_summary:
            db.delete(db_summary)
        
        db.delete(category)
        db.commit()

    @staticmethod
    def move_category(db: Session, category_id: int, target_parent_id: int):
        category = CategoryService.get_category_by_id(db, category_id)
        target_parent = CategoryService.get_category_by_id(db, target_parent_id)
        
        if target_parent.path.startswith(f"{category.path}/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将节点移动到其子节点下"
            )
        
        old_path = category.path
        old_level = category.level
        old_parent_id = category.parent_id
        
        category.parent_id = target_parent_id
        category.level = target_parent.level + 1
        new_path = f"{target_parent.path}/{category.id}"
        
        CategoryService._update_descendant_paths(db, category_id, old_path, new_path, old_level, category.level)
        
        category.path = new_path
        
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def merge_category(db: Session, source_id: int, target_id: int):
        if source_id == target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能合并到自身"
            )
        
        source = CategoryService.get_category_by_id(db, source_id)
        target = CategoryService.get_category_by_id(db, target_id)
        
        db.query(Knowledge).filter(Knowledge.category_id == source_id).update(
            {Knowledge.category_id: target_id}
        )
        
        db.query(Category).filter(Category.parent_id == source_id).update(
            {Category.parent_id: target_id}
        )
        
        source_children = db.query(Category).filter(Category.path.like(f"{source.path}/%")).all()
        for child in source_children:
            relative_path = child.path[len(source.path) + 1:]
            child.path = f"{target.path}/{relative_path}"
            level_diff = target.level - source.level + 1
            child.level = child.level + level_diff
            db.add(child)
        
        db_summary = db.query(NodeSummary).filter(NodeSummary.category_id == source_id).first()
        if db_summary:
            db.delete(db_summary)
        
        db.delete(source)
        db.commit()

    @staticmethod
    def _copy_category_tree(db: Session, source_id: int, target_parent_id: int = None, target_group_id: int = None, path_map: dict = None) -> dict:
        if path_map is None:
            path_map = {}
        
        source = CategoryService.get_category_by_id(db, source_id)
        
        new_group_id = target_group_id if target_group_id else source.group_id
        
        new_category = Category(
            name=f"{source.name}(副本)",
            code=source.code,
            parent_id=target_parent_id,
            group_id=new_group_id,
            sort_order=source.sort_order,
            is_active=source.is_active,
            level=1
        )
        
        if target_parent_id:
            target_parent = CategoryService.get_category_by_id(db, target_parent_id)
            new_category.level = target_parent.level + 1
        
        db.add(new_category)
        db.flush()
        
        if target_parent_id:
            target_parent = CategoryService.get_category_by_id(db, target_parent_id)
            new_category.path = f"{target_parent.path}/{new_category.id}"
        else:
            new_category.path = str(new_category.id)
        
        db.commit()
        db.refresh(new_category)
        
        db_summary = NodeSummary(
            category_id=new_category.id,
            total_count=0,
            pending_count=0
        )
        db.add(db_summary)
        db.commit()
        
        path_map[source_id] = new_category.id
        
        children = db.query(Category).filter(Category.parent_id == source_id).order_by(Category.sort_order).all()
        for child in children:
            CategoryService._copy_category_tree(db, child.id, new_category.id, target_group_id, path_map)
        
        return path_map

    @staticmethod
    def copy_category(db: Session, source_id: int, target_group_id: int, target_parent_id: int = None):
        if target_parent_id is not None:
            target_parent = CategoryService.get_category_by_id(db, target_parent_id)
            if target_parent.group_id != target_group_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="目标父节点不属于目标小组"
                )
        
        group = db.query(UserGroup).filter(UserGroup.id == target_group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标小组不存在"
            )
        
        path_map = CategoryService._copy_category_tree(db, source_id, target_parent_id, target_group_id)
        
        return {
            "message": "复制成功",
            "source_id": source_id,
            "new_root_id": path_map.get(source_id),
            "copied_count": len(path_map)
        }

    @staticmethod
    def deactivate_category(db: Session, category_id: int):
        category = CategoryService.get_category_by_id(db, category_id)
        category.is_active = False
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_category_list(db: Session, group_id: int = None):
        query = db.query(Category).filter(Category.is_active == True)
        if group_id:
            query = query.filter(Category.group_id == group_id)
        return query.order_by(Category.path).all()
