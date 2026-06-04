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


def test_register_password_too_long_returns_422(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "longpass@example.com", "password": "a" * 73},
    )

    assert resp.status_code == 422


def test_reset_password_too_long_returns_422(client):
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid.token", "new_password": "a" * 73},
    )

    assert resp.status_code == 422


def test_register_password_too_long_in_utf8_bytes_returns_422(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "emoji@example.com", "password": "😀" * 19},
    )

    assert resp.status_code == 422
