import pytest
from auth_helpers import login_as_platform_admin

def test_login_success(client):
    token = login_as_platform_admin(client)
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@cynera.io"
    assert me.json()["role"] == "Super Administrator"

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@cynera.io",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401

def test_legacy_registration_is_disabled(client):
    res = client.post("/api/auth/register", json={
        "email": "newoperator@cynera.io",
        "password": "Cynera2026!Secure",
        "full_name": "Jordan Smith",
        "role": "Operator"
    })
    assert res.status_code == 410
    assert "register-org" in res.json()["detail"]

@pytest.mark.parametrize(
    ("email", "expected_role"),
    [
        ("admin@cynera.io", "Super Administrator"),
        ("owner@cynera.io", "Organization Owner"),
    ],
)
def test_development_demo_login(client, email, expected_role):
    res = client.post("/api/auth/demo-login", json={"email": email})
    assert res.status_code == 200
    assert res.json()["user"]["email"] == email
    assert res.json()["user"]["role"] == expected_role
    assert res.json()["access_token"]


def test_demo_login_rejects_unlisted_account(client):
    res = client.post("/api/auth/demo-login", json={"email": "unknown@cynera.io"})
    assert res.status_code == 403
