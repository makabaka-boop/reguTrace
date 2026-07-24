import pytest
from fastapi import HTTPException
from backend.app.services.auth_service import AuthService
from backend.app.schemas import UserLogin, UserCreate
from backend.app.utils.security import verify_password


class TestAuthService:

    def test_login_success(self, db, test_employee):
        login_data = UserLogin(username="employee", password="emp123", role="employee")
        result = AuthService.login(db, login_data)

        assert result["username"] == "employee"
        assert result["role"] == "employee"
        assert result["name"] == "普通员工"
        assert "token" in result
        assert result["id"] == test_employee.id

    def test_login_wrong_password(self, db, test_employee):
        login_data = UserLogin(username="employee", password="wrongpass", role="employee")
        with pytest.raises(HTTPException) as exc_info:
            AuthService.login(db, login_data)
        assert exc_info.value.status_code == 401
        assert "用户名或密码错误" in exc_info.value.detail

    def test_login_nonexistent_user(self, db):
        login_data = UserLogin(username="nobody", password="pass123", role="employee")
        with pytest.raises(HTTPException) as exc_info:
            AuthService.login(db, login_data)
        assert exc_info.value.status_code == 401

    def test_login_role_mismatch(self, db, test_employee):
        login_data = UserLogin(username="employee", password="emp123", role="admin")
        with pytest.raises(HTTPException) as exc_info:
            AuthService.login(db, login_data)
        assert exc_info.value.status_code == 401
        assert "角色不匹配" in exc_info.value.detail

    def test_login_admin(self, db, test_admin):
        login_data = UserLogin(username="admin", password="admin123", role="admin")
        result = AuthService.login(db, login_data)
        assert result["role"] == "admin"
        assert result["token"] is not None

    def test_login_supervisor(self, db, test_supervisor):
        login_data = UserLogin(username="supervisor", password="sup123", role="supervisor")
        result = AuthService.login(db, login_data)
        assert result["role"] == "supervisor"

    def test_create_user_success(self, db):
        user_data = UserCreate(
            username="newuser",
            password="password123",
            role="employee",
            name="新用户"
        )
        result = AuthService.create_user(db, user_data)

        assert result.username == "newuser"
        assert result.role == "employee"
        assert result.name == "新用户"
        assert verify_password("password123", result.password_hash)

    def test_create_user_duplicate_username(self, db, test_employee):
        user_data = UserCreate(
            username="employee",
            password="pass123",
            role="employee",
            name="重复用户"
        )
        with pytest.raises(HTTPException) as exc_info:
            AuthService.create_user(db, user_data)
        assert exc_info.value.status_code == 400
        assert "用户名已存在" in exc_info.value.detail

    def test_get_current_user_info_success(self, db, test_employee):
        result = AuthService.get_current_user_info(db, test_employee.id)
        assert result.username == "employee"
        assert result.name == "普通员工"

    def test_get_current_user_info_not_found(self, db):
        with pytest.raises(HTTPException) as exc_info:
            AuthService.get_current_user_info(db, 99999)
        assert exc_info.value.status_code == 404
        assert "用户不存在" in exc_info.value.detail
