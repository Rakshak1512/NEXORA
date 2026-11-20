import pytest
from app.allowlist import MetadataAllowlistValidator

def test_allowlist_filtering():
    raw_payload = {
        "payload_id": "test-payload-001",
        "collector_id": "col-01",
        "tenant_id": "tenant-01",
        "timestamp_utc": "2026-11-20T10:00:00Z",
        "cpu_utilization_pct": 55.4,
        "memory_utilization_pct": 62.1,
        "raw_query_string": "SELECT * FROM users WHERE credit_card='1234'",
        "unapproved_secret_token": "token123"
    }

    filtered, rejected, is_valid = MetadataAllowlistValidator.filter_and_validate(raw_payload)

    assert is_valid is True
    assert "raw_query_string" in rejected
    assert "unapproved_secret_token" in rejected
    assert "raw_query_string" not in filtered
    assert "unapproved_secret_token" not in filtered
    assert filtered["cpu_utilization_pct"] == 55.4
    assert filtered["payload_id"] == "test-payload-001"

def test_allowlist_missing_required_keys():
    incomplete = {
        "cpu_utilization_pct": 55.4
    }
    filtered, rejected, is_valid = MetadataAllowlistValidator.filter_and_validate(incomplete)
    assert is_valid is False

