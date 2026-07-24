"""
后端单元测试的公共夹具（fixtures）。

采用内存级 SQLite（StaticPool）替代真实数据库，保证：
- 每个测试用例拥有独立、干净的数据库；
- 无需依赖磁盘上的 knowledge_base.db 或外部服务；
- 使用小规模 mock 数据构造清晰、可维护的测试场景。
"""
import os
import sys
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 保证可以通过 `backend.app.*` 导入应用代码（项目根为 backend 的上一级目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import Base  # noqa: E402
from backend.app.models import (  # noqa: E402
    User,
    UserGroup,
    Category,
    Knowledge,
    ReadingStatus,
)
from backend.app.utils.security import hash_password  # noqa: E402


@pytest.fixture()
def db_session():
    """提供一个基于内存 SQLite 的独立会话，并在用例结束后销毁。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def users(db_session):
    """创建三种角色的基础用户：员工 / 主管 / 管理员。"""
    employee = User(
        username="employee01",
        password_hash=hash_password("emp-pass"),
        role="employee",
        name="员工张三",
    )
    supervisor = User(
        username="supervisor01",
        password_hash=hash_password("sup-pass"),
        role="supervisor",
        name="主管李四",
    )
    admin = User(
        username="admin01",
        password_hash=hash_password("admin-pass"),
        role="admin",
        name="管理员王五",
    )
    db_session.add_all([employee, supervisor, admin])
    db_session.commit()
    for u in (employee, supervisor, admin):
        db_session.refresh(u)
    return {"employee": employee, "supervisor": supervisor, "admin": admin}


@pytest.fixture()
def group(db_session):
    grp = UserGroup(name="制度小组", description="负责制度维护")
    db_session.add(grp)
    db_session.commit()
    db_session.refresh(grp)
    return grp


@pytest.fixture()
def categories(db_session, group):
    """构造两层分类树：

    根(root) -> 子(child)、根(root) -> 停用子(inactive_child)
    path 与 level 按 CategoryService 的约定填充，便于筛选类用例复用。
    """
    root = Category(
        name="人事制度",
        code="HR",
        parent_id=None,
        group_id=group.id,
        sort_order=1,
        is_active=True,
        level=1,
    )
    db_session.add(root)
    db_session.flush()
    root.path = str(root.id)

    child = Category(
        name="考勤管理",
        code="HR-ATT",
        parent_id=root.id,
        group_id=group.id,
        sort_order=1,
        is_active=True,
        level=2,
    )
    db_session.add(child)
    db_session.flush()
    child.path = f"{root.path}/{child.id}"

    inactive_child = Category(
        name="已停用目录",
        code="HR-OLD",
        parent_id=root.id,
        group_id=group.id,
        sort_order=2,
        is_active=False,
        level=2,
    )
    db_session.add(inactive_child)
    db_session.flush()
    inactive_child.path = f"{root.path}/{inactive_child.id}"

    db_session.commit()
    for c in (root, child, inactive_child):
        db_session.refresh(c)
    return {"root": root, "child": child, "inactive": inactive_child}


def _make_knowledge(db_session, *, title, category, submitter, review_status="approved",
                    cycle="6months", next_review_date=None, content="正文内容"):
    item = Knowledge(
        title=title,
        content=content,
        category_id=category.id,
        submitter_id=submitter.id,
        review_status=review_status,
        suggested_review_cycle=cycle,
        next_review_date=next_review_date,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture()
def make_knowledge(db_session):
    """返回一个工厂函数，便于各用例按需创建制度条目。"""
    def _factory(**kwargs):
        return _make_knowledge(db_session, **kwargs)
    return _factory


@pytest.fixture()
def knowledge_set(db_session, categories, users):
    """一组覆盖不同复核到期状态的制度条目，供筛选/统计类用例使用。"""
    now = datetime.now()
    employee = users["employee"]
    child = categories["child"]

    overdue = _make_knowledge(
        db_session, title="已到期制度", category=child, submitter=employee,
        review_status="approved", next_review_date=now - timedelta(days=1),
    )
    upcoming = _make_knowledge(
        db_session, title="即将到期制度", category=child, submitter=employee,
        review_status="approved", next_review_date=now + timedelta(days=10),
    )
    normal = _make_knowledge(
        db_session, title="正常制度", category=child, submitter=employee,
        review_status="approved", next_review_date=now + timedelta(days=100),
    )
    pending = _make_knowledge(
        db_session, title="待复核制度", category=child, submitter=employee,
        review_status="pending", next_review_date=None,
    )
    rejected = _make_knowledge(
        db_session, title="已驳回制度", category=child, submitter=employee,
        review_status="rejected", next_review_date=None,
    )
    return {
        "overdue": overdue,
        "upcoming": upcoming,
        "normal": normal,
        "pending": pending,
        "rejected": rejected,
    }
