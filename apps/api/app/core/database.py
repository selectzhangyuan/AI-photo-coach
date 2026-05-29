from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.base import Base

engine = create_engine(settings.db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    apply_dev_schema_updates()


def apply_dev_schema_updates() -> None:
    updates = [
        # image_assets 增量更新
        "ALTER TABLE image_assets ADD COLUMN IF NOT EXISTS parent_image_id UUID",
        "ALTER TABLE image_assets ADD COLUMN IF NOT EXISTS asset_type VARCHAR(16) DEFAULT 'original'",
        # analysis_tasks 增量更新
        "ALTER TABLE analysis_tasks ADD COLUMN IF NOT EXISTS task_type VARCHAR(32) DEFAULT 'ANALYZE'",
        "ALTER TABLE analysis_tasks ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128)",
        (
            "CREATE INDEX IF NOT EXISTS idx_analysis_tasks_task_type_created "
            "ON analysis_tasks (task_type, created_at)"
        ),
        # users 表新增列
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE",
    ]

    with engine.begin() as connection:
        for statement in updates:
            connection.execute(text(statement))
