"""Users 模块集成测试"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.core.security import create_access_token, hash_password

# SQLite 测试数据库（仅创建 users 表，避免 JSONB 等PG专有类型问题）
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前后创建/销毁 users 表"""
    User.__table__.create(bind=engine, checkfirst=True)
    yield
    User.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture
def client():
    """创建测试客户端，覆盖数据库依赖，禁用 startup 事件"""
    app.dependency_overrides[get_db] = override_get_db
    # 禁用 startup 事件（避免连接 PostgreSQL）
    startup_handlers = app.router.on_startup.copy()
    app.router.on_startup.clear()
    with TestClient(app) as c:
        yield c
    # 恢复 startup 事件
    app.router.on_startup.extend(startup_handlers)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_id():
    """测试用户 ID"""
    return uuid.uuid4()


@pytest.fixture
def auth_headers(test_user_id):
    """直接创建用户并生成认证头（不依赖 auth/register 端点）"""
    db = TestingSessionLocal()
    try:
        user = User(
            id=test_user_id,
            email="user@example.com",
            password_hash=hash_password("password123"),
            nickname="TestUser",
            is_active=True,
        )
        db.add(user)
        db.commit()
        token = create_access_token(subject=str(test_user_id))
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


class TestGetProfile:
    """获取资料测试"""

    def test_get_profile_success(self, client, auth_headers):
        """已认证用户应能获取资料"""
        resp = client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@example.com"
        assert data["nickname"] == "TestUser"

    def test_get_profile_unauthenticated(self, client):
        """未认证应返回 403（FastAPI HTTPBearer 默认返回 403）"""
        resp = client.get("/api/v1/users/me")
        assert resp.status_code in [401, 403]


class TestUpdateProfile:
    """更新资料测试"""

    def test_update_nickname(self, client, auth_headers):
        """应能更新昵称"""
        resp = client.patch("/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "NewName"})
        assert resp.status_code == 200
        assert resp.json()["nickname"] == "NewName"

    def test_update_avatar(self, client, auth_headers):
        """应能更新头像"""
        resp = client.patch("/api/v1/users/me",
            headers=auth_headers,
            json={"avatar_url": "https://example.com/avatar.png"})
        assert resp.status_code == 200
        assert resp.json()["avatar_url"] == "https://example.com/avatar.png"

    def test_nickname_too_long(self, client, auth_headers):
        """超过50字符的昵称应返回 422"""
        resp = client.patch("/api/v1/users/me",
            headers=auth_headers,
            json={"nickname": "a" * 51})
        assert resp.status_code == 422


class TestChangePassword:
    """修改密码测试"""

    def test_change_password_success(self, client, auth_headers):
        """正确旧密码+新密码应成功"""
        resp = client.post("/api/v1/users/me/change-password",
            headers=auth_headers,
            json={"current_password": "password123", "new_password": "newpassword123"})
        assert resp.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers):
        """错误的当前密码应返回 400"""
        resp = client.post("/api/v1/users/me/change-password",
            headers=auth_headers,
            json={"current_password": "wrongpassword", "new_password": "newpassword123"})
        assert resp.status_code == 400

    def test_change_password_too_short(self, client, auth_headers):
        """新密码过短应返回 422"""
        resp = client.post("/api/v1/users/me/change-password",
            headers=auth_headers,
            json={"current_password": "password123", "new_password": "short"})
        assert resp.status_code == 422
