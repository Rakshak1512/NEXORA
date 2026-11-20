# CYNERA
## Cyber Network Evaluation and Risk Analytics
### AI-Powered Secure Infrastructure Observability Platform

> **See More. Secure More.**  
> *Intelligent Visibility. Privacy-First Monitoring. Actionable Insights.*  
> GitHub Repository: [https://github.com/Rakshak1512/NEXORA.git](https://github.com/Rakshak1512/NEXORA.git)

---

### Table of Contents
1. [Project Overview & Core Principles](#1-project-overview--core-principles)
2. [CYNERA Architecture](#2-cynera-architecture)
3. [Two-Tier Architecture: Local Collector & Central SaaS](#3-two-tier-architecture-local-collector--central-saas)
4. [Project Structure](#4-project-structure)
5. [Technology Stack](#5-technology-stack)
6. [Prerequisites](#6-prerequisites)
7. [Frontend Installation and Startup](#7-frontend-installation-and-startup)
8. [Backend Installation and Startup](#8-backend-installation-and-startup)
9. [Collector Installation and Startup](#9-collector-installation-and-startup)
10. [Environment Variable Architecture](#10-environment-variable-architecture)
11. [Database Setup & Supabase Integration](#11-database-setup--supabase-integration)
12. [API Documentation](#12-api-documentation)
13. [Testing Instructions & Results](#13-testing-instructions--results)
14. [Future Deployment Architecture (Exactly TWO Hosted Services)](#14-future-deployment-architecture-exactly-two-hosted-services)
15. [Egress Proof Center & Security Instructions](#15-egress-proof-center--security-instructions)
16. [Scenario Control Center (13 Scenarios)](#16-scenario-control-center-13-scenarios)

---

### 1. Project Overview & Core Principles

**CYNERA** (Cyber Network Evaluation and Risk Analytics) is an end-to-end secure observability and autonomous incident intelligence platform built to resolve the *Observability Paradox*: enterprises need centralized visibility and AI intelligence, but cannot afford to ship raw logs, passwords, API keys, or customer PII to third-party SaaS providers.

#### Core Principles:
- **Local-First Data Security**: Raw logs, database query texts, connection strings, and credentials never cross the local customer perimeter.
- **Metadata-Only SaaS Communication**: The central cloud backend strictly ingests approved numerical metrics, health states, and aggregated risk summaries.
- **Explainable Anomaly Detection**: Combines rolling statistical baselines (Z-Scores & IQR) with Scikit-learn's **Isolation Forest** on multidimensional telemetry vectors.
- **Event Correlation & Noise Reduction**: Automatically groups related alerts on the same collector within a 90-second sliding window into unified incidents with causal explanations.
- **Guaranteed Zero Data Loss**: Local SQLite queue (`local_buffer.db`) provides transactional persistence, exponential backoff, and idempotent ingestion.
- **Safe Autonomous Operations**: Policy-governed human-in-the-loop remediation requiring explicit operator approval before executing container recycles or edge rate limits.

---

### 2. CYNERA Architecture

```
+-------------------------------------------------------------------------+
|                  TIER 1: CUSTOMER ON-PREMISES / VPC                     |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                     Python Local Collector                        |  |
|  |                                                                   |  |
|  |   [psutil Hardware Engine] ----------> [Local Security Monitor]   |  |
|  |       (CPU, Mem, Disk, Net)                (Auth Failure Rates)   |  |
|  |                 |                                   |             |  |
|  |                 v                                   v             |  |
|  |   +-----------------------------------------------------------+   |  |
|  |   |           Local Secret Redactor (Regex Engine)            |   |  |
|  |   |    (AWS Keys, Passwords, Tokens, Conn Strings Neutralized)|   |  |
|  |   +-----------------------------------------------------------+   |  |
|  |                                 |                                 |  |
|  |                                 v                                 |  |
|  |   +-----------------------------------------------------------+   |  |
|  |   |            Strict Metadata Allowlist Validator            |   |  |
|  |   |       (Only 18 Approved Categorical/Numerical Keys Pass)  |   |  |
|  |   +-----------------------------------------------------------+   |  |
|  |                                 |                                 |  |
|  |            +--------------------+--------------------+            |  |
|  |            |                                         |            |  |
|  |            v                                         v            |  |
|  |   [Egress Proof Generator]                 [SQLite Persistent Q]  |  |
|  |   (SHA-256 Payload Hash,                    (Transactional Buffer)|  |
|  |    Local Sample vs Egress)                           |            |  |
|  +------------------------------------------------------|------------+  |
+---------------------------------------------------------|---------------+
                                                          | (HTTPS / HMAC Auth)
                                                          | Approved Metadata Only
                                                          v
+-------------------------------------------------------------------------+
|                  TIER 2: CENTRAL SAAS OBSERVABILITY PLATFORM            |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                   FastAPI High-Throughput Ingestion               |  |
|  |           (Duplicate Elimination via Idempotent Payload IDs)      |  |
|  +-------------------------------------------------------------------+  |
|            |                              |                             |
|            v                              v                             v
|   +------------------+          +--------------------+        +---------------+
|   | Supabase Postgres|          | AIOps Intelligence |        | WebSocket Hub |
|   | (RLS Enforced,   |          | - Z-Score Baseline |        | (Real-time    |
|   |  Tenants, Proofs)|          | - Isolation Forest |        |  Broadcasts to|
|   +------------------+          | - Temporal Cluster |        |  Dashboards)  |
|                                 | - Explainable Recs |        +---------------+
|                                 +--------------------+                |
|                                           |                           v
|                                           v                   +---------------+
|                                 [Remediation Approvals] ----->| React SaaS UI |
|                                 (Safe Human-in-the-Loop)      | (16 Modules)  |
+-------------------------------------------------------------------------------+
```

---

### 3. Two-Tier Architecture: Local Collector & Central SaaS

1. **Tier 1 (Customer Perimeter)**:
   - Operates entirely within the customer's on-premises network or private cloud VPC.
   - Collects live hardware metrics via `psutil`.
   - Neutralizes credentials via regex pattern matchers.
   - Discards non-whitelisted properties before queuing.
   - Buffers telemetry locally in SQLite (`data/local_buffer.db`) during SaaS outages.
   - Generates cryptographic SHA-256 evidence for the Egress Proof Center.
2. **Tier 2 (Central SaaS Platform)**:
   - Exposes authenticated FastAPI ingestion endpoints.
   - Validates incoming metadata against strict schemas and drops duplicate payloads idempotently.
   - Stores approved summaries in Supabase PostgreSQL with Row-Level Security (RLS).
   - Runs ensemble anomaly detection (rolling Z-score + Scikit-Learn Isolation Forest).
   - Groups related temporal signals into correlated incidents with explainable root causes and rollback plans.
   - Broadcasts real-time metric updates via WebSockets.

---

### 4. Project Structure

```
d:\NEXORA\
├── backend/                             # Tier 2: Central SaaS Platform
│   ├── app/
│   │   ├── main.py                      # FastAPI app & router registry
│   │   ├── config.py                    # Environment settings (Pydantic Settings)
│   │   ├── database.py                  # Dual-engine: SQLite fallback + Supabase client
│   │   ├── auth/                        # JWT authentication & collector HMAC token check
│   │   ├── api/                         # 10+ REST API endpoints
│   │   ├── models/models.py             # Relational database models
│   │   ├── schemas/schemas.py           # Pydantic schemas
│   │   ├── services/                    # Telemetry, Incident, Health, Audit services
│   │   ├── aiops/                       # Isolation Forest, Correlator, Recommendation
│   │   └── websocket/manager.py         # Real-time WebSocket manager
│   ├── tests/                           # Pytest Suite (10 Passed)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
│
├── collector/                           # Tier 1: Local Perimeter Daemon
│   ├── app/
│   │   ├── main.py                      # Daemon runner & scenario engine
│   │   ├── collector.py                 # Core telemetry orchestrator
│   │   ├── telemetry.py                 # psutil hardware metrics
│   │   ├── redactor.py                  # Regex secret scrubber
│   │   ├── allowlist.py                 # Strict metadata whitelist
│   │   ├── queue_manager.py             # SQLite transactional on-disk buffer
│   │   ├── egress_proof.py              # Cryptographic SHA-256 proof builder
│   │   ├── security_monitor.py          # Local auth burst detector
│   │   └── sender.py                    # HTTPS transmission client
│   ├── tests/                           # Pytest Suite (10 Passed)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
│
├── frontend/                            # React Enterprise SaaS Application
│   ├── src/
│   │   ├── pages/                       # 16 Interactive Pages
│   │   ├── components/                  # Common buttons, cards, modals, tables, health
│   │   ├── context/                     # Auth, Theme (Dark/Light), WebSocket
│   │   └── services/api.js              # Centralized Axios client (VITE_API_URL)
│   ├── package.json
│   ├── vite.config.js
│   ├── vercel.json                      # Vercel client-side routing rewrites
│   └── .env.example
│
├── database/                            # Supabase PostgreSQL Configuration
│   ├── schema.sql                       # Complete PostgreSQL DDL with RLS & indexes
│   └── seed.sql                         # Enterprise seed data (AcroGlobal Financial)
│
├── docs/                                # Technical Documentation
│   ├── architecture.md                  # Two-tier system topology
│   ├── data-flow.md                     # Telemetry lifecycle & data pipeline
│   ├── security.md                      # Threat model & perimeter defenses
│   ├── api-documentation.md             # REST API & WebSocket specifications
│   └── testing.md                       # Test suites & verification instructions
│
├── scripts/
│   ├── start-all.bat                    # Windows 1-click startup script
│   └── start-all.sh                     # Linux/macOS startup script
├── docker-compose.yml                   # Containerized multi-service deployment
├── .gitignore                           # Secure exclusions (no secrets, no DB files)
└── README.md                            # Complete master documentation
```

---

### 5. Technology Stack

- **Frontend**: React 18, Vite 5, Tailwind CSS 3, React Router v6, Lucide React, Recharts, Framer Motion, Axios, WebSockets.
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, python-jose, passlib, bcrypt, WebSockets.
- **Database**: Supabase PostgreSQL / Local Relational SQLite fallback, Row Level Security (RLS).
- **Collector**: Python 3.11, `psutil`, SQLite persistent queue, requests, SHA-256 verification.
- **AIOps & Machine Learning**: NumPy, Pandas, Scikit-learn (Isolation Forest), Causal Graph Inference.
- **Testing**: Pytest, Vitest, React Testing Library.

---

### 6. Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher and npm
- Git

---

### 7. Frontend Installation and Startup

```powershell
cd d:\NEXORA\frontend
npm install
npm run dev
```
*Frontend runs at `http://localhost:3000`.*  
To create a production build:
```powershell
npm run build
```

---

### 8. Backend Installation and Startup

```powershell
cd d:\NEXORA\backend
python -m pip install -r requirements.txt
python run.py
```
*Backend runs on `http://127.0.0.1:8000`.*  
*Interactive OpenAPI documentation available at `http://127.0.0.1:8000/docs`.*

---

### 9. Collector Installation and Startup

```powershell
cd d:\NEXORA\collector
python -m pip install -r requirements.txt
python run.py
```
*Collector runs independently, gathering live hardware telemetry and streaming metadata to the backend.*

#### Quick 1-Click Startup (All Services)
Double-click `scripts\start-all.bat` or execute:
```powershell
.\scripts\start-all.bat
```

---

### 10. Environment Variable Architecture

Environment configurations are cleanly separated between services.

#### A. Frontend (`frontend/.env`)
The frontend environment contains **exactly ONE variable**:
```env
VITE_API_URL=http://127.0.0.1:8000
```
- **Rules**:
  - No database configuration
  - No Supabase keys or service-role keys
  - No JWT secrets or backend tokens
  - All API calls and WebSocket connections dynamically derive from `VITE_API_URL`.
  - For production Vercel deployment: `VITE_API_URL=https://YOUR-BACKEND-DOMAIN`.

#### B. Backend (`backend/.env`)
Contains the frontend URL and backend-specific settings:
```env
APP_NAME=CYNERA
APP_ENV=development
DEBUG=true

BACKEND_URL=http://127.0.0.1:8000
FRONTEND_URL=http://localhost:3000

DATABASE_URL=sqlite:///./cicada_saas.db

JWT_SECRET_KEY=cynera-2026-super-secret-jwt-key-98127398127
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=

COLLECTOR_AUTH_SECRET=secret-collector-token-01

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

LOG_LEVEL=INFO
```

#### C. Collector (`collector/.env`)
Independent local configuration:
```env
COLLECTOR_ID=col-prod-core-01
COLLECTOR_NAME=Primary Cluster Collector 01
TENANT_ID=11111111-1111-1111-1111-111111111111
BACKEND_URL=http://127.0.0.1:8000
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

### 11. Database Setup & Supabase Integration

The platform features a **dual-engine database architecture**: it runs automatically out-of-the-box with local relational SQLite and seamlessly connects to live Supabase PostgreSQL when credentials are provided.

To connect live Supabase:
1. Log in to [Supabase Console](https://supabase.com).
2. Create a new project.
3. In the SQL Editor, execute `database/schema.sql` followed by `database/seed.sql`.
4. Update `backend/.env`:
   ```env
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   SUPABASE_URL=https://[PROJECT-REF].supabase.co
   SUPABASE_KEY=[ANON-KEY]
   ```
5. Restart the backend.

#### Pre-Configured Demo Credentials:
- **Super Administrator**: `admin@cynera.io` / `Cynera2026!Secure` (or `admin@cicada.io` / `Cicada2026!Secure`)
- **Operator**: `operator@cynera.io` / `Cynera2026!Secure` (or `operator@cicada.io` / `Cicada2026!Secure`)

---

### 12. API Documentation

Interactive OpenAPI documentation is available at:
`http://127.0.0.1:8000/docs`

Key API Route Groups:
- `/api/auth`: Login, registration, user profile, password reset.
- `/api/collectors`: Fleet management, heartbeats, watchdog status.
- `/api/telemetry`: Metadata ingestion with idempotent duplicate prevention.
- `/api/metrics`: Summary stats, CPU/Memory/Disk/Latency timeseries.
- `/api/incidents`: Correlated incidents, lifecycle updates (Investigating, Acknowledged, Resolved).
- `/api/egress`: Cryptographic egress proof ledger and verification.
- `/api/approvals`: Policy-checked remediation approvals and simulated execution.
- `/api/scenarios`: 1-click execution for all 13 hackathon failure injection scenarios.
- `/ws`: Real-time bi-directional WebSocket telemetry stream.

---

### 13. Testing Instructions & Results

All automated test suites execute locally and pass with 100% success:

#### Collector Tests (10 Passed)
```powershell
python -m pytest collector/tests -v
```
- `test_redactor.py`: 5 passed (password, bearer token, AWS key, connection string, nested dictionary).
- `test_allowlist.py`: 2 passed (allowlist filtering, required keys validation).
- `test_queue.py`: 1 passed (enqueue, idempotency, delivery confirmation).
- `test_collector.py`: 2 passed (live psutil telemetry, egress proof generation).

#### Backend Tests (10 Passed)
```powershell
python -m pytest backend/tests -v
```
- `test_auth.py`: 3 passed (login success, invalid password, registration).
- `test_telemetry.py`: 2 passed (ingestion, duplicate payload idempotency, unauthorized token).
- `test_aiops.py`: 3 passed (CPU anomaly detection, event correlation, explainable recommendations).
- `test_egress.py`: 1 passed (egress proof recording and retrieval).
- `test_e2e_integration.py`: 1 passed (full end-to-end operational lifecycle).

#### Frontend Tests & Production Build
```powershell
cd frontend
npm test
npm run build
```
- Vitest: 3 passed (Button, Badge, 4 Mandatory Health States).
- Production Build: Built in 8.77s with zero errors.

---

### 14. Future Deployment Architecture (Exactly TWO Hosted Services)

When ready to deploy, the architecture consists of **exactly TWO hosted services**:

#### Service 1: Frontend (Vercel)
- **Host**: Vercel
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Routing**: `vercel.json` provides client-side rewrites to `index.html`.
- **Environment**: Only `VITE_API_URL=https://YOUR-BACKEND-DOMAIN`.

#### Service 2: Backend (Render / Railway / Cloud Host)
- **Host**: Cloud ASGI container
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Environment**: `FRONTEND_URL`, `DATABASE_URL`, `JWT_SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, etc.
- **CORS**: Dynamically allows `FRONTEND_URL`.

#### Local Collector is NOT a Third Hosted Service
- The collector is an independent daemon installed on customer machines or Kubernetes clusters.
- It is never hosted as a central cloud service.

---

### 15. Egress Proof Center & Security Instructions

The **Egress Proof Center** proves what data leaves the local environment:
- **Left Column (Local Raw Perimeter)**: Displays original local events with credentials caught locally.
- **Middle Column (Redaction & Allowlist Audit)**: Shows which secrets were neutralized by `LocalDataRedactor` and non-whitelisted properties dropped.
- **Right Column (Outgoing Clean JSON)**: Displays the exact canonical JSON transmitted to SaaS with its SHA-256 checksum and delivery timestamp.

#### Security Checks Enforced:
- No secrets in frontend code or Git.
- Database passwords and JWT secrets excluded via `.gitignore`.
- Password hashing using bcrypt.
- Rate limiting and collector token validation.
- Row-Level Security on Supabase tables.

---

### 16. Scenario Control Center (13 Scenarios)

In the web console, navigate to **Scenario Control** to trigger any of the 13 official scenarios:
1. `Normal system operation`
2. `CPU spike` (Surges CPU to 97.4%, triggers CRITICAL alert)
3. `Memory spike` (Surges memory to 94.2%)
4. `Disk spike` (Fills volume to 96.8%)
5. `Network latency increase` (Surges WAN latency to 312ms)
6. `Packet loss surge` (Drops 7.8% of packets)
7. `Repeated failed logins` (Simulates 65 failures/min auth storm)
8. `Collector offline` (Tests 60s watchdog auto-downgrade)
9. `SaaS outage` (Tests SQLite queue local persistence)
10. `Recovery after outage` (Flushes backlog to backend with zero loss)
11. `Duplicate payload` (Idempotently drops duplicate payload IDs)
12. `Out-of-order payload` (Validates UTC event-time sorting)
13. `Multiple alerts for one incident` (Cascading multi-signal correlation)
