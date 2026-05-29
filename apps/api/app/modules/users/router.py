"""用户资料路由"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token, verify_password, hash_password
from app.models.user import User
from app.schemas.user import UserProfile, UpdateProfileRequest, ChangePasswordRequest

router = APIRouter(prefix="/users", tags=["用户"])
security = HTTPBearer()


def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """临时认证依赖（Task5 会统一到 deps.py）"""
    payload = verify_token(credentials.credentials)
    user = db.get(User, uuid.UUID(payload.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("/me", response_model=UserProfile)
def get_my_profile(current_user: User = Depends(_get_current_user)):
    """获取当前用户资料"""
    return current_user


@router.patch("/me", response_model=UserProfile)
def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户资料（昵称、头像）"""
    if payload.nickname is not None:
        current_user.nickname = payload.nickname
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码"""
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth-only account",
        )
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
