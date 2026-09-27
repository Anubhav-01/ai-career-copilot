import uuid


def _register(client, email, password="S3curePassw0rd!"):
    return client.post("/api/auth/register", json={
        "email": email, "password": password, "full_name": "Auth Tester",
    })


def test_register_and_me(client):
    email = f"reg-{uuid.uuid4().hex[:8]}@example.com"
    response = _register(client, email)
    assert response.status_code == 201
    tokens = response.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = client.get("/api/auth/me",
                    headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_duplicate_email_rejected(client):
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    assert _register(client, email).status_code == 201
    response = _register(client, email)
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_weak_password_rejected(client):
    response = _register(client, f"weak-{uuid.uuid4().hex[:8]}@example.com", "short")
    assert response.status_code == 422


def test_login_wrong_password(client):
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email)
    response = client.post("/api/auth/login",
                           json={"email": email, "password": "WrongPassword1!"})
    assert response.status_code == 401


def test_refresh_rotation(client):
    email = f"rot-{uuid.uuid4().hex[:8]}@example.com"
    tokens = _register(client, email).json()

    refreshed = client.post("/api/auth/refresh",
                            json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # Old refresh token must now be revoked (rotation).
    reused = client.post("/api/auth/refresh",
                         json={"refresh_token": tokens["refresh_token"]})
    assert reused.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/dashboard").status_code == 401
    assert client.get(
        "/api/dashboard", headers={"Authorization": "Bearer not-a-token"}
    ).status_code == 401


def test_admin_route_forbidden_for_regular_user(client, auth_headers):
    response = client.get("/api/admin/stats", headers=auth_headers)
    assert response.status_code == 403
