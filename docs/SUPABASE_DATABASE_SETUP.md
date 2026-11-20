# CYNERA — Supabase Database Setup & Configuration Guide
**Platform:** CYNERA (*Cyber Network Evaluation and Risk Analytics*)  
**Primary Store:** Supabase Managed PostgreSQL Database  
**Driver:** SQLAlchemy with `psycopg2-binary` (Connection Pooling Enforced)

---

## 1. Overview & Precedence Architecture

CYNERA uses **Supabase PostgreSQL** as its primary cloud data store. In accordance with platform design standards:
- **Strict Precedence:** `SUPABASE_DB_URL` takes strict precedence over `DATABASE_URL`.
- **No Silent Fallback:** If `SUPABASE_DB_URL` and `DATABASE_URL` are not configured in `backend/.env`, CYNERA strictly refuses to silently fall back to a local SQLite database for production transactions. The application sets `DATABASE_STATUS = "BLOCKED_BY_CONFIGURATION"` and returns HTTP `503 Service Unavailable` on database operations until credentials are provided.
- **Collector Queue Scope:** Local SQLite (`LOCAL_QUEUE_PATH=data/local_buffer.db`) is strictly reserved for the Tier 1 edge collector's offline queue and retry buffer.

---

## 2. Supabase Connection Parameters

In your Supabase project dashboard (Project Settings → Database):
1. Locate your **Connection Pooling** or **Direct Connection** URI.
2. Formats:
   - **Transaction Pooler (Recommended for Serverless / High Concurrency):**
     ```ini
     SUPABASE_DB_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
     ```
   - **Session Pooler:**
     ```ini
     SUPABASE_DB_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
     ```
   - **Direct Connection:**
     ```ini
     SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres?sslmode=require
     ```

---

## 3. Configuration in `backend/.env`

Open `backend/.env` and update the database section:
```ini
# Primary Supabase PostgreSQL Connection String
SUPABASE_DB_URL=postgresql://postgres.yourprojectref:YourSecretPassword123@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require

# Standard Fallback Database URL (optional, only used if SUPABASE_DB_URL is omitted)
DATABASE_URL=

# Supabase REST & Auth API Credentials (Optional)
SUPABASE_URL=https://yourprojectref.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 4. Connection Pooling Configuration

CYNERA automatically configures SQLAlchemy connection pooling for Supabase in `backend/app/database.py`:
- `pool_size = 10`: Maintains 10 steady reusable connections.
- `max_overflow = 20`: Allows up to 20 temporary burst connections during high telemetry traffic.
- `pool_timeout = 30`: Waits up to 30 seconds for an available pool slot before throwing an error.
- `pool_recycle = 1800`: Recycles connections every 30 minutes to prevent stale TCP connections.
- `pool_pre_ping = True`: Issues a `SELECT 1` heartbeat probe before releasing a connection from the pool, preventing broken pipe disconnects.

---

## 5. Verifying Database Connectivity

CYNERA provides an automated connection verification helper `test_database_connection()`:
```python
from app.database import test_database_connection
result = test_database_connection()
print(result)
# Output on success:
# {'connected': True, 'status': 'CONNECTED', 'engine': 'postgresql', 'message': 'Database connection verified successfully.'}
```
If unconfigured, it safely outputs:
```python
# {'connected': False, 'status': 'BLOCKED_BY_CONFIGURATION', 'message': 'SUPABASE_DB_URL and DATABASE_URL are empty. Please configure Supabase in backend/.env.'}
```

---

## 6. Schema DDL Execution

When `SUPABASE_DB_URL` is set, CYNERA automatically executes `Base.metadata.create_all(bind=engine)` upon backend startup via the FastAPI `lifespan` handler. All 24 model tables (organizations, profiles, monitored websites, network devices, telemetry metrics, alerts, incidents, approvals) will be automatically provisioned in your Supabase schema.
