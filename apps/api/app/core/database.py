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
        "ALTER TABLE image_assets ADD COLUMN IF NOT EXISTS parent_image_id UUID",
        "ALTER TABLE image_assets ADD COLUMN IF NOT EXISTS asset_type VARCHAR(16) DEFAULT 'original'",
        "ALTER TABLE analysis_tasks ADD COLUMN IF NOT EXISTS task_type VARCHAR(32) DEFAULT 'ANALYZE'",
        "ALTER TABLE analysis_tasks ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128)",
        (
            "CREATE INDEX IF NOT EXISTS idx_analysis_tasks_task_type_created "
            "ON analysis_tasks (task_type, created_at)"
        ),
    ]

    with engine.begin() as connection:
        for statement in updates:
            connection.execute(text(statement))
