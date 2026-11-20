import pytest
import socket
from collector.app.network_monitor import LocalNetworkMonitor
from collector.app.allowlist import MetadataAllowlistValidator

@pytest.fixture
def monitor():
    return LocalNetworkMonitor()

def test_ping_localhost(monitor):
    res = monitor.ping("127.0.0.1", count=1, timeout_sec=1)
    assert "reachable" in res
    assert "latency_ms" in res
    assert "packet_loss_pct" in res
    assert res["packet_loss_pct"] <= 100.0

def test_ping_unreachable_ip(monitor):
    # RFC 5737 test address 192.0.2.1 is reserved for documentation and non-routable
    res = monitor.ping("192.0.2.1", count=1, timeout_sec=1)
    assert res["reachable"] is False
    assert res["status"] in ("UNREACHABLE", "INVALID_HOST")

def test_tcp_open_port(monitor):
    # Bind a temporary listening socket on localhost
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(('127.0.0.1', 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    try:
        res = monitor.check_tcp_port('127.0.0.1', port, timeout_sec=1.0)
        assert res["status"] == "OPEN"
        assert res["latency_ms"] >= 0.0
    finally:
        srv.close()

def test_tcp_closed_port(monitor):
    # A port where nothing is listening
    res = monitor.check_tcp_port('127.0.0.1', 29999, timeout_sec=0.5)
    assert res["status"] in ("CLOSED", "FILTERED")

def test_inspect_device_and_redaction(monitor):
    raw_device = {
        "id": "test-dev-01",
        "name": "Branch Router",
        "ip_address": "127.0.0.1",
        "device_type": "Router",
        "monitoring_methods": ["ping", "tcp"],
        "tcp_ports": [80],
        # Accidental credential inside configuration
        "raw_snmp_community": "postgres://admin:SecretPass123@10.0.1.1:5432/core"
    }
    inspected = monitor.inspect_device(raw_device)
    assert inspected["device_id"] == "test-dev-01"
    assert "check_status" in inspected
    assert "latency_ms" in inspected
    assert "packet_loss_pct" in inspected
    # Check that secrets are neutralized
    assert "SecretPass123" not in str(inspected)

def test_network_allowlist_filtering():
    payload = {
        "device_id": "dev-123",
        "device_name": "Core-Switch",
        "ip_address": "10.0.1.1",
        "check_status": "ONLINE",
        "latency_ms": 2.4,
        "packet_loss_pct": 0.0,
        "open_ports": [80, 443],
        "unauthorized_raw_packet_dump": "RAW_HEX_BYTES_DUMP_HERE"
    }
    filtered, rejected, is_valid = MetadataAllowlistValidator.filter_and_validate(payload)
    assert "device_id" in filtered
    assert "open_ports" in filtered
    assert "unauthorized_raw_packet_dump" in rejected
    assert "unauthorized_raw_packet_dump" not in filtered

