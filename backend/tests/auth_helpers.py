from unittest.mock import patch

def login_as_platform_admin(client, email="admin@cynera.io", password="Cynera2026!Secure"):
    """Exercise the real mandatory email-OTP login flow with only the delivery provider mocked."""
    delivered = []
    with patch("app.api.auth.send_login_2fa_otp", side_effect=lambda _email, _name, code: delivered.append(code)):
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        body = response.json()
        if body.get("status") == "otp_required":
            assert delivered, "OTP delivery was not invoked"
            verified = client.post("/api/auth/verify-otp", json={
                "email": email, "otp": delivered[-1], "purpose": "login"
            })
            assert verified.status_code == 200, verified.text
            return verified.json()["access_token"]
        return body["access_token"]
