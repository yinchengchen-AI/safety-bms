from fastapi.testclient import TestClient

from app.core.constants import PermissionCode
from app.core.security import get_password_hash
from app.db.base_all import Base  # noqa: F401
from app.db.session import SessionLocal
from app.main import app
from app.models.user import Permission, Role, User

client = TestClient(app)


def _create_user_with_perms(username: str, permission_codes: list):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user:
        db.close()
        return user

    role = Role(name=f"role_{username}", description="test role", data_scope="SELF")
    db.add(role)
    db.flush()

    for code in permission_codes:
        perm = db.query(Permission).filter(Permission.code == code).first()
        if not perm:
            perm = Permission(code=code, name=code, description=code)
            db.add(perm)
            db.flush()
        role.permissions.append(perm)

    user = User(
        username=username,
        email=f"{username}@test.com",
        full_name=username,
        hashed_password=get_password_hash("Test@123456"),
        is_active=True,
        is_superuser=False,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def _login(username: str, password: str = "Test@123456"):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.cookies.get("access_token")


class TestRequirePermissions:
    def test_allows_user_with_required_permission(self):
        _create_user_with_perms("perm_user1", [PermissionCode.CUSTOMER_READ.value])
        token = _login("perm_user1")
        r = client.get("/api/v1/customers", cookies={"access_token": token})
        assert r.status_code == 200

    def test_blocks_user_without_required_permission(self):
        _create_user_with_perms("perm_user2", [PermissionCode.CUSTOMER_READ.value])
        token = _login("perm_user2")
        # contracts:read not granted
        r = client.get("/api/v1/contracts", cookies={"access_token": token})
        assert r.status_code == 403

    def test_superuser_bypasses_permission_check(self):
        db = SessionLocal()
        user = db.query(User).filter(User.username == "super_bypass").first()
        if not user:
            user = User(
                username="super_bypass",
                email="super_bypass@test.com",
                full_name="super",
                hashed_password=get_password_hash("Test@123456"),
                is_active=True,
                is_superuser=True,
            )
            db.add(user)
            db.commit()
        db.close()
        token = _login("super_bypass")
        r = client.get("/api/v1/contracts", cookies={"access_token": token})
        assert r.status_code == 200

    def test_unauthenticated_request_401(self):
        c = TestClient(app)
        r = c.get("/api/v1/customers")
        assert r.status_code == 401
