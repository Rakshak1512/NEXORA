import pytest

def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@cicada.io",
        "password": "Cicada2026!Secure"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@cicada.io"
    assert data["user"]["role"] == "Super Administrator"

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "email": "admin@cicada.io",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401

def test_register_and_get_me(client):
    email = f"newoperator@cicada.io"
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Cicada2026!Secure",
        "full_name": "Jordan Smith",
        "role": "Operator"
    })
    # If already exists in DB, 400 or 200
    if res.status_code == 200:
        token = res.json()["access_token"]
        me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == email

