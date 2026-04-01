import uuid
from typing import Annotated

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


def get_current_user_id(x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None) -> uuid.UUID:
    if x_user_id:
        try:
            return uuid.UUID(x_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid X-User-Id") from exc
    return uuid.UUID(settings.default_user_id)


def ensure_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user:
        return user

    user = User(
        id=user_id,
        email=f"{str(user_id)[:8]}@local.dev",
        password_hash="mvp-no-auth",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def bootstrap_default_user(db: Session) -> None:
    ensure_user(db, uuid.UUID(settings.default_user_id))

