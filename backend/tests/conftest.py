import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import User, Category, Knowledge, ReadingStatus, ReviewRecord, NodeSummary, UserGroup, GroupMember


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_admin(db):
    from backend.app.utils.security import hash_password
    user = User(
        username="admin",
        password_hash=hash_password("admin123"),
        role="admin",
        name="系统管理员"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_supervisor(db):
    from backend.app.utils.security import hash_password
    user = User(
        username="supervisor",
        password_hash=hash_password("sup123"),
        role="supervisor",
        name="部门主管"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_employee(db):
    from backend.app.utils.security import hash_password
    user = User(
        username="employee",
        password_hash=hash_password("emp123"),
        role="employee",
        name="普通员工"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_group(db):
    group = UserGroup(name="测试小组", description="用于测试的小组")
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@pytest.fixture
def root_category(db, test_group):
    cat = Category(
        name="行政制度",
        code="ADMIN",
        parent_id=None,
        group_id=test_group.id,
        sort_order=1,
        is_active=True,
        level=1,
        path="1"
    )
    db.add(cat)
    db.flush()
    cat.path = str(cat.id)
    db.commit()
    db.refresh(cat)
    summary = NodeSummary(category_id=cat.id, total_count=0, pending_count=0)
    db.add(summary)
    db.commit()
    return cat


@pytest.fixture
def child_category(db, root_category, test_group):
    cat = Category(
        name="考勤制度",
        code="ATTEND",
        parent_id=root_category.id,
        group_id=test_group.id,
        sort_order=1,
        is_active=True,
        level=2,
        path=f"{root_category.path}/2"
    )
    db.add(cat)
    db.flush()
    cat.path = f"{root_category.path}/{cat.id}"
    db.commit()
    db.refresh(cat)
    summary = NodeSummary(category_id=cat.id, total_count=0, pending_count=0)
    db.add(summary)
    db.commit()
    return cat


@pytest.fixture
def inactive_category(db, test_group):
    cat = Category(
        name="已停用目录",
        code="INACTIVE",
        parent_id=None,
        group_id=test_group.id,
        sort_order=2,
        is_active=False,
        level=1,
        path="3"
    )
    db.add(cat)
    db.flush()
    cat.path = str(cat.id)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def pending_knowledge(db, child_category, test_employee):
    knowledge = Knowledge(
        title="员工考勤管理办法",
        content="<p>考勤制度内容...</p>",
        category_id=child_category.id,
        submitter_id=test_employee.id,
        review_status="pending",
        suggested_review_cycle="6months"
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    return knowledge


@pytest.fixture
def approved_knowledge(db, child_category, test_employee):
    from datetime import datetime, timedelta
    knowledge = Knowledge(
        title="已审批制度",
        content="<p>已通过审批的制度内容</p>",
        category_id=child_category.id,
        submitter_id=test_employee.id,
        review_status="approved",
        suggested_review_cycle="1year",
        next_review_date=datetime.now() + timedelta(days=180)
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    return knowledge


@pytest.fixture
def overdue_knowledge(db, child_category, test_employee):
    from datetime import datetime, timedelta
    knowledge = Knowledge(
        title="已到期制度",
        content="<p>已经到期需要复核的制度</p>",
        category_id=child_category.id,
        submitter_id=test_employee.id,
        review_status="approved",
        suggested_review_cycle="3months",
        next_review_date=datetime.now() - timedelta(days=10)
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    return knowledge


@pytest.fixture
def upcoming_knowledge(db, child_category, test_employee):
    from datetime import datetime, timedelta
    knowledge = Knowledge(
        title="即将到期制度",
        content="<p>即将在30天内到期的制度</p>",
        category_id=child_category.id,
        submitter_id=test_employee.id,
        review_status="approved",
        suggested_review_cycle="6months",
        next_review_date=datetime.now() + timedelta(days=15)
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    return knowledge


@pytest.fixture
def rejected_knowledge(db, child_category, test_employee):
    knowledge = Knowledge(
        title="被驳回制度",
        content="<p>内容不符合规范</p>",
        category_id=child_category.id,
        submitter_id=test_employee.id,
        review_status="rejected",
        reject_reason="内容格式不正确",
        suggested_review_cycle="6months"
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    return knowledge
