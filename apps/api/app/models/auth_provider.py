"""第三方登录绑定记录 - OAuth2 预留表"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class AuthProvider(Base):
    """第三方登录绑定记录 - 预留表，暂不启用"""
    __tablename__ = "auth_providers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20))  # "google", "github", "wechat"
    provider_user_id: Mapped[str] = mapped_column(String)
    access_token: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
