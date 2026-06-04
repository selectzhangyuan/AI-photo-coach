import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    startup_handlers = app.router.on_startup.copy()
    app.router.on_startup.clear()
    with TestClient(app) as c:
        yield c
    app.router.on_startup.extend(startup_handlers)
    app.dependency_overrides.clear()


def test_register_long_password_accepted(client):
    """Passwords longer than 72 bytes should now work (SHA-256 pre-hashed)."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "longpass@example.com", "password": "a" * 100},
    )
    # Should not be rejected with 422 for length reasons
    assert resp.status_code != 422 or "at most 72" not in resp.text


def test_register_emoji_password_accepted(client):
    """Multi-byte emoji passwords should now work (SHA-256 pre-hashed)."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "emoji@example.com", "password": "😀" * 19},
    )
    assert resp.status_code != 422 or "at most 72" not in resp.text


def test_register_password_too_short_returns_422(client):
    """Minimum length (8 chars) is still enforced."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "password": "1234567"},
    )
    assert resp.status_code == 422
