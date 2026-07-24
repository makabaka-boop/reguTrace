"""认证服务单元测试：登录鉴权、用户创建、当前用户查询。"""
import pytest
from fastapi import HTTPException

from backend.app.services.auth_service import AuthService
from backend.app.schemas import UserLogin, UserCreate
from backend.app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from jose import jwt
from backend.app.config import settings


class TestLogin:
    def test_login_success_returns_token_and_profile(self, db_session, users):
        result = AuthService.login(
            db_session, UserLogin(username="employee01", password="emp-pass", role="employee")
        )
        assert result["id"] == users["employee"].id
        assert result["username"] == "employee01"
        assert result["role"] == "employee"
        assert result["token"]

    def test_login_token_payload_contains_user_id_and_role(self, db_session, users):
        result = AuthService.login(
            db_session, UserLogin(username="supervisor01", password="sup-pass", role="supervisor")
        )
        payload = jwt.decode(result["token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == str(users["supervisor"].id)
        assert payload["role"] == "supervisor"

    def test_login_nonexistent_user_raises_401(self, db_session, users):
        with pytest.raises(HTTPException) as exc:
            AuthService.login(
                db_session, UserLogin(username="ghost", password="x", role="employee")
            )
        assert exc.value.status_code == 401
        assert exc.value.detail == "用户名或密码错误"

    def test_login_wrong_password_raises_401(self, db_session, users):
        with pytest.raises(HTTPException) as exc:
            AuthService.login(
                db_session, UserLogin(username="employee01", password="wrong", role="employee")
            )
        assert exc.value.status_code == 401
        assert exc.value.detail == "用户名或密码错误"

    def test_login_role_mismatch_raises_401(self, db_session, users):
        with pytest.raises(HTTPException) as exc:
            AuthService.login(
                db_session, UserLogin(username="employee01", password="emp-pass", role="admin")
            )
        assert exc.value.status_code == 401
        assert exc.value.detail == "角色不匹配"

    @pytest.mark.parametrize("username,password,role", [
        ("supervisor01", "sup-pass", "supervisor"),
        ("admin01", "admin-pass", "admin"),
    ])
    def test_login_supports_all_roles(self, db_session, users, username, password, role):
        result = AuthService.login(
            db_session, UserLogin(username=username, password=password, role=role)
        )
        assert result["role"] == role


class TestCreateUser:
    def test_create_user_success_hashes_password(self, db_session):
        user = AuthService.create_user(
            db_session,
            UserCreate(username="newbie", password="plain-pass", role="employee", name="新人"),
        )
        assert user.id is not None
        assert user.username == "newbie"
        # 密码应被哈希存储，且可通过校验
        assert user.password_hash != "plain-pass"
        assert verify_password("plain-pass", user.password_hash)

    def test_create_user_duplicate_username_raises_400(self, db_session, users):
        with pytest.raises(HTTPException) as exc:
            AuthService.create_user(
                db_session,
                UserCreate(username="employee01", password="p", role="employee", name="重复"),
            )
        assert exc.value.status_code == 400
        assert exc.value.detail == "用户名已存在"


class TestGetCurrentUserInfo:
    def test_get_current_user_info_success(self, db_session, users):
        user = AuthService.get_current_user_info(db_session, users["admin"].id)
        assert user.username == "admin01"

    def test_get_current_user_info_not_found_raises_404(self, db_session, users):
        with pytest.raises(HTTPException) as exc:
            AuthService.get_current_user_info(db_session, 999999)
        assert exc.value.status_code == 404
        assert exc.value.detail == "用户不存在"


class TestSecurityUtils:
    def test_hash_and_verify_password(self):
        hashed = hash_password("secret")
        assert verify_password("secret", hashed)
        assert not verify_password("other", hashed)

    def test_create_access_token_is_decodable(self):
        token = create_access_token({"sub": "1", "role": "employee"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "1"
        assert "exp" in payload
