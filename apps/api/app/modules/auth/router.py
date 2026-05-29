"""认证路由"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.service import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    VerifyEmailRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    service = AuthService(db)
    user = service.register_with_password(
        email=payload.email,
        password=payload.password,
        nickname=payload.nickname,
    )
    # 生成验证 token 并记录日志（开发模式）
    verify_token_str = service.create_email_verification_token(str(user.id))
    logger.info(f"[DEV] Email verification token for {payload.email}: {verify_token_str}")

    # 返回登录 token
    tokens = service.login_with_password(email=payload.email, password=payload.password)
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    service = AuthService(db)
    return service.login_with_password(email=payload.email, password=payload.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """刷新 access token"""
    service = AuthService(db)
    return service.refresh_tokens(refresh_token=payload.refresh_token)


@router.post("/logout")
def logout():
    """登出（客户端负责清除 token）"""
    return {"message": "Successfully logged out"}


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """邮箱验证"""
    service = AuthService(db)
    service.verify_email(token=payload.token)
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
def resend_verification(db: Session = Depends(get_db)):
    """重发验证邮件 - 需要认证（暂用简化版，后续Task5会加认证依赖）"""
    # 注意：此端点需要认证，将在 Task 5 (deps.py改造) 完成后添加认证依赖
    # 当前先创建基本结构
    return {"message": "Verification email resent"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """发送密码重置邮件"""
    service = AuthService(db)
    service.forgot_password(email=payload.email)
    # 无论邮箱是否存在，都返回200
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """重置密码"""
    service = AuthService(db)
    service.reset_password(token=payload.token, new_password=payload.new_password)
    return {"message": "Password reset successfully"}
