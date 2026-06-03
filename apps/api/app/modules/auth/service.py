"""认证服务 - 策略模式预留多 provider"""
import logging
import uuid
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""

    def __init__(self, db: Session):
        self.db = db

    def register_with_password(self, email: str, password: str, nickname: str | None = None) -> User:
        """邮箱+密码注册"""
        # 检查邮箱是否已存在
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            nickname=nickname,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login_with_password(self, email: str, password: str) -> dict:
        """邮箱+密码登录，返回 token 对"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh_tokens(self, refresh_token: str) -> dict:
        """用 refresh_token 换新 access_token"""
        payload = verify_token(refresh_token)  # 会自动抛 401 如果无效/过期
        # 验证用户仍然存在且活跃
        user = self.db.get(User, uuid.UUID(payload.sub))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        new_access_token = create_access_token(subject=str(user.id))
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,  # refresh token 不变
            "token_type": "bearer",
        }

    def create_email_verification_token(self, user_id: str) -> str:
        """生成邮箱验证 token（使用短期JWT）"""
        return create_access_token(subject=user_id, expires_delta=timedelta(hours=24))

    def verify_email(self, token: str) -> None:
        """验证邮箱"""
        try:
            payload = verify_token(token)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )
        user = self.db.get(User, uuid.UUID(payload.sub))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )
        user.is_verified = True
        self.db.commit()

    def forgot_password(self, email: str) -> None:
        """发送密码重置 token（开发模式记录日志）"""
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            reset_token = create_access_token(subject=str(user.id), expires_delta=timedelta(hours=1))
            # 开发模式：输出到日志
            logger.info("Password reset token generated", extra={"email": email})

    def reset_password(self, token: str, new_password: str) -> None:
        """用 reset token 重置密码"""
        try:
            payload = verify_token(token)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )
        user = self.db.get(User, uuid.UUID(payload.sub))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )
        user.password_hash = hash_password(new_password)
        self.db.commit()

    # OAuth2 预留接口 (暂不实现)
    # async def login_with_oauth(self, provider: str, code: str) -> dict: ...
    # async def link_oauth_provider(self, user_id: str, provider: str, code: str) -> None: ...
