"""Auth 模块集成测试 - 覆盖 spec 中所有场景"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base

# 使用 SQLite 内存数据库进行测试，StaticPool 确保共享同一连接
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前重建数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    startup_handlers = app.router.on_startup.copy()
    app.router.on_startup.clear()
    with TestClient(app) as c:
        yield c
    app.router.on_startup.extend(startup_handlers)
    app.dependency_overrides.clear()


class TestRegister:
    """注册相关测试"""

    def test_register_success(self, client):
        """注册成功应返回 token 对"""
        resp = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        """重复邮箱注册应返回 409"""
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        resp = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password456"
        })
        assert resp.status_code == 409

    def test_register_invalid_email(self, client):
        """无效邮箱应返回 422"""
        resp = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "password123"
        })
        assert resp.status_code == 422

    def test_register_short_password(self, client):
        """密码少于8位应返回 422"""
        resp = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "short"
        })
        assert resp.status_code == 422


class TestLogin:
    """登录相关测试"""

    def test_login_success(self, client):
        """正确凭证应返回 token"""
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client):
        """错误密码应返回 401"""
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        """不存在的邮箱应返回 401"""
        resp = client.post("/api/v1/auth/login", json={
            "email": "noone@example.com",
            "password": "password123"
        })
        assert resp.status_code == 401


class TestRefresh:
    """Token 刷新测试"""

    def test_refresh_success(self, client):
        """有效 refresh token 应返回新 access token"""
        resp = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        refresh_token = resp.json()["refresh_token"]
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_invalid_token(self, client):
        """无效 refresh token 应返回 401"""
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })
        assert resp.status_code == 401


class TestLogout:
    """登出测试"""

    def test_logout_success(self, client):
        """登出应返回 200"""
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200


class TestPasswordReset:
    """密码重置测试"""

    def test_forgot_password_existing_email(self, client):
        """已注册邮箱请求重置应返回 200"""
        client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123"
        })
        resp = client.post("/api/v1/auth/forgot-password", json={
            "email": "test@example.com"
        })
        assert resp.status_code == 200

    def test_forgot_password_nonexistent_email(self, client):
        """不存在的邮箱请求重置也应返回 200（不泄露信息）"""
        resp = client.post("/api/v1/auth/forgot-password", json={
            "email": "noone@example.com"
        })
        assert resp.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """无效 token 重置密码应返回 400"""
        resp = client.post("/api/v1/auth/reset-password", json={
            "token": "invalid.token",
            "new_password": "newpassword123"
        })
        assert resp.status_code == 400
