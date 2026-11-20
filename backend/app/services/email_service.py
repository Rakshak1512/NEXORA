import os
import re
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from typing import Optional, Dict, Any
from ..config import settings

logger = logging.getLogger("cynera.email")

def get_styled_email_template(title: str, preheader: str, body_html: str, action_code: Optional[str] = None) -> str:
    """Returns a responsive, premium CYNERA dark-themed HTML email."""
    code_box = ""
    if action_code:
        code_box = f"""
        <div style="margin: 28px 0; padding: 20px; background-color: #0c1424; border: 1px solid #1e293b; border-radius: 12px; text-align: center;">
            <p style="margin: 0 0 8px 0; color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.15em; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">VERIFICATION CODE</p>
            <div style="font-size: 36px; font-weight: 800; letter-spacing: 0.35em; color: #38bdf8; font-family: 'SF Mono', Monaco, Consolas, 'Courier New', monospace; padding: 8px 0;">{action_code}</div>
            <p style="margin: 8px 0 0 0; color: #64748b; font-size: 11px;">Expires in 10 minutes. Do not share this code.</p>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #030712; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <div style="max-width: 580px; margin: 40px auto; background-color: #090e17; border: 1px solid #1e293b; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #090e17 0%, #0d1829 100%); padding: 32px 32px 24px 32px; border-bottom: 1px solid #1e293b;">
            <div style="display: flex; align-items: center;">
                <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                    <tr>
                        <td style="vertical-align: middle;">
                            <div style="font-size: 22px; font-weight: 900; letter-spacing: 0.08em; color: #f8fafc;">
                                CYNERA <span style="font-size: 11px; font-weight: 700; color: #38bdf8; background-color: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); padding: 2px 6px; border-radius: 4px; vertical-align: middle; margin-left: 6px;">AIOPS</span>
                            </div>
                            <div style="font-size: 11px; color: #64748b; margin-top: 4px; font-weight: 500;">
                                Cyber Network Evaluation and Risk Analytics
                            </div>
                        </td>
                        <td style="vertical-align: middle; text-align: right;">
                            <span style="font-size: 10px; color: #38bdf8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; background: rgba(56, 189, 248, 0.08); padding: 4px 10px; border-radius: 9999px; border: 1px solid rgba(56, 189, 248, 0.2);">SECURE PLATFORM</span>
                        </td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- Body -->
        <div style="padding: 36px 32px;">
            <h1 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 700; color: #f1f5f9; line-height: 1.4;">{title}</h1>
            <div style="font-size: 14px; line-height: 1.7; color: #cbd5e1;">
                {body_html}
            </div>
            {code_box}
        </div>

        <!-- Footer -->
        <div style="padding: 24px 32px; background-color: #050912; border-top: 1px solid #1e293b; text-align: center;">
            <p style="margin: 0 0 8px 0; font-size: 11px; color: #64748b; font-weight: 600;">
                CYNERA &bull; See More. Secure More.
            </p>
            <p style="margin: 0; font-size: 10px; color: #475569; line-height: 1.5;">
                Two-Tier Zero-Trust Architecture &bull; Telemetry Filtered & Redacted Locally &bull; Only Approved Metadata Egresses
            </p>
        </div>
    </div>
</body>
</html>
"""

def send_smtp_email(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> Dict[str, Any]:
    """Sends an email using standard SMTP with STARTTLS or direct SSL."""
    host = settings.get_smtp_host()
    port = settings.get_smtp_port()
    username = settings.get_smtp_username()
    password = settings.get_smtp_password()
    from_email = settings.get_smtp_from_email()
    from_name = settings.get_smtp_from_name()
    use_ssl = getattr(settings, "SMTP_USE_SSL", False) or port == 465
    use_tls = getattr(settings, "SMTP_USE_TLS", True) and not use_ssl
    timeout = getattr(settings, "SMTP_TIMEOUT_SECONDS", 15)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header(from_name, "utf-8")), from_email))
    msg["To"] = to_email
    reply_to = getattr(settings, "SMTP_REPLY_TO", None) or "support@cynera.io"
    if reply_to:
        msg["Reply-To"] = reply_to

    # Plain text fallback
    plain_text = text_content or re.sub(r'<[^>]+>', ' ', html_content)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            server = smtplib.SMTP(host, port, timeout=timeout)
            if use_tls:
                server.ehlo()
                server.starttls()
                server.ehlo()

        if username and password:
            server.login(username, password)

        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        logger.info(f"[SMTP Success] Email dispatched to {to_email} via {host}:{port}")
        return {
            "success": True,
            "provider": "smtp",
            "host": host,
            "status": "DELIVERED"
        }
    except Exception as e:
        logger.error(f"[SMTP Error] Failed to send email via SMTP ({host}:{port}): {e}")
        return {
            "success": False,
            "provider": "smtp",
            "host": host,
            "status": "DELIVERY_FAILED",
            "error": str(e)
        }

def send_email(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> Dict[str, Any]:
    """Primary email dispatcher for CYNERA using standard corporate/cloud SMTP protocol."""
    # In test runner environment, return clean stub
    if "PYTEST_CURRENT_TEST" in os.environ or os.getenv("TESTING") == "true":
        return {"success": True, "provider": "test_stub", "status": "TEST_MODE"}

    # 1. Dispatch via SMTP
    if settings.is_smtp_configured():
        return send_smtp_email(to_email, subject, html_content, text_content)

    # 2. Blocked by configuration if SMTP is unconfigured
    logger.warning("[Email] SMTP is not configured in backend/.env. Email delivery is BLOCKED BY CONFIGURATION.")
    return {
        "success": False,
        "status": "BLOCKED_BY_CONFIGURATION",
        "message": "Email dispatch is BLOCKED BY CONFIGURATION. Please configure SMTP settings (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL) in backend/.env."
    }

def send_signup_otp(to_email: str, full_name: str, otp_code: str, organization_name: str) -> Dict[str, Any]:
    subject = f"Your CYNERA Verification Code: {otp_code}"
    body = f"""
    <p>Hello <strong>{full_name}</strong>,</p>
    <p>Thank you for creating an account on <strong>CYNERA</strong> for <strong>{organization_name}</strong>. To verify your corporate email address and initialize your secure observability workspace, enter the 6-digit verification code below:</p>
    """
    html = get_styled_email_template(
        title="Verify Your Corporate Account",
        preheader="Your 6-digit CYNERA verification code",
        body_html=body,
        action_code=otp_code
    )
    return send_email(to_email, subject, html)

def send_login_2fa_otp(to_email: str, full_name: str, otp_code: str) -> Dict[str, Any]:
    subject = f"CYNERA Security Alert: Login 2FA Code {otp_code}"
    body = f"""
    <p>Hello <strong>{full_name}</strong>,</p>
    <p>A login request was initiated for your CYNERA account. Complete your two-factor authentication by entering the code below:</p>
    """
    html = get_styled_email_template(
        title="Two-Factor Login Verification",
        preheader="Your CYNERA 2FA login code",
        body_html=body,
        action_code=otp_code
    )
    return send_email(to_email, subject, html)

def send_password_reset_otp(to_email: str, full_name: str, otp_code: str) -> Dict[str, Any]:
    subject = f"CYNERA Password Reset Code: {otp_code}"
    body = f"""
    <p>Hello <strong>{full_name}</strong>,</p>
    <p>We received a request to reset the password for your CYNERA account. Enter the 6-digit security code below to set a new password:</p>
    """
    html = get_styled_email_template(
        title="Password Reset Request",
        preheader="Your CYNERA password reset code",
        body_html=body,
        action_code=otp_code
    )
    return send_email(to_email, subject, html)

def send_member_invite(to_email: str, invited_by_name: str, organization_name: str, role: str, to_name: Optional[str] = None) -> Dict[str, Any]:
    subject = f"You're invited to join {organization_name} on CYNERA"
    recipient_greeting = f"<strong>{to_name}</strong>" if to_name else "Colleague"
    body = f"""
    <p>Hello {recipient_greeting},</p>
    <p><strong>{invited_by_name}</strong> has invited you to collaborate on the <strong>{organization_name}</strong> observability workspace on CYNERA as a <strong>{role}</strong>.</p>
    <p>CYNERA provides secure, AI-powered infrastructure monitoring with privacy-first two-tier telemetry.</p>
    <div style="margin: 24px 0; text-align: center;">
        <a href="http://localhost:3000/register?email={to_email}&org={organization_name}" style="background-color: #0284c7; color: #ffffff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; display: inline-block;">Accept Invitation & Register</a>
    </div>
    """
    html = get_styled_email_template(
        title=f"Invitation to {organization_name}",
        preheader=f"Join {organization_name} on CYNERA",
        body_html=body
    )
    return send_email(to_email, subject, html)

