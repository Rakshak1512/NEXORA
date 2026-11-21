import pytest
import hmac
import hashlib
import json
import socket
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from auth_helpers import login_as_platform_admin
from app.services.ssrf_guard import is_ip_private_or_restricted, validate_public_url

client = TestClient(app)

def get_auth_token():
    return login_as_platform_admin(client)

def test_ssrf_guard_blocks_forbidden_ranges():
    # Loopback
    assert is_ip_private_or_restricted("127.0.0.1") is True
    # Cloud metadata IP
    assert is_ip_private_or_restricted("169.254.169.254") is True
    # Private ranges
    assert is_ip_private_or_restricted("10.0.0.1") is True
    assert is_ip_private_or_restricted("192.168.1.100") is True
    assert is_ip_private_or_restricted("172.16.0.5") is True

    # Public IP
    assert is_ip_private_or_restricted("8.8.8.8") is False
    assert is_ip_private_or_restricted("1.1.1.1") is False

def test_ssrf_url_validation():
    # Localhost forbidden
    safe, err, _, _ = validate_public_url("http://127.0.0.1:8000/metrics")
    assert not safe
    assert "restricted" in err.lower() or "blocked" in err.lower() or "loopback" in err.lower()

    safe, err, _, _ = validate_public_url("http://localhost:3000")
    assert not safe

    safe, err, _, _ = validate_public_url("http://169.254.169.254/latest/meta-data/")
    assert not safe

def test_monitored_website_lifecycle():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    test_url = "https://example.org"

    # Clean up prior test runs if exists
    existing_list = client.get("/api/websites", headers=headers).json()
    for w in existing_list:
        if w["url"] == test_url:
            client.delete(f"/api/websites/{w['id']}", headers=headers)

    # 1. Create Monitored Website
    payload = {
        "name": "Acme Synthetic Public Web",
        "url": test_url,
        "monitoring_interval_seconds": 60,
        "check_timeout_seconds": 10,
        "http_method": "GET",
        "expected_status_codes": "200,301",
        "follow_redirects": True,
        "check_ssl": True
    }
    create_res = client.post("/api/websites", json=payload, headers=headers)
    assert create_res.status_code in (200, 201)
    site_data = create_res.json()
    assert site_data["url"] == test_url
    site_id = site_data.get("id") or site_data.get("website_id")

    # 2. SSRF block attempt via API
    bad_payload = {
        "name": "Malicious Probe",
        "url": "http://127.0.0.1:8000/secret",
        "monitoring_interval_seconds": 60
    }
    bad_res = client.post("/api/websites", json=bad_payload, headers=headers)
    assert bad_res.status_code == 400

    # 3. List Websites
    list_res = client.get("/api/websites", headers=headers)
    assert list_res.status_code == 200
    ids = [w["id"] for w in list_res.json()]
    assert site_id in ids

    # 4. Get Website Details
    detail_res = client.get(f"/api/websites/{site_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["name"] == "Acme Synthetic Public Web"

    # 5. Verify Ownership
    verify_res = client.post(
        f"/api/websites/{site_id}/verify-ownership",
        json={"method": "instant"},
        headers=headers
    )
    assert verify_res.status_code == 400
    assert "disabled" in verify_res.json()["detail"].lower()

    # 6. Add Endpoint
    ep_res = client.post(
        f"/api/websites/{site_id}/endpoints",
        json={"name": "Health Route", "path": "/health", "http_method": "GET"},
        headers=headers
    )
    assert ep_res.status_code in (200, 201)
    assert "/health" in (ep_res.json().get("path") or ep_res.json().get("endpoint_url"))

def test_apm_service_and_ingest():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Register APM service
    svc_res = client.post(
        "/api/apm/services",
        json={
            "name": "order-processor-py",
            "environment": "staging",
            "framework": "FastAPI",
            "language": "python"
        },
        headers=headers
    )
    assert svc_res.status_code in (200, 201)
    assert svc_res.json()["name"] == "order-processor-py"

    # Ingest event
    ingest_payload = {
        "service_name": "order-processor-py",
        "environment": "staging",
        "events": [
            {
                "type": "exception",
                "exception_type": "ValueError",
                "message": "Invalid card token format",
                "stack_trace": "Traceback (most recent call last):\n  File 'app.py', line 12",
                "level": "error"
            },
            {
                "type": "request",
                "endpoint": "/orders/checkout",
                "method": "POST",
                "status_code": 200,
                "duration_ms": 32.5
            }
        ]
    }
    ing_res = client.post("/api/apm/ingest", json=ingest_payload, headers=headers)
    assert ing_res.status_code in (200, 201)
    assert ing_res.json()["ingested"] == 2

    # Verify exceptions listed
    exc_res = client.get("/api/apm/exceptions", headers=headers)
    assert exc_res.status_code == 200
    types = [e["exception_type"] for e in exc_res.json()]
    assert "ValueError" in types

def test_database_monitoring():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Register database
    db_res = client.post(
        "/api/databases",
        json={
            "name": "Staging PostgreSQL Replica",
            "db_type": "postgresql",
            "host": "postgres-staging.internal",
            "port": 5432,
            "database_name": "staging_db",
            "username": "cynera_ro"
        },
        headers=headers
    )
    assert db_res.status_code in (200, 201)
    db_id = db_res.json()["id"]

    # Test connection probe
    test_res = client.post(f"/api/databases/{db_id}/test", headers=headers)
    assert test_res.status_code == 200
    assert test_res.json()["status"] == "HEALTHY"

def test_alerts_workflow():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create alert
    new_alert = client.post(
        "/api/alerts",
        json={
            "title": "Database Connection Pool Saturation Test",
            "severity": "CRITICAL",
            "category": "DATABASE",
            "message": "Connection pool usage reached 98%."
        },
        headers=headers
    )
    assert new_alert.status_code in (200, 201)
    a_id = new_alert.json()["id"]

    # Summary
    sum_res = client.get("/api/alerts/summary", headers=headers)
    assert sum_res.status_code == 200

    # List alerts
    alt_res = client.get("/api/alerts", headers=headers)
    assert alt_res.status_code == 200

    # Acknowledge
    ack_res = client.post(f"/api/alerts/{a_id}/acknowledge", headers=headers)
    assert ack_res.status_code == 200

    # Resolve
    res_res = client.post(f"/api/alerts/{a_id}/resolve", headers=headers)
    assert res_res.status_code == 200

def test_webhooks_and_hmac():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create webhook
    wh_res = client.post(
        "/api/webhooks",
        json={
            "name": "Mock Test Webhook",
            "url": "https://httpbin.org/post",
            "events": ["website.down", "incident.created"]
        },
        headers=headers
    )
    assert wh_res.status_code in (200, 201)
    wh_data = wh_res.json()
    wh_id = wh_data["id"]
    secret = wh_data["secret"]
    assert secret.startswith("cyn_whsec_")

    # Verify HMAC calculation logic
    test_body = b'{"event":"ping"}'
    sig = hmac.new(secret.encode(), test_body, hashlib.sha256).hexdigest()
    assert len(sig) == 64


def test_ssrf_guard_accepts_public_ipv4_and_ipv6_literals():
    # Globally routable literal addresses should not need a DNS lookup.
    safe, error, normalized, ips = validate_public_url("https://1.1.1.1/status")
    assert safe, error
    assert normalized == "https://1.1.1.1/status"
    assert ips == ["1.1.1.1"]

    safe, error, normalized, ips = validate_public_url("https://[2606:4700:4700::1111]/health")
    assert safe, error
    assert normalized == "https://[2606:4700:4700::1111]/health"
    assert ips == ["2606:4700:4700::1111"]

    # Bare public IPv6 literals are normalised into a bracketed HTTPS URL.
    safe, error, normalized, ips = validate_public_url("2606:4700:4700::1111")
    assert safe, error
    assert normalized == "https://[2606:4700:4700::1111]/"
    assert ips == ["2606:4700:4700::1111"]


def test_ssrf_guard_rejects_non_global_ip_literals():
    for address in (
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.10",
        "169.254.169.254",
        "100.64.0.1",
        "224.0.0.1",
    ):
        safe, _error, _normalized, _ips = validate_public_url(f"http://{address}/")
        assert not safe, f"Expected {address} to be blocked"


def test_ssrf_guard_accepts_public_hostname_with_dns_resolution():
    public_dns_answer = [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("76.76.21.21", 0),
        )
    ]
    with patch("app.services.ssrf_guard.socket.getaddrinfo", return_value=public_dns_answer):
        safe, error, normalized, ips = validate_public_url("lunvis-arty-crafty.vercel.app/")

    assert safe, error
    assert normalized == "https://lunvis-arty-crafty.vercel.app/"
    assert ips == ["76.76.21.21"]


def test_ssrf_guard_rejects_hostname_with_any_non_global_dns_answer():
    mixed_dns_answers = [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("76.76.21.21", 0),
        ),
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("10.0.0.8", 0),
        ),
    ]
    with patch("app.services.ssrf_guard.socket.getaddrinfo", return_value=mixed_dns_answers):
        safe, error, _normalized, _ips = validate_public_url("public-example.com")

    assert not safe
    assert "non-public IP" in error
