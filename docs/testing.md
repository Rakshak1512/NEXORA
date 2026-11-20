# Testing & Verification Guide

CICADA OBSERVE includes automated test suites covering the Python Collector, FastAPI Backend, and React Frontend.

## 1. Running Collector Tests
Tests verify regex redaction, strict allowlist enforcement, SQLite queue transactions, and idempotent delivery.

```powershell
python -m pytest collector/tests -v
```
**Results**:
- `test_redactor.py`: 5 passed (password, bearer token, AWS key, connection string, nested dictionary).
- `test_allowlist.py`: 2 passed (allowlist filtering, required keys validation).
- `test_queue.py`: 1 passed (enqueue, idempotency, delivery confirmation).
- `test_collector.py`: 2 passed (live psutil telemetry, egress proof generation).

## 2. Running Backend Tests
Tests verify JWT authentication, telemetry ingestion, duplicate payload prevention, Isolation Forest anomaly detection, event correlation, and egress proof recording.

```powershell
python -m pytest backend/tests -v
```
**Results**:
- `test_auth.py`: 3 passed (login success, invalid password, registration).
- `test_telemetry.py`: 2 passed (ingestion, duplicate payload idempotency, unauthorized token).
- `test_aiops.py`: 3 passed (CPU anomaly detection, event correlation into single incident, explainable recommendations).
- `test_egress.py`: 1 passed (egress proof recording and retrieval).

## 3. Running Frontend Tests
Tests verify React components, custom health state indicators, and production bundling.

```powershell
cd frontend
npm test
npm run build
```
**Results**:
- Vitest: 3 passed (Button, Badge, 4 Mandatory Health States).
- Production Build: Vite production bundling completed in ~9s with zero errors.

