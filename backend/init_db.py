import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import Base, engine, SessionLocal
from backend.app.models.user import User
from backend.app.models.group import UserGroup, GroupMember
from backend.app.models.category import Category
from backend.app.models.knowledge import Knowledge
from backend.app.utils.security import hash_password
from sqlalchemy import text


def init_database():
    db_path = engine.url.database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        with open(os.path.join(os.path.dirname(__file__), "app", "triggers", "summary_triggers.sql"), "r") as f:
            trigger_sql = f.read()
        
        import re
        pattern = r'CREATE TRIGGER[\s\S]*?END;'
        matches = re.findall(pattern, trigger_sql, re.IGNORECASE)
        
        for sql_stmt in matches:
            sql_stmt = sql_stmt.strip()
            if sql_stmt:
                db.execute(text(sql_stmt))
        db.commit()
        
        users = [
            {"username": "admin", "password": "123456", "role": "admin", "name": "系统管理员"},
            {"username": "employee1", "password": "123456", "role": "employee", "name": "员工张三"},
            {"username": "employee2", "password": "123456", "role": "employee", "name": "员工李四"},
            {"username": "supervisor1", "password": "123456", "role": "supervisor", "name": "主管王五"},
        ]
        
        for user_data in users:
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(
                    username=user_data["username"],
                    password_hash=hash_password(user_data["password"]),
                    role=user_data["role"],
                    name=user_data["name"]
                )
                db.add(user)
        
        db.commit()
        
        groups = [
            {"name": "技术部", "description": "技术研发部门"},
            {"name": "产品部", "description": "产品设计部门"},
            {"name": "运营部", "description": "运营推广部门"},
        ]
        
        group_ids = []
        for group_data in groups:
            existing = db.query(UserGroup).filter(UserGroup.name == group_data["name"]).first()
            if not existing:
                group = UserGroup(**group_data)
                db.add(group)
                db.commit()
                db.refresh(group)
                group_ids.append(group.id)
            else:
                group_ids.append(existing.id)
        
        employee1 = db.query(User).filter(User.username == "employee1").first()
        employee2 = db.query(User).filter(User.username == "employee2").first()
        supervisor1 = db.query(User).filter(User.username == "supervisor1").first()
        
        if employee1 and group_ids:
            for gid in group_ids[:1]:
                existing = db.query(GroupMember).filter(
                    GroupMember.group_id == gid,
                    GroupMember.user_id == employee1.id
                ).first()
                if not existing:
                    db.add(GroupMember(group_id=gid, user_id=employee1.id))
        
        if employee2 and len(group_ids) > 1:
            for gid in group_ids[1:2]:
                existing = db.query(GroupMember).filter(
                    GroupMember.group_id == gid,
                    GroupMember.user_id == employee2.id
                ).first()
                if not existing:
                    db.add(GroupMember(group_id=gid, user_id=employee2.id))
        
        db.commit()
        
        default_categories = [
            {"name": "技术文档", "code": "TECH", "parent_id": None, "group_id": group_ids[0] if len(group_ids) > 0 else 1, "level": 1, "sort_order": 1},
            {"name": "前端开发", "code": "TECH-FE", "parent_id": None, "group_id": group_ids[0] if len(group_ids) > 0 else 1, "level": 2, "sort_order": 1},
            {"name": "后端开发", "code": "TECH-BE", "parent_id": None, "group_id": group_ids[0] if len(group_ids) > 0 else 1, "level": 2, "sort_order": 2},
            {"name": "Vue3 规范", "code": "TECH-FE-VUE", "parent_id": None, "group_id": group_ids[0] if len(group_ids) > 0 else 1, "level": 3, "sort_order": 1},
            {"name": "产品文档", "code": "PROD", "parent_id": None, "group_id": group_ids[1] if len(group_ids) > 1 else 2, "level": 1, "sort_order": 2},
            {"name": "需求文档", "code": "PROD-REQ", "parent_id": None, "group_id": group_ids[1] if len(group_ids) > 1 else 2, "level": 2, "sort_order": 1},
            {"name": "原型设计", "code": "PROD-PROTO", "parent_id": None, "group_id": group_ids[1] if len(group_ids) > 1 else 2, "level": 2, "sort_order": 2},
            {"name": "运营资料", "code": "OPS", "parent_id": None, "group_id": group_ids[2] if len(group_ids) > 2 else 3, "level": 1, "sort_order": 3},
            {"name": "活动策划", "code": "OPS-ACT", "parent_id": None, "group_id": group_ids[2] if len(group_ids) > 2 else 3, "level": 2, "sort_order": 1},
            {"name": "数据分析", "code": "OPS-DATA", "parent_id": None, "group_id": group_ids[2] if len(group_ids) > 2 else 3, "level": 2, "sort_order": 2},
        ]
        
        created_categories = {}
        root_ids = []
        
        for i, cat_data in enumerate(default_categories):
            existing = db.query(Category).filter(Category.code == cat_data["code"]).first()
            if not existing:
                cat = Category(
                    name=cat_data["name"],
                    code=cat_data["code"],
                    group_id=cat_data["group_id"],
                    level=cat_data["level"],
                    sort_order=cat_data["sort_order"],
                    is_active=True,
                    path=""
                )
                db.add(cat)
                db.flush()
                created_categories[i] = cat.id
                if cat_data["level"] == 1:
                    root_ids.append(cat.id)
            else:
                created_categories[i] = existing.id
                if existing.level == 1:
                    root_ids.append(existing.id)
        
        db.commit()
        
        parent_mapping = {
            1: 0,
            2: 0,
            3: 0,
            4: 1,
            5: None,
            6: 4,
            7: 4,
            8: None,
            9: 7,
            10: 7,
        }
        
        for i, cat_data in enumerate(default_categories):
            cat_id = created_categories[i]
            cat = db.query(Category).filter(Category.id == cat_id).first()
            if cat:
                parent_idx = parent_mapping.get(i)
                if parent_idx is not None and parent_idx in created_categories:
                    cat.parent_id = created_categories[parent_idx]
                
                if cat.parent_id:
                    parent = db.query(Category).filter(Category.id == cat.parent_id).first()
                    if parent:
                        cat.path = f"{parent.path}/{cat.id}"
                        cat.level = parent.level + 1
                else:
                    cat.path = str(cat.id)
                
                db.add(cat)
        
        db.commit()
        
        if employee1:
            sample_knowledge = [
                {
                    "title": "Vue3 组合式API最佳实践",
                    "content": "本文介绍Vue3组合式API的最佳实践，包括响应式数据、生命周期、自定义钩子等。",
                    "category_id": created_categories.get(3),
                    "submitter_id": employee1.id,
                    "review_status": "approved"
                },
                {
                    "title": "Python FastAPI 性能优化指南",
                    "content": "FastAPI性能优化的各种技巧，包括异步处理、数据库连接池、缓存等。",
                    "category_id": created_categories.get(2),
                    "submitter_id": employee1.id,
                    "review_status": "pending"
                },
                {
                    "title": "产品需求文档模板",
                    "content": "标准的产品需求文档模板，包含背景、目标、用户故事、功能规格等。",
                    "category_id": created_categories.get(5),
                    "submitter_id": employee1.id,
                    "review_status": "approved"
                },
            ]
            
            for k_data in sample_knowledge:
                if k_data["category_id"]:
                    existing = db.query(Knowledge).filter(Knowledge.title == k_data["title"]).first()
                    if not existing:
                        k = Knowledge(**k_data)
                        db.add(k)
            
            db.commit()
        
        print("数据库初始化完成！")
        print("默认账号：")
        print("  管理员：admin / 123456")
        print("  员工：employee1 / 123456")
        print("  员工：employee2 / 123456")
        print("  主管：supervisor1 / 123456")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
