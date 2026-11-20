# CYNERA — Resend Email & OTP Verification Setup Guide
**Platform:** CYNERA (*Cyber Network Evaluation and Risk Analytics*)  
**Service Provider:** Resend (REST API / Transactional Email)  
**Security Model:** Cryptographic HMAC-SHA256 OTP Storage & Strict Configuration Guard

---

## 1. Overview & Anti-Faking Rules

CYNERA uses **Resend** for production transactional emails, including:
1. User registration 6-digit OTP verification.
2. Operator login MFA challenges.
3. Password reset links and verification codes.
4. Critical infrastructure alert broadcasts.

### Strict Configuration Guard
- **No Fake Success:** If `RESEND_API_KEY` or `RESEND_FROM_EMAIL` is missing from `backend/.env`, CYNERA will **never** claim an email was delivered or pretend operations succeeded.
- **Blocked State:** Unconfigured email operations return `BLOCKED_BY_CONFIGURATION`.
- **No Plaintext OTP Leaks:** 6-digit verification codes are **never** logged to the server console, stdout, or application logs in plaintext.

---

## 2. Setting Up Your Resend Account

1. Register or log in to your account at [resend.com](https://resend.com).
2. Go to **Domains** → **Add Domain**:
   - Add your company domain (e.g., `cynera.io` or `monitoring.yourdomain.com`).
   - Add the required DNS records (SPF, DKIM, and MX/Return-Path) in your DNS registrar (Cloudflare, Route53, Namecheap, etc.).
   - Wait for domain status to transition to **Verified**.
   *(Note: For rapid testing, Resend allows sending to your own verified account email from `onboarding@resend.dev`)*.
3. Go to **API Keys** → **Create API Key**:
   - Name: `cynera-production-auth`
   - Permissions: Full Access (or Sending Access)
   - Copy the API key string starting with `re_...`.

---

## 3. Configuration in `backend/.env`

Open `backend/.env` and update the Resend section:
```ini
# Resend Transactional Email API Key
RESEND_API_KEY=re_123456789_abcdefghijklmnopqrstuvwxyz

# Verified Sender Email Address
RESEND_FROM_EMAIL=notifications@yourdomain.com
RESEND_FROM_NAME=CYNERA Security Team
RESEND_REPLY_TO=support@yourdomain.com

# OTP Security Parameters
OTP_EXPIRY_MINUTES=5
OTP_LENGTH=6
OTP_REQUIRED=true
OTP_HASH_SECRET=cyn_sec_otp_hash_9f4b2c1e8a7d3f5b
```

---

## 4. OTP Cryptographic Security Architecture

1. **Generation:** When a user registers or requests a password reset, CYNERA generates a 6-digit number using Python's `secrets.randbelow(900000) + 100000`.
2. **Cryptographic Hashing:** The code is immediately hashed with HMAC-SHA256 using `OTP_HASH_SECRET`.
3. **Storage:** Only the hash and timestamp are saved to the user profile record in the database.
4. **Transmission:** The plaintext code is sent exclusively to the user's email via the encrypted Resend API request:
   ```json
   {
     "from": "CYNERA Security Team <notifications@yourdomain.com>",
     "to": ["user@company.com"],
     "subject": "Your CYNERA Verification Code: 492817",
     "html": "<p>Your 6-digit verification code is <strong>492817</strong>. It will expire in 5 minutes.</p>"
   }
   ```
5. **Verification:** When the user enters their 6-digit OTP in the frontend, the server re-computes the HMAC-SHA256 hash and performs a constant-time comparison against the stored hash.

---

## 5. Verification Endpoint Diagnostic

To test Resend integration status without sending an actual email:
- The backend config provides `settings.is_resend_configured()`.
- If `RESEND_API_KEY` is present, it returns `True`.
- If unconfigured, calling `/api/auth/resend-otp` responds:
  ```json
  {
    "status": "BLOCKED_BY_CONFIGURATION",
    "message": "Email delivery service is unconfigured. Set RESEND_API_KEY in backend/.env."
  }
  ```
