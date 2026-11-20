import pytest
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.models import Profile, Organization, OTPChallenge
from app.services.email_service import (
    send_smtp_email, send_email, send_signup_otp, send_login_2fa_otp,
    send_password_reset_otp, send_member_invite
)
from app.config import settings

def test_smtp_send_email_success_with_tls():
    """Verify that send_smtp_email connects, issues STARTTLS, authenticates, and dispatches."""
    with patch("smtplib.SMTP") as mock_smtp_cls, \
         patch.object(settings, "SMTP_HOST", "smtp.example.com"), \
         patch.object(settings, "SMTP_PORT", 587), \
         patch.object(settings, "SMTP_USERNAME", "apikey"), \
         patch.object(settings, "SMTP_PASSWORD", "smtp-pass-123"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "notifications@cynera.io"), \
         patch.object(settings, "SMTP_FROM_NAME", "CYNERA Security"), \
         patch.object(settings, "SMTP_USE_TLS", True), \
         patch.object(settings, "SMTP_USE_SSL", False):

        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        res = send_smtp_email(
            to_email="admin@clientcorp.com",
            subject="Verification Code",
            html_content="<p>Hello Alex Vance, your code is 123456</p>"
        )

        assert res["success"] is True
        assert res["provider"] == "smtp"
        assert res["status"] == "DELIVERED"
        mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=15)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("apikey", "smtp-pass-123")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

def test_smtp_send_email_success_with_ssl():
    """Verify SMTP over SSL (port 465)."""
    with patch("smtplib.SMTP_SSL") as mock_ssl_cls, \
         patch.object(settings, "SMTP_HOST", "smtp.gmail.com"), \
         patch.object(settings, "SMTP_PORT", 465), \
         patch.object(settings, "SMTP_USERNAME", "sec@gmail.com"), \
         patch.object(settings, "SMTP_PASSWORD", "app-password-xyz"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "sec@gmail.com"), \
         patch.object(settings, "SMTP_USE_SSL", True):

        mock_server = MagicMock()
        mock_ssl_cls.return_value = mock_server

        res = send_smtp_email(
            to_email="dev@company.com",
            subject="Security Alert",
            html_content="<p>Hello Sarah Chen, 2FA code is 999888</p>"
        )

        assert res["success"] is True
        assert res["provider"] == "smtp"
        assert res["status"] == "DELIVERED"
        mock_ssl_cls.assert_called_once_with("smtp.gmail.com", 465, timeout=15)
        mock_server.login.assert_called_once_with("sec@gmail.com", "app-password-xyz")
        mock_server.sendmail.assert_called_once()

def test_smtp_send_email_failure_handling():
    """Verify graceful handling when SMTP connection raises an exception."""
    with patch("smtplib.SMTP", side_effect=Exception("Connection refused (ECONNREFUSED)")), \
         patch.object(settings, "SMTP_HOST", "unreachable-smtp.local"), \
         patch.object(settings, "SMTP_PORT", 587), \
         patch.object(settings, "SMTP_FROM_EMAIL", "alerts@cynera.io"):

        res = send_smtp_email(
            to_email="ops@corp.com",
            subject="Test Fail",
            html_content="<p>Test</p>"
        )

        assert res["success"] is False
        assert res["status"] == "DELIVERY_FAILED"
        assert "Connection refused" in res["error"]

def test_user_name_rendered_in_all_email_templates():
    """Verify that user full_name is explicitly formatted into all authentication email templates."""
    with patch("app.services.email_service.send_email") as mock_send:
        mock_send.return_value = {"success": True}

        # 1. Signup OTP
        send_signup_otp("john@example.com", "Johnathan Doe", "123456", "Acme Security")
        args1 = mock_send.call_args[0]
        assert "Johnathan Doe" in args1[2] # html content contains user's name
        assert "Acme Security" in args1[2]

        # 2. Login 2FA OTP
        send_login_2fa_otp("jane@example.com", "Jane Montgomery", "654321")
        args2 = mock_send.call_args[0]
        assert "Jane Montgomery" in args2[2]

        # 3. Password Reset OTP
        send_password_reset_otp("alex@example.com", "Alexandria Vance", "789012")
        args3 = mock_send.call_args[0]
        assert "Alexandria Vance" in args3[2]

        # 4. Member Invite
        send_member_invite("colleague@example.com", "Lead Architect", "Apex Global", "Admin", to_name="David Miller")
        args4 = mock_send.call_args[0]
        assert "David Miller" in args4[2]
        assert "Lead Architect" in args4[2]

def test_database_contains_and_persists_user_name(client: TestClient):
    """Verify full end-to-end registration flow ensures the user's full name is in the database."""
    from app.database import SessionLocal
    db_session = SessionLocal()
    try:
        email = "enterprise-user@cynera-test.io"
        full_name = "Chief Information Security Officer"

        # 1. Register organization
        reg_res = client.post("/api/auth/register-org", json={
            "full_name": full_name,
            "email": email,
            "password": "StrongMasterPassword123!",
            "organization_name": "Test Sovereign Cloud",
            "job_title": "Director of Security"
        })
        assert reg_res.status_code == 200
        assert reg_res.json()["status"] == "otp_sent"

        # Query OTP Challenge directly from test database
        challenge = db_session.query(OTPChallenge).filter(
            OTPChallenge.email == email,
            OTPChallenge.purpose == "signup"
        ).order_by(OTPChallenge.created_at.desc()).first()
        assert challenge is not None

        # Retrieve pending payload
        payload = json.loads(challenge.payload_data)
        assert payload["full_name"] == full_name

        # 2. Register direct user to verify Profile database persistence
        direct_email = "direct-user@cynera-test.io"
        direct_name = "Dr. Robert Vance"
        direct_res = client.post("/api/auth/register", json={
            "email": direct_email,
            "password": "Password9988!!",
            "full_name": direct_name,
            "role": "Security Analyst"
        })
        assert direct_res.status_code == 200
        token_data = direct_res.json()
        assert token_data["user"]["full_name"] == direct_name

        # Query the database directly to ensure database contains the user name
        db_profile = db_session.query(Profile).filter(Profile.email == direct_email).first()
        assert db_profile is not None
        assert db_profile.full_name == direct_name

        # 3. Retrieve profile via /api/auth/me
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me_res = client.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["full_name"] == direct_name

        # 4. Update profile name via PUT /api/auth/me
        updated_name = "Dr. Robert Vance, PhD"
        update_res = client.put("/api/auth/me", json={"full_name": updated_name}, headers=headers)
        assert update_res.status_code == 200
        assert update_res.json()["user"]["full_name"] == updated_name

        # Re-query DB to verify updated name persisted in database
        db_session.refresh(db_profile)
        assert db_profile.full_name == updated_name
    finally:
        db_session.close()

