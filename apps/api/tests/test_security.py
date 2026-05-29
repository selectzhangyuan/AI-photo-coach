"""security 模块单元测试 - TDD: 先写测试"""
import pytest
from datetime import timedelta
import time

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """密码哈希相关测试"""

    def test_hash_password_returns_hash(self):
        """哈希密码应返回非明文字符串"""
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """正确密码应验证通过"""
        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_password_incorrect(self):
        """错误密码应验证失败"""
        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        """不同密码应产生不同哈希"""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2


class TestTokenCreation:
    """Token 创建相关测试"""

    def test_create_access_token(self):
        """应成功创建 access token"""
        token = create_access_token(subject="user-uuid-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """应成功创建 refresh token"""
        token = create_refresh_token(subject="user-uuid-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_with_custom_expiry(self):
        """自定义过期时间应生效"""
        token = create_access_token(
            subject="user-uuid-123",
            expires_delta=timedelta(minutes=5)
        )
        payload = verify_token(token)
        assert payload.sub == "user-uuid-123"


class TestTokenVerification:
    """Token 验证相关测试"""

    def test_verify_valid_access_token(self):
        """有效 token 应验证成功并返回 payload"""
        token = create_access_token(subject="user-uuid-123")
        payload = verify_token(token)
        assert payload.sub == "user-uuid-123"

    def test_verify_valid_refresh_token(self):
        """有效 refresh token 应验证成功"""
        token = create_refresh_token(subject="user-uuid-456")
        payload = verify_token(token)
        assert payload.sub == "user-uuid-456"

    def test_verify_invalid_token_raises(self):
        """无效 token 应抛出异常"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token.string")
        assert exc_info.value.status_code == 401

    def test_verify_expired_token_raises(self):
        """过期 token 应抛出异常"""
        from fastapi import HTTPException
        token = create_access_token(
            subject="user-uuid-123",
            expires_delta=timedelta(seconds=-1)  # 已过期
        )
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401
