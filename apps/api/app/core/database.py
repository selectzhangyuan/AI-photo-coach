from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.base import Base

engine = create_engine(settings.db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# alembic.ini 位于 apps/api/alembic.ini，即 database.py 的上两级目录
_ALEMBIC_INI = str(Path(__file__).resolve().parent.parent.parent / "alembic.ini")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """应用所有待执行的 Alembic 迁移。

    替代了过去的 Base.metadata.create_all() + 手写 SQL 方式，
    确保所有的 schema 变更都经过版本控制。
    """
    import app.models  # noqa: F401 — 确保所有模型已注册

    alembic_cfg = Config(_ALEMBIC_INI)
    # 确保 alembic 使用与 app 相同的数据库 URL
    alembic_cfg.set_main_option("sqlalchemy.url", settings.db_url)
    command.upgrade(alembic_cfg, "head")
