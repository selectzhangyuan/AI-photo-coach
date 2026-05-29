"""用户资料相关 Schema"""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """用户资料响应"""
    id: uuid.UUID
    email: str
    nickname: str | None = None
    avatar_url: str | None = None
    is_verified: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """更新资料请求"""
    nickname: str | None = Field(None, max_length=50)
    avatar_url: str | None = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    current_password: str
    new_password: str = Field(..., min_length=8)
