import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.utils.redis_client import get_redis_client

# 测试环境使用非 Secure Cookie，确保 TestClient 正确发送 Cookie
settings.DEBUG = True

TEST_USER = {"username": "admin", "password": "Admin@123456"}


@pytest.fixture(autouse=True)
def _clear_redis_test_state():
    for key in get_redis_client().scan_iter(match="rate_limit:testclient:*"):
        get_redis_client().delete(key)
    for key in get_redis_client().scan_iter(match="token:blacklist:*"):
        get_redis_client().delete(key)
    for key in get_redis_client().scan_iter(match="login_fail:*"):
        get_redis_client().delete(key)
    for key in get_redis_client().scan_iter(match="login_lock:*"):
        get_redis_client().delete(key)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    r = client.post("/api/v1/auth/login", json=TEST_USER)
    if r.status_code != 200:
        raise RuntimeError(f"Login failed: {r.status_code} {r.text}")
    if "access_token" not in r.cookies:
        raise RuntimeError("access_token cookie not set")
    yield client
    client.post("/api/v1/auth/logout")


@pytest.fixture
def db_session():
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
