# CYNERA — Complete Environment Configuration Guide
**Platform:** CYNERA (*Cyber Network Evaluation and Risk Analytics*)  
**Version:** 1.4.2  
**Scope:** Exhaustive guide to environment variables for Backend (`backend/.env`), Frontend (`frontend/.env`), and Tier 1 Collector (`collector/.env`).

---

## 1. Frontend Configuration (`frontend/.env`)

The frontend is built with React and Vite. It requires only two strict variables:

```ini
# Backend API Base URL (FastAPI)
VITE_API_URL=http://127.0.0.1:8000

# Platform Branding Identity
VITE_APP_NAME=CYNERA
```

*Note: In production deployments, change `VITE_API_URL` to your live domain or reverse proxy endpoint (e.g., `https://api.cynera.io`).*

---

## 2. Backend Configuration (`backend/.env`)

The backend environment controls database pooling, Resend transactional emails, JWT secrets, CORS policies, and collector configurations.

```ini
# ====================================================================
# CYNERA: BACKEND CONFIGURATION
# Cyber Network Evaluation and Risk Analytics
# ====================================================================

# Service URLs & Networking
FRONTEND_URL=http://127.0.0.1:5173
BACKEND_URL=http://127.0.0.1:8000
ENVIRONMENT=production
DEBUG=false

# --------------------------------------------------------------------
# DATABASE CONFIGURATION (Primary: Supabase PostgreSQL)
# Strict Precedence: SUPABASE_DB_URL > DATABASE_URL
# --------------------------------------------------------------------
SUPABASE_DB_URL=
DATABASE_URL=

# Supabase REST & Auth Service Credentials (Optional)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Granular Connection Parameters (if assembling dynamically)
DB_ENGINE=postgresql
DB_HOST=
DB_PORT=5432
DB_NAME=postgres
DB_USER=
DB_PASSWORD=

# --------------------------------------------------------------------
# EMAIL & OTP SERVICE (Standard Corporate & Cloud SMTP Protocol)
# --------------------------------------------------------------------
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_FROM_EMAIL=
SMTP_FROM_NAME="CYNERA Security Team"
SMTP_REPLY_TO=support@cynera.io
SMTP_TIMEOUT_SECONDS=15

# OTP Security Parameters
OTP_EXPIRY_MINUTES=5
OTP_LENGTH=6
OTP_REQUIRED=true
OTP_HASH_SECRET=cyn_sec_otp_hash_9f4b2c1e8a7d3f5b

# --------------------------------------------------------------------
# AUTHENTICATION & JWT SECURITY
# --------------------------------------------------------------------
JWT_SECRET_KEY=cynera-enterprise-secret-key-replace-in-production-2026-secure
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# --------------------------------------------------------------------
# TIER 1 COLLECTOR & TELEMETRY CONFIGURATION
# --------------------------------------------------------------------
COLLECTOR_ID=col-prod-core-01
COLLECTOR_NAME=Primary Cluster Collector 01
TENANT_ID=11111111-1111-1111-1111-111111111111
COLLECTOR_CREDENTIAL=secret-collector-token-01
COLLECTION_INTERVAL_SECONDS=5
HEARTBEAT_INTERVAL_SECONDS=15
LOCAL_QUEUE_PATH=data/local_buffer.db
MAX_RETRY_ATTEMPTS=5
BACKOFF_FACTOR=1.5
VERSION=1.4.2
SIMULATED_MODE=false
```

---

## 3. Collector Configuration (`collector/.env`)

The edge collector runs inside client infrastructure (VM, bare metal, or Docker container) and communicates outbound to the backend via HTTPS/REST.

```ini
# ====================================================================
# CYNERA: TIER 1 EDGE COLLECTOR CONFIGURATION
# ====================================================================

# Collector Fleet Identity
COLLECTOR_ID=col-prod-core-01
COLLECTOR_NAME=Primary Cluster Collector 01
TENANT_ID=11111111-1111-1111-1111-111111111111
VERSION=1.4.2

# Backend Ingestion Endpoint & Authentication
BACKEND_URL=http://127.0.0.1:8000
COLLECTOR_CREDENTIAL=secret-collector-token-01

# Sampling & Heartbeat Cadence
COLLECTION_INTERVAL_SECONDS=5
HEARTBEAT_INTERVAL_SECONDS=15

# Local Offline Queue (Tier 1 Resiliency)
LOCAL_QUEUE_PATH=data/local_buffer.db
MAX_RETRY_ATTEMPTS=5
BACKOFF_FACTOR=1.5

# Simulation Flag (false for live OS hardware metrics)
SIMULATED_MODE=false
```

---

## 4. Precedence & Fallback Rules Summary

1. **Database:**
   - Precedence: `SUPABASE_DB_URL` > `DATABASE_URL`.
   - If empty: Application marks database operations as `BLOCKED_BY_CONFIGURATION` with HTTP 503.
   - SQLite test fallback: Enabled exclusively during automated test suite runs (`PYTEST_CURRENT_TEST` or `TESTING=true`).
2. **Email & OTP:**
   - If `RESEND_API_KEY` is empty, returns `BLOCKED_BY_CONFIGURATION`.
   - Never prints plaintext OTPs to console or log files.
3. **CORS:**
   - Automatically supports `localhost` and `127.0.0.1` on ports `3000` (Vite dev) and `5173` (Vite default), plus any custom origin specified in `FRONTEND_URL`.

