import os
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import (
    User,
    UserGroup,
    Category,
    Knowledge,
    ReadingStatus,
    ReviewRecord,
    NodeSummary,
)
from backend.app.utils.security import hash_password

_TRIGGERS_SQL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app",
    "triggers",
    "summary_triggers.sql",
)


def _load_triggers(engine):
    with open(_TRIGGERS_SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.connect() as conn:
        raw_conn = conn.connection.dbapi_connection
        raw_conn.executescript(sql)
        raw_conn.commit()


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=eng)
    _load_triggers(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def make_user(db):
    def _make(
        username="employee1",
        password="password123",
        role="employee",
        name="测试用户",
    ):
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            name=name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture()
def make_group(db):
    def _make(name="默认小组", description=""):
        group = UserGroup(name=name, description=description)
        db.add(group)
        db.commit()
        db.refresh(group)
        return group

    return _make


@pytest.fixture()
def make_category(db):
    def _make(
        name="分类A",
        code=None,
        parent_id=None,
        group_id=None,
        sort_order=0,
        is_active=True,
    ):
        if parent_id is None:
            level = 1
            path = ""
        else:
            parent = db.query(Category).filter(Category.id == parent_id).first()
            level = parent.level + 1
            path = f"{parent.path}/{parent.id}"

        category = Category(
            name=name,
            code=code,
            parent_id=parent_id,
            group_id=group_id,
            sort_order=sort_order,
            is_active=is_active,
            level=level,
            path=path,
        )
        db.add(category)
        db.flush()

        if parent_id is None:
            category.path = str(category.id)
        else:
            category.path = f"{path}/{category.id}"

        db.commit()
        db.refresh(category)

        summary = NodeSummary(
            category_id=category.id,
            total_count=0,
            pending_count=0,
        )
        db.add(summary)
        db.commit()
        return category

    return _make


@pytest.fixture()
def make_knowledge(db):
    def _make(
        title="制度标题",
        content="<p>制度内容</p>",
        category_id=1,
        submitter_id=1,
        review_status="pending",
        suggested_review_cycle="6months",
        next_review_date=None,
    ):
        k = Knowledge(
            title=title,
            content=content,
            category_id=category_id,
            submitter_id=submitter_id,
            review_status=review_status,
            suggested_review_cycle=suggested_review_cycle,
            next_review_date=next_review_date,
        )
        db.add(k)
        db.commit()
        db.refresh(k)
        return k

    return _make


@pytest.fixture()
def make_reading(db):
    def _make(knowledge_id, user_id, is_read=True):
        r = ReadingStatus(
            knowledge_id=knowledge_id,
            user_id=user_id,
            is_read=is_read,
            read_at=datetime.now(),
        )
        db.add(r)
        db.commit()
        db.refresh(r)
        return r

    return _make
