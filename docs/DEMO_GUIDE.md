# CYNERA Demo Workspace Guide

## Two independent services

- **Backend API**: FastAPI application in `backend/`. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Health: `/api/health`.
- **Frontend**: React + Vite application in `frontend/`. Build: `npm ci && npm run build`; publish directory: `dist`.
- The root `render.yaml` defines one backend web service and one frontend static service. Set `VITE_API_URL` to the backend origin (without `/api`); the frontend client adds `/api`.

## Demo mode safety

Demo accounts and seeded demo records are disabled unless the backend has `DEMO_MODE=true`. Enable this only on a disposable demo/staging database, never on a production customer database. The Render blueprint defaults `DEMO_MODE=false`.

Demo mode uses synthetic, shared data. Changes made by one demo user can be visible to other demo users. Do not connect real customer collectors, credentials, websites or databases to a demo workspace.

## Demo accounts

All accounts use the demo password `Cynera2026!Secure`. In demo mode, the login page fetches the available accounts from `GET /api/auth/demo-accounts`; select a persona to enter using the role-specific demo-login route.

| Email | Persona | Intended demonstration |
|---|---|---|
| admin@cynera.io | Super Administrator | Platform controls and administration |
| owner@cynera.io | Organization Owner | Organization and membership management |
| workspace-admin@cynera.io | Admin | Workspace administration |
| security@cynera.io | Security Analyst | Security alerts and incident review |
| infra@cynera.io | Infrastructure Engineer | Collectors, infrastructure and network |
| operator@cynera.io | Operator | Daily operational monitoring |
| viewer@cynera.io | Viewer | Read-only review |

The existing `operator@cynera.io` and `admin@cynera.io` seeded personas are retained. Demo login is password/OTP-free only when the backend explicitly enables demo mode. Normal login still follows normal password and OTP policy.

## Seeded demo cases

The demo seeder is idempotent and labels synthetic records with `DEMO:` or `DEMO -`. It adds sample active warning and critical alerts, a resolved recovery alert, an investigating incident with a deterministic recommendation, authentication-failure security summary, egress proof record, a report, and notifications. Existing seeded website, APM, database, collector, network, approval and telemetry examples remain available.

## Validation

Run the GitHub Actions workflow after pushing. It executes backend API/security tests, collector tests, frontend tests and the Vite production build. A green build does not replace end-to-end testing against a disposable database and real configured integrations.
