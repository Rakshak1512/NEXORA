import os
import pytest
from app.collector import LocalCollectorEngine
from app.telemetry import TelemetryEngine

def test_telemetry_collection():
    engine = TelemetryEngine()
    metrics = engine.collect_infrastructure()
    assert "cpu_utilization_pct" in metrics
    assert "memory_utilization_pct" in metrics
    assert "disk_utilization_pct" in metrics
    assert "health_state" in metrics
    assert metrics["health_state"] in ["EXCELLENT", "GOOD", "FAIR", "POOR"]
    assert "node-masked-" in metrics["hostname_pseudonym"]

def test_collector_cycle_and_egress_proof():
    collector = LocalCollectorEngine()
    res = collector.process_cycle()

    assert "payload_id" in res
    assert "outgoing_payload" in res
    assert "egress_proof" in res

    proof = res["egress_proof"]
    assert proof["allowlist_validated"] is True
    assert proof["bytes_transmitted"] > 0
    assert "payload_hash_sha256" in proof
    assert len(proof["payload_hash_sha256"]) == 64
    assert proof["destination_endpoint"].endswith("/api/telemetry/ingest")

