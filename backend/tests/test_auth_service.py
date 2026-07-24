import pytest
from fastapi import HTTPException
from jose import jwt

from backend.app.config import settings
from backend.app.schemas import UserLogin, UserCreate
from backend.app.services.auth_service import AuthService
from backend.app.utils.security import verify_password, hash_password


class TestAuthService:
    def test_login_success(self, db, make_user):
        user = make_user(username="alice", password="secret123", role="employee", name="Alice")
        login_data = UserLogin(username="alice", password="secret123", role="employee")

        result = AuthService.login(db, login_data)
        assert result["username"] == "alice"
        assert result["role"] == "employee"
        assert result["name"] == "Alice"
        assert result["id"] == user.id
        assert "token" in result

        payload = jwt.decode(result["token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == str(user.id)
        assert payload["role"] == "employee"

    def test_login_wrong_password(self, db, make_user):
        make_user(username="bob", password="correct", role="employee", name="Bob")
        login_data = UserLogin(username="bob", password="wrong", role="employee")

        with pytest.raises(HTTPException) as exc:
            AuthService.login(db, login_data)
        assert exc.value.status_code == 401
        assert "用户名或密码错误" in exc.value.detail

    def test_login_nonexistent_user(self, db):
        login_data = UserLogin(username="ghost", password="whatever", role="employee")

        with pytest.raises(HTTPException) as exc:
            AuthService.login(db, login_data)
        assert exc.value.status_code == 401

    def test_login_role_mismatch(self, db, make_user):
        make_user(username="carol", password="pw", role="employee", name="Carol")
        login_data = UserLogin(username="carol", password="pw", role="supervisor")

        with pytest.raises(HTTPException) as exc:
            AuthService.login(db, login_data)
        assert exc.value.status_code == 401
        assert "角色不匹配" in exc.value.detail

    def test_create_user_success(self, db):
        user_data = UserCreate(
            username="newuser",
            password="init1234",
            role="employee",
            name="新用户",
        )

        user = AuthService.create_user(db, user_data)

        assert user.id is not None
        assert user.username == "newuser"
        assert user.role == "employee"
        assert user.name == "新用户"
        assert verify_password("init1234", user.password_hash)

    def test_create_user_duplicate_username(self, db, make_user):
        make_user(username="dup", password="pw", role="employee", name="Dup")
        user_data = UserCreate(username="dup", password="pw2", role="employee", name="Dup2")

        with pytest.raises(HTTPException) as exc:
            AuthService.create_user(db, user_data)
        assert exc.value.status_code == 400
        assert "用户名已存在" in exc.value.detail

    def test_get_current_user_info_found(self, db, make_user):
        user = make_user(username="dave", password="pw", role="admin", name="Dave")
        result = AuthService.get_current_user_info(db, user.id)
        assert result.id == user.id
        assert result.username == "dave"

    def test_get_current_user_info_not_found(self, db):
        with pytest.raises(HTTPException) as exc:
            AuthService.get_current_user_info(db, 99999)
        assert exc.value.status_code == 404

    def test_hash_password_verify_roundtrip(self):
        h = hash_password("plain-text-pw")
        assert h != "plain-text-pw"
        assert verify_password("plain-text-pw", h)
        assert not verify_password("other", h)
