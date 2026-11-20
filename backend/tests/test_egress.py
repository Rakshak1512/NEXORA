from app.config import settings
import pytest
import uuid

def test_egress_proof_recording(client):
    headers = {
        "Authorization": f"Bearer {settings.COLLECTOR_CREDENTIAL}",
        "X-Collector-ID": "col-prod-core-01",
        "X-Tenant-ID": "11111111-1111-1111-1111-111111111111"
    }

    p_id = f"proof-test-{uuid.uuid4().hex[:8]}"
    proof_payload = {
        "payload_id": p_id,
        "collector_id": "col-prod-core-01",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "payload_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes_transmitted": 512,
        "redacted_fields_count": 3,
        "redacted_field_types": ["REDACTED_PASSWORD", "REDACTED_BEARER_TOKEN"],
        "rejected_keys": ["raw_unapproved_key"],
        "allowlist_validated": True,
        "raw_payload_preview_hash": "a1b2c3d4e5f6",
        "local_raw_preview": {"sample_keys": ["cpu", "password"]},
        "outgoing_payload_json": {"cpu_utilization_pct": 45.0},
        "destination_endpoint": "http://127.0.0.1:8000/api/telemetry/ingest",
        "sent_at": "2026-11-20T10:00:00Z"
    }

    res = client.post("/api/egress/record", json=proof_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["allowlist_validated"] is True

    # Retrieve from list
    list_res = client.get("/api/egress/records")
    assert list_res.status_code == 200
    records = list_res.json()
    assert any(r["payload_id"] == p_id for r in records)

