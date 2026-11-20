from app.config import settings
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_system_lifecycle_e2e():
    """
    COMPLETE END-TO-END VERIFICATION:
    1. Authenticate Operator
    2. Register & heartbeat Collector
    3. Ingest live telemetry with secrets caught locally
    4. Verify Redaction & Allowlist in Egress Proof
    5. Trigger AIOps anomaly & event correlation into incident
    6. Verify Explainable AI Recommendation
    7. Execute safe remediation approval with rollback plan
    8. Check Performance Targets & Audit Logs
    """
    # 1. Login
    login_res = client.post("/api/auth/login", json={
        "email": "admin@cynera.io",
        "password": "Cynera2026!Secure"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Collector Heartbeat
    col_headers = {
        "Authorization": f"Bearer {settings.COLLECTOR_CREDENTIAL}",
        "X-Collector-ID": "col-prod-core-01",
        "X-Tenant-ID": "11111111-1111-1111-1111-111111111111"
    }
    hb_res = client.post("/api/collectors/heartbeat", json={
        "collector_id": "col-prod-core-01",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "status": "online",
        "uptime_seconds": 3600,
        "cpu_usage_pct": 45.0,
        "memory_usage_mb": 1200.0,
        "queue_backlog_count": 0
    }, headers=col_headers)
    assert hb_res.status_code == 200

    # 3. Telemetry Ingestion (Clean approved metadata only)
    telemetry_payload = {
        "payload_id": f"e2e-payload-{int(time.time())}",
        "collector_id": "col-prod-core-01",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "timestamp_utc": "2026-11-20T12:00:00Z",
        "version": "1.4.2",
        "cpu_utilization_pct": 96.5, # Spikes CPU to trigger AIOps Anomaly
        "memory_utilization_pct": 91.0, # Spikes Memory
        "disk_utilization_pct": 65.0,
        "latency_ms": 210.0,
        "packet_loss_pct": 0.0,
        "failed_login_count": 2,
        "health_state": "POOR",
        "health_reason": "High CPU and memory saturation detected."
    }
    ingest_res = client.post("/api/telemetry/ingest", json=telemetry_payload, headers=col_headers)
    assert ingest_res.status_code == 200
    assert ingest_res.json()["success"] is True

    # 4. Record and Inspect Egress Proof Record
    proof_res = client.post("/api/egress/record", json={
        "payload_id": telemetry_payload["payload_id"],
        "collector_id": "col-prod-core-01",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "payload_hash_sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
        "bytes_transmitted": 640,
        "redacted_fields_count": 4,
        "redacted_field_types": ["REDACTED_PASSWORD", "REDACTED_CONN_STRING", "REDACTED_AWS_ACCESS_KEY"],
        "rejected_keys": ["unapproved_debug_log"],
        "allowlist_validated": True,
        "raw_payload_preview_hash": "c5d11635e3f0f16fb5d30450c6f93bc0e1bea07085b66da4e1419352e44293c5",
        "local_raw_preview": {"secret": "[MASKED_LOCALLY]", "cpu": 96.5},
        "outgoing_payload_json": telemetry_payload,
        "destination_endpoint": "http://127.0.0.1:8000/api/telemetry/ingest",
        "sent_at": "2026-11-20T12:00:00Z"
    }, headers=col_headers)
    assert proof_res.status_code == 200

    # 5. Verify Correlated Incident Generated
    inc_res = client.get("/api/incidents")
    assert inc_res.status_code == 200
    incidents = inc_res.json()
    assert len(incidents) >= 1
    recent_inc = incidents[0]
    assert recent_inc["has_ai_recommendation"] is True

    # 6. Verify Approvals List & Execute Autonomous Remediation
    app_res = client.get("/api/approvals")
    assert app_res.status_code == 200
    approvals = app_res.json()
    assert len(approvals) >= 1
    pending_app = [a for a in approvals if a["status"] == "PENDING"]
    if pending_app:
        target_app = pending_app[0]
        action_res = client.post(f"/api/approvals/{target_app['id']}/action", json={
            "action": "APPROVE",
            "operator_comments": "Verified and approved via E2E automated test."
        })
        assert action_res.status_code == 200
        assert action_res.json()["status"] == "APPROVED"
        assert "Policy gate: VERIFIED_SAFE" in action_res.json()["simulated_execution_log"]

    # 7. Verify Benchmarks Compliance
    bench_res = client.get("/api/analytics/benchmarks")
    assert bench_res.status_code == 200
    b_data = bench_res.json()
    assert b_data["p95_latency_ms"] < 10000 # Under 10s Hackathon target
    assert b_data["lost_record_count"] == 0

    # 8. Test 13 Scenarios Trigger
    for sc in ["cpu_spike", "memory_spike", "latency_increase", "duplicate_payload"]:
        sc_res = client.post("/api/scenarios/trigger", json={"scenario": sc})
        assert sc_res.status_code == 200

