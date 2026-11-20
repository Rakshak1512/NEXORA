import pytest
from fastapi.testclient import TestClient

def get_auth_headers(client: TestClient):
    login_res = client.post("/api/auth/login", json={
        "email": "admin@cynera.io",
        "password": "Cynera2026!Secure"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_network_devices(client):
    headers = get_auth_headers(client)
    res = client.get("/api/network/devices", headers=headers)
    assert res.status_code == 200
    devices = res.json()
    assert isinstance(devices, list)
    assert len(devices) > 0
    dev = devices[0]
    assert "id" in dev
    assert "name" in dev
    assert "ip_address" in dev
    assert "status" in dev

def test_create_update_and_delete_network_device(client):
    headers = get_auth_headers(client)

    # 1. Create
    create_payload = {
        "name": "Integration-Test-Server",
        "ip_address": "127.0.0.1",
        "device_type": "Server",
        "monitoring_methods": ["ping", "tcp"],
        "tcp_ports": [8000, 3000],
        "monitoring_interval_seconds": 15,
        "is_active": True
    }
    create_res = client.post("/api/network/devices", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    device_data = create_res.json()
    device_id = device_data["id"]
    assert device_data["name"] == "Integration-Test-Server"
    assert device_data["ip_address"] == "127.0.0.1"

    # 2. Update
    update_res = client.put(f"/api/network/devices/{device_id}", json={
        "name": "Updated-Test-Server",
        "monitoring_interval_seconds": 60
    }, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated-Test-Server"
    assert update_res.json()["monitoring_interval_seconds"] == 60

    # 3. On-demand probe
    check_res = client.post(f"/api/network/devices/{device_id}/check-now", headers=headers)
    assert check_res.status_code == 200
    probe = check_res.json()["probe_result"]
    assert "reachable" in probe
    assert "latency_ms" in probe
    assert "open_ports" in probe

    # 4. Check history
    hist_res = client.get(f"/api/network/devices/{device_id}/history", headers=headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()["history"]) >= 1

    # 5. Delete
    del_res = client.delete(f"/api/network/devices/{device_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "SUCCESS"

def test_network_summary(client):
    headers = get_auth_headers(client)
    res = client.get("/api/network/summary", headers=headers)
    assert res.status_code == 200
    summary = res.json()
    assert "total_devices" in summary
    assert "online_devices" in summary
    assert "avg_latency_ms" in summary
    assert "avg_packet_loss_pct" in summary
    assert "total_monitored_ports" in summary
