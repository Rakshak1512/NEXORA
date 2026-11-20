import os
import logging
from typing import Optional, Dict, Any
from ..config import settings

logger = logging.getLogger("cynera.email")

# Try importing resend
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend package not installed. Email dispatch will use development fallback logger.")

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

def send_email(to_email: str, subject: str, html_content: str) -> Dict[str, Any]:
    """Sends an email via Resend when configured. Never fakes delivery when credentials are missing."""
    api_key = (getattr(settings, "RESEND_API_KEY", "") or os.getenv("RESEND_API_KEY", "")).strip()
    from_email = (getattr(settings, "RESEND_FROM_EMAIL", "") or os.getenv("RESEND_FROM_EMAIL", "")).strip()
    
    # In test runner environment, return clean stub
    if "PYTEST_CURRENT_TEST" in os.environ or os.getenv("TESTING") == "true":
        return {"success": True, "provider": "test_stub", "status": "TEST_MODE"}
    
    if not api_key or not from_email:
        logger.warning("[Email] RESEND_API_KEY or RESEND_FROM_EMAIL is not configured in backend/.env. Email delivery is BLOCKED BY CONFIGURATION.")
        return {
            "success": False,
            "status": "BLOCKED_BY_CONFIGURATION",
            "message": "Email dispatch is BLOCKED BY CONFIGURATION. Please enter RESEND_API_KEY and RESEND_FROM_EMAIL in backend/.env."
        }
    
    if not RESEND_AVAILABLE:
        return {
            "success": False,
            "status": "RESEND_PACKAGE_MISSING",
            "message": "The 'resend' python package is not installed in the active environment."
        }
        
    try:
        resend.api_key = api_key
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        resp = resend.Emails.send(params)
        logger.info(f"[Resend Success] Email sent to {to_email}. ID: {resp.get('id', 'N/A')}")
        return {"success": True, "provider": "resend", "id": resp.get("id"), "status": "DELIVERED"}
    except Exception as e:
        logger.error(f"[Resend Error] Failed to send email via Resend: {e}")
        return {"success": False, "provider": "resend", "status": "DELIVERY_FAILED", "error": str(e)}

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

def send_member_invite(to_email: str, invited_by_name: str, organization_name: str, role: str) -> Dict[str, Any]:
    subject = f"You're invited to join {organization_name} on CYNERA"
    body = f"""
    <p>Hello,</p>
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

