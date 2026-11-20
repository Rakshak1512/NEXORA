# CYNERA – SMTP Email Authentication & Verification Configuration Guide

## Overview

CYNERA uses standard **SMTP (Simple Mail Transfer Protocol)** as the primary transport protocol for all authentication, verification, and transactional security emails.

Standard SMTP provides high deliverability, works with any corporate mail server or third-party transactional mail provider (Google Workspace, Microsoft 365, Amazon SES, SendGrid, Mailgun, Postmark, Brevo, custom Postfix/Exim), and eliminates third-party API SDK vendor lock-in.

---

## 1. Supported SMTP Environment Variables

Add the following variables to your `backend/.env` file:

```bash
# =====================================================================
# SMTP EMAIL CONFIGURATION (PRIMARY AUTHENTICATION & VERIFICATION)
# =====================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME="CYNERA Security"
SMTP_REPLY_TO=support@cynera.io
SMTP_TIMEOUT_SECONDS=15
```

### Alternative Alias Support
The system automatically recognizes standard enterprise aliases:
- `MAIL_HOST` or `SMTP_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME` or `SMTP_USER`
- `MAIL_PASSWORD` or `SMTP_PASS`
- `MAIL_FROM_ADDRESS` or `MAIL_FROM`
- `MAIL_FROM_NAME`

---

## 2. Common Provider Settings

### A. Gmail / Google Workspace
- **Host**: `smtp.gmail.com`
- **Port**: `587` (with STARTTLS) or `465` (with SSL)
- **Username**: Your full Gmail / Workspace email
- **Password**: 16-character **App Password** (Generated under Google Account > Security > 2-Step Verification > App Passwords)
- `SMTP_USE_TLS=true`
- `SMTP_USE_SSL=false`

### B. Microsoft 365 / Outlook
- **Host**: `smtp.office365.com`
- **Port**: `587`
- **Username**: Your full M365 email
- **Password**: App Password or Account Password
- `SMTP_USE_TLS=true`
- `SMTP_USE_SSL=false`

### C. Amazon SES (Simple Email Service)
- **Host**: `email-smtp.<region>.amazonaws.com` (e.g. `email-smtp.us-east-1.amazonaws.com`)
- **Port**: `587`
- **Username**: SES SMTP Username (from AWS IAM)
- **Password**: SES SMTP Password
- `SMTP_USE_TLS=true`
- `SMTP_USE_SSL=false`

### D. SendGrid
- **Host**: `smtp.sendgrid.net`
- **Port**: `587`
- **Username**: `apikey`
- **Password**: `<Your SendGrid API Key>`
- `SMTP_USE_TLS=true`
- `SMTP_USE_SSL=false`

---

## 3. Supported Security & Verification Flows

1. **Enterprise Signup & Workspace Initialization**:
   - Dispatches a 6-digit cryptographic verification code to the registrant.
   - Greets the user with their registered **Full Name** and validates the corporate email.
2. **Two-Factor Authentication (2FA) Login**:
   - Triggers a secure one-time passcode whenever 2FA is required or requested.
   - Directly addresses the user by **Full Name**.
3. **Self-Service Password Reset**:
   - Dispatches a time-limited 6-digit recovery OTP addressed to the user.
4. **Member Invitations**:
   - Sends customized workspace collaboration invites with the member's name and role.

---

## 4. User Name Storage in Database

- **Database Table**: `profiles` in Supabase PostgreSQL (`postgres`)
- **Column**: `full_name` (`VARCHAR(255) NOT NULL`)
- **Endpoints**:
  - `POST /api/auth/register-org`: Stores name in initial registration payload.
  - `POST /api/auth/verify-otp`: Persists user profile with `full_name` in Supabase.
  - `POST /api/auth/register`: Directly stores user name in `profiles`.
  - `POST /api/auth/login`: Returns `user.full_name` in authentication tokens and payloads.
  - `GET /api/auth/me`: Retrieves user profile including `full_name` from Supabase.
  - `PUT /api/auth/me` / `PATCH /api/auth/me`: Updates `full_name` and persists directly to Supabase.

