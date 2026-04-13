import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.base_all import Base  # noqa: F401
from app.models.user import Role, Permission
from app.core.security import get_password_hash
from app.core.constants import PermissionCode
from app.crud.role import crud_role, PREDEFINED_ROLES

client = TestClient(app)


def _admin_login():
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@123456"})
    assert r.status_code == 200
    return r.cookies.get("access_token")


class TestRoleCrud:
    def test_create_role(self):
        import uuid
        role_name = f"test_role_create_{uuid.uuid4().hex[:8]}"
        token = _admin_login()
        r = client.post(
            "/api/v1/roles",
            json={"name": role_name, "description": "test", "data_scope": "self", "permission_ids": []},
            cookies={"access_token": token},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == role_name

    def test_list_roles(self):
        token = _admin_login()
        r = client.get("/api/v1/roles", cookies={"access_token": token})
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

    def test_get_role(self):
        token = _admin_login()
        db = SessionLocal()
        role = db.query(Role).filter(Role.name == "admin").first()
        db.close()
        r = client.get(f"/api/v1/roles/{role.id}", cookies={"access_token": token})
        assert r.status_code == 200
        assert r.json()["name"] == "admin"

    def test_update_role(self):
        token = _admin_login()
        db = SessionLocal()
        role = db.query(Role).filter(Role.name == "test_role_create").first()
        if not role:
            role = Role(name="test_role_create", description="tmp", data_scope="SELF")
            db.add(role)
            db.commit()
            db.refresh(role)
        role_id = role.id
        db.close()
        r = client.put(
            f"/api/v1/roles/{role_id}",
            json={"name": "test_role_create", "description": "updated desc"},
            cookies={"access_token": token},
        )
        assert r.status_code == 200
        assert r.json()["description"] == "updated desc"

    def test_delete_custom_role(self):
        token = _admin_login()
        db = SessionLocal()
        role = db.query(Role).filter(Role.name == "test_role_create").first()
        if not role:
            role = Role(name="test_role_create", description="tmp", data_scope="SELF")
            db.add(role)
            db.commit()
            db.refresh(role)
        role_id = role.id
        db.close()
        r = client.delete(f"/api/v1/roles/{role_id}", cookies={"access_token": token})
        assert r.status_code == 200


class TestPredefinedRoles:
    @pytest.mark.parametrize("role_name", list(PREDEFINED_ROLES))
    def test_predefined_role_cannot_be_deleted(self, role_name):
        token = _admin_login()
        db = SessionLocal()
        role = db.query(Role).filter(Role.name == role_name).first()
        db.close()
        if not role:
            pytest.skip(f"Role {role_name} not found in DB")
        r = client.delete(f"/api/v1/roles/{role.id}", cookies={"access_token": token})
        assert r.status_code == 403
        assert "预定义角色不能删除" in r.json()["detail"]

    def test_admin_has_all_permissions(self):
        db = SessionLocal()
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        assert admin_role is not None
        perm_codes = {p.code for p in admin_role.permissions}
        all_codes = {p.value for p in PermissionCode}
        assert perm_codes == all_codes
        db.close()
