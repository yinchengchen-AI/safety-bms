TEST_USER = {"username": "admin", "password": "Admin@123456"}


def test_login_issues_cookie(client):
    r = client.post("/api/v1/auth/login", json=TEST_USER)
    assert r.status_code == 200
    assert "access_token" in r.cookies


def test_me_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_with_cookie(authenticated_client):
    r = authenticated_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_logout_clears_cookie(authenticated_client):
    r = authenticated_client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    # 再次访问应 401
    r2 = authenticated_client.get("/api/v1/auth/me")
    assert r2.status_code == 401
