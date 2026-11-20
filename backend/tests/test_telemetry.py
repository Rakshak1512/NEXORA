from app.config import settings
import pytest
import uuid

def test_telemetry_ingestion_and_idempotency(client):
    headers = {
        "Authorization": f"Bearer {settings.COLLECTOR_CREDENTIAL}",
        "X-Collector-ID": "col-prod-core-01",
        "X-Tenant-ID": "11111111-1111-1111-1111-111111111111"
    }

    p_id = f"test-p-{uuid.uuid4().hex[:8]}"
    payload = {
        "payload_id": p_id,
        "collector_id": "col-prod-core-01",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "timestamp_utc": "2026-11-20T10:00:00Z",
        "version": "1.4.2",
        "cpu_utilization_pct": 52.4,
        "memory_utilization_pct": 58.1,
        "disk_utilization_pct": 63.2,
        "health_state": "EXCELLENT"
    }

    # 1. First ingest
    res1 = client.post("/api/telemetry/ingest", json=payload, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["success"] is True

    # 2. Duplicate ingest with identical payload_id (Idempotency test)
    res2 = client.post("/api/telemetry/ingest", json=payload, headers=headers)
    assert res2.status_code == 200
    assert "Duplicate" in res2.json()["message"]

def test_collector_unauthorized_token(client):
    headers = {
        "Authorization": "Bearer WRONG_TOKEN",
        "X-Collector-ID": "col-prod-core-01",
        "X-Tenant-ID": "11111111-1111-1111-1111-111111111111"
    }
    res = client.post("/api/telemetry/ingest", json={}, headers=headers)
    assert res.status_code in [401, 403]

