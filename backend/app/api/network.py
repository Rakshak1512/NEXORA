import datetime
import json
import time
import socket
import subprocess
import platform
import re
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.models import (
    NetworkDevice, NetworkCheckResult, IncidentAlert, Incident, 
    SystemAuditLog, Tenant, Profile
)
from ..auth.deps import get_current_user
from ..websocket.manager import ws_manager

router = APIRouter(prefix="/network", tags=["Network Monitoring & Devices"])

# -----------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# -----------------------------------------------------------------------------
ALLOWED_DEVICE_TYPES = {"Server", "Router", "Switch", "Firewall", "Workstation", "Other"}
ALLOWED_PROTOCOLS = {"ping", "tcp", "snmp", "ssh", "syslog"}

class NetworkDeviceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    ip_address: str = Field(..., min_length=3, max_length=100)
    device_type: str = Field(default="Server")
    monitoring_methods: List[str] = Field(default=["ping", "tcp"])
    tcp_ports: List[int] = Field(default=[80, 443])
    monitoring_interval_seconds: int = Field(default=30, ge=5, le=3600)
    is_active: bool = True
    snmp_config: Optional[Dict[str, Any]] = None
    ssh_config: Optional[Dict[str, Any]] = None

class NetworkDeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    monitoring_methods: Optional[List[str]] = None
    tcp_ports: Optional[List[int]] = None
    monitoring_interval_seconds: Optional[int] = None
    is_active: Optional[bool] = None

class NetworkDeviceResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    ip_address: str
    device_type: str
    monitoring_methods: List[str]
    tcp_ports: List[int]
    monitoring_interval_seconds: int
    is_active: bool
    status: str
    last_latency_ms: float
    last_packet_loss_pct: float
    open_ports_summary: List[int]
    last_checked_at: Optional[str] = None
    created_at: Optional[str] = None

# -----------------------------------------------------------------------------
# HELPER: SAFE LOCAL PROBE ENGINE
# -----------------------------------------------------------------------------
def perform_safe_network_probe(ip: str, methods: List[str], ports: List[int]) -> Dict[str, Any]:
    """
    Executes an active network probe against an authorized device IP/hostname.
    Protected with bounded timeouts and strict input sanitization.
    """
    clean_host = ip.strip()
    # Strict validation to prevent command injection
    if not re.match(r'^[a-zA-Z0-9.\-_:]+$', clean_host):
        return {
            "reachable": False,
            "status": "UNREACHABLE",
            "latency_ms": 0.0,
            "packet_loss_pct": 100.0,
            "open_ports": [],
            "closed_ports": [],
            "port_details": {},
            "error": "Invalid IP address or hostname syntax"
        }

    ping_ok = True
    latency_ms = 1.0
    packet_loss = 0.0
    os_name = platform.system().lower()

    if "ping" in methods:
        cmd = ["ping", "-n", "2", "-w", "1000", clean_host] if "win" in os_name else ["ping", "-c", "2", "-W", "1", clean_host]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
            stdout = res.stdout

            loss_match = re.search(r'(\d+)%\s*(?:packet\s*)?loss', stdout, re.IGNORECASE)
            packet_loss = float(loss_match.group(1)) if loss_match else (0.0 if res.returncode == 0 else 100.0)

            avg_match = re.search(r'Average\s*=\s*(\d+)ms', stdout, re.IGNORECASE)
            if avg_match:
                latency_ms = float(avg_match.group(1))
            else:
                posix_match = re.search(r'=\s*[\d.]+/([\d.]+)/', stdout)
                if posix_match:
                    latency_ms = float(posix_match.group(1))
                elif "time<1ms" in stdout:
                    latency_ms = 0.5
                else:
                    latency_ms = 1.5

            ping_ok = (res.returncode == 0 and packet_loss < 100.0)
        except Exception:
            ping_ok = False
            packet_loss = 100.0
            latency_ms = 0.0

    # TCP Port Probing
    open_ports = []
    closed_ports = []
    port_details = {}

    if "tcp" in methods and ports:
        for p in ports:
            if not isinstance(p, int) or p < 1 or p > 65535:
                continue
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.2)
            t0 = time.perf_counter()
            try:
                code = s.connect_ex((clean_host, p))
                dt = round((time.perf_counter() - t0) * 1000.0, 2)
                if code == 0:
                    open_ports.append(p)
                    port_details[str(p)] = {"status": "OPEN", "latency_ms": dt}
                    # If ICMP was dropped by firewall but TCP responds, device is alive!
                    if not ping_ok:
                        ping_ok = True
                        packet_loss = 0.0
                        latency_ms = dt
                elif code in (10061, 111):
                    closed_ports.append(p)
                    port_details[str(p)] = {"status": "CLOSED", "latency_ms": dt}
                else:
                    closed_ports.append(p)
                    port_details[str(p)] = {"status": "FILTERED", "latency_ms": dt}
            except Exception as e:
                closed_ports.append(p)
                port_details[str(p)] = {"status": "CLOSED", "error": str(e)}
            finally:
                s.close()

    # Determine status
    if not ping_ok:
        device_status = "UNREACHABLE"
    elif closed_ports and not open_ports and len(ports) > 0:
        device_status = "DEGRADED"
    elif packet_loss > 20.0 or latency_ms > 150.0:
        device_status = "DEGRADED"
    else:
        device_status = "ONLINE"

    return {
        "reachable": ping_ok,
        "status": device_status,
        "latency_ms": round(max(0.1, latency_ms), 2),
        "packet_loss_pct": round(packet_loss, 2),
        "open_ports": open_ports,
        "closed_ports": closed_ports,
        "port_details": port_details
    }

# -----------------------------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------------------------
@router.get("/devices", response_model=List[NetworkDeviceResponse])
def list_network_devices(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Lists all registered network devices for the authorized tenant."""
    devices = db.query(NetworkDevice).filter(
        NetworkDevice.tenant_id == current_user.tenant_id
    ).order_by(NetworkDevice.created_at.desc()).all()

    results = []
    for d in devices:
        try:
            methods = json.loads(d.monitoring_methods) if d.monitoring_methods else ["ping", "tcp"]
        except Exception:
            methods = ["ping", "tcp"]
        try:
            ports = json.loads(d.tcp_ports) if d.tcp_ports else [80, 443]
        except Exception:
            ports = [80, 443]
        try:
            open_ports = json.loads(d.open_ports_summary) if d.open_ports_summary else []
        except Exception:
            open_ports = []

        results.append(NetworkDeviceResponse(
            id=d.id,
            tenant_id=d.tenant_id,
            name=d.name,
            ip_address=d.ip_address,
            device_type=d.device_type,
            monitoring_methods=methods,
            tcp_ports=ports,
            monitoring_interval_seconds=d.monitoring_interval_seconds,
            is_active=d.is_active,
            status=d.status,
            last_latency_ms=d.last_latency_ms,
            last_packet_loss_pct=d.last_packet_loss_pct,
            open_ports_summary=open_ports,
            last_checked_at=d.last_checked_at.isoformat() if d.last_checked_at else None,
            created_at=d.created_at.isoformat() if d.created_at else None
        ))
    return results

@router.post("/devices", response_model=NetworkDeviceResponse, status_code=status.HTTP_201_CREATED)
def create_network_device(
    payload: NetworkDeviceCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Registers a new network device or server with authorized IP and monitoring methods.
    Audited in system logs.
    """
    # Validation
    if payload.device_type not in ALLOWED_DEVICE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid device type. Allowed: {list(ALLOWED_DEVICE_TYPES)}"
        )
    for m in payload.monitoring_methods:
        if m not in ALLOWED_PROTOCOLS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid monitoring protocol '{m}'. Allowed: {list(ALLOWED_PROTOCOLS)}"
            )

    clean_ip = payload.ip_address.strip()
    if not re.match(r'^[a-zA-Z0-9.\-_:]+$', clean_ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IP address or hostname format."
        )

    # Initial probe to determine current state
    probe = perform_safe_network_probe(clean_ip, payload.monitoring_methods, payload.tcp_ports)

    device = NetworkDevice(
        tenant_id=current_user.tenant_id,
        name=payload.name.strip(),
        ip_address=clean_ip,
        device_type=payload.device_type,
        monitoring_methods=json.dumps(payload.monitoring_methods),
        tcp_ports=json.dumps(payload.tcp_ports),
        monitoring_interval_seconds=payload.monitoring_interval_seconds,
        is_active=payload.is_active,
        status=probe["status"],
        last_latency_ms=probe["latency_ms"],
        last_packet_loss_pct=probe["packet_loss_pct"],
        open_ports_summary=json.dumps(probe["open_ports"]),
        snmp_config=json.dumps(payload.snmp_config or {}),
        ssh_config=json.dumps(payload.ssh_config or {}),
        last_checked_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(device)
    db.flush()

    # Save initial check result
    check_rec = NetworkCheckResult(
        device_id=device.id,
        tenant_id=current_user.tenant_id,
        check_type="probe_initial",
        status=probe["status"],
        latency_ms=probe["latency_ms"],
        packet_loss_pct=probe["packet_loss_pct"],
        open_ports=json.dumps(probe["open_ports"]),
        closed_ports=json.dumps(probe["closed_ports"]),
        port_details=json.dumps(probe["port_details"]),
        metrics_payload=json.dumps({"probe_source": "cynera-local-agent"})
    )
    db.add(check_rec)

    # Audit Log
    audit = SystemAuditLog(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="NETWORK_DEVICE_REGISTERED",
        entity_type="NetworkDevice",
        entity_id=device.id,
        details=json.dumps({
            "name": device.name,
            "ip_address": device.ip_address,
            "device_type": device.device_type,
            "initial_status": probe["status"]
        }),
        ip_address=current_user.email
    )
    db.add(audit)
    db.commit()
    db.refresh(device)

    # Broadcast WebSocket event
    import asyncio
    try:
        asyncio.create_task(ws_manager.broadcast({
            "type": "NETWORK_DEVICE_ADDED",
            "data": {
                "device_id": device.id,
                "name": device.name,
                "status": device.status,
                "ip_address": device.ip_address
            }
        }))
    except Exception:
        pass

    return NetworkDeviceResponse(
        id=device.id,
        tenant_id=device.tenant_id,
        name=device.name,
        ip_address=device.ip_address,
        device_type=device.device_type,
        monitoring_methods=payload.monitoring_methods,
        tcp_ports=payload.tcp_ports,
        monitoring_interval_seconds=device.monitoring_interval_seconds,
        is_active=device.is_active,
        status=device.status,
        last_latency_ms=device.last_latency_ms,
        last_packet_loss_pct=device.last_packet_loss_pct,
        open_ports_summary=probe["open_ports"],
        last_checked_at=device.last_checked_at.isoformat() if device.last_checked_at else None,
        created_at=device.created_at.isoformat() if device.created_at else None
    )

@router.put("/devices/{device_id}", response_model=NetworkDeviceResponse)
def update_network_device(
    device_id: str,
    payload: NetworkDeviceUpdate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Updates device name, IP address, monitoring intervals, or monitored ports."""
    device = db.query(NetworkDevice).filter(
        NetworkDevice.id == device_id,
        NetworkDevice.tenant_id == current_user.tenant_id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Network device not found.")

    if payload.name is not None:
        device.name = payload.name.strip()
    if payload.ip_address is not None:
        clean_ip = payload.ip_address.strip()
        if not re.match(r'^[a-zA-Z0-9.\-_:]+$', clean_ip):
            raise HTTPException(status_code=400, detail="Invalid IP address format.")
        device.ip_address = clean_ip
    if payload.device_type is not None:
        if payload.device_type in ALLOWED_DEVICE_TYPES:
            device.device_type = payload.device_type
    if payload.monitoring_methods is not None:
        device.monitoring_methods = json.dumps(payload.monitoring_methods)
    if payload.tcp_ports is not None:
        device.tcp_ports = json.dumps(payload.tcp_ports)
    if payload.monitoring_interval_seconds is not None:
        device.monitoring_interval_seconds = payload.monitoring_interval_seconds
    if payload.is_active is not None:
        device.is_active = payload.is_active

    # Audit log
    audit = SystemAuditLog(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="NETWORK_DEVICE_UPDATED",
        entity_type="NetworkDevice",
        entity_id=device.id,
        details=json.dumps({"updated_fields": payload.model_dump(exclude_unset=True)}),
        ip_address=current_user.email
    )
    db.add(audit)
    db.commit()
    db.refresh(device)

    try:
        methods = json.loads(device.monitoring_methods)
    except Exception:
        methods = ["ping", "tcp"]
    try:
        ports = json.loads(device.tcp_ports)
    except Exception:
        ports = [80, 443]
    try:
        open_ports = json.loads(device.open_ports_summary)
    except Exception:
        open_ports = []

    return NetworkDeviceResponse(
        id=device.id,
        tenant_id=device.tenant_id,
        name=device.name,
        ip_address=device.ip_address,
        device_type=device.device_type,
        monitoring_methods=methods,
        tcp_ports=ports,
        monitoring_interval_seconds=device.monitoring_interval_seconds,
        is_active=device.is_active,
        status=device.status,
        last_latency_ms=device.last_latency_ms,
        last_packet_loss_pct=device.last_packet_loss_pct,
        open_ports_summary=open_ports,
        last_checked_at=device.last_checked_at.isoformat() if device.last_checked_at else None,
        created_at=device.created_at.isoformat() if device.created_at else None
    )

@router.delete("/devices/{device_id}")
def delete_network_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Deletes an authorized network device and all associated check logs."""
    device = db.query(NetworkDevice).filter(
        NetworkDevice.id == device_id,
        NetworkDevice.tenant_id == current_user.tenant_id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Network device not found.")

    device_name = device.name
    db.delete(device)

    audit = SystemAuditLog(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="NETWORK_DEVICE_DELETED",
        entity_type="NetworkDevice",
        entity_id=device_id,
        details=json.dumps({"deleted_name": device_name}),
        ip_address=current_user.email
    )
    db.add(audit)
    db.commit()
    return {"status": "SUCCESS", "message": f"Network device '{device_name}' removed."}

@router.post("/devices/{device_id}/check-now")
def trigger_immediate_device_check(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Executes an on-demand live ping and port check against the specified network device.
    Generates AIOps incident alerts if unreachable or critical service port is down.
    """
    device = db.query(NetworkDevice).filter(
        NetworkDevice.id == device_id,
        NetworkDevice.tenant_id == current_user.tenant_id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Network device not found.")

    try:
        methods = json.loads(device.monitoring_methods)
    except Exception:
        methods = ["ping", "tcp"]
    try:
        ports = json.loads(device.tcp_ports)
    except Exception:
        ports = [80, 443]

    # Execute safe probe
    probe = perform_safe_network_probe(device.ip_address, methods, ports)

    # Update device state
    device.status = probe["status"]
    device.last_latency_ms = probe["latency_ms"]
    device.last_packet_loss_pct = probe["packet_loss_pct"]
    device.open_ports_summary = json.dumps(probe["open_ports"])
    import datetime
    device.last_checked_at = datetime.datetime.now(datetime.timezone.utc)

    # Record check result
    check_rec = NetworkCheckResult(
        device_id=device.id,
        tenant_id=current_user.tenant_id,
        check_type="manual_check",
        status=probe["status"],
        latency_ms=probe["latency_ms"],
        packet_loss_pct=probe["packet_loss_pct"],
        open_ports=json.dumps(probe["open_ports"]),
        closed_ports=json.dumps(probe["closed_ports"]),
        port_details=json.dumps(probe["port_details"]),
        metrics_payload=json.dumps({"triggered_by": current_user.email})
    )
    db.add(check_rec)

    # AIOps Alert Generation if unreachable or packet loss high
    if probe["status"] == "UNREACHABLE":
        alert = IncidentAlert(
            tenant_id=current_user.tenant_id,
            collector_id="col-network-guard",
            alert_type="NETWORK_DEVICE_UNREACHABLE",
            severity="CRITICAL",
            metric_name="packet_loss_pct",
            metric_value=probe["packet_loss_pct"],
            threshold_value=10.0,
            message=f"Network device '{device.name}' ({device.ip_address}) is UNREACHABLE. Ping and TCP connection timed out."
        )
        db.add(alert)
    elif probe["status"] == "DEGRADED":
        alert = IncidentAlert(
            tenant_id=current_user.tenant_id,
            collector_id="col-network-guard",
            alert_type="NETWORK_SERVICE_DEGRADED",
            severity="HIGH",
            metric_name="latency_ms",
            metric_value=probe["latency_ms"],
            threshold_value=100.0,
            message=f"Network device '{device.name}' is DEGRADED. Monitored TCP ports {probe['closed_ports']} are closed or latency is {probe['latency_ms']}ms."
        )
        db.add(alert)

    db.commit()

    # Broadcast WebSocket update
    import asyncio
    try:
        asyncio.create_task(ws_manager.broadcast({
            "type": "NETWORK_DEVICE_CHECKED",
            "data": {
                "device_id": device.id,
                "name": device.name,
                "status": device.status,
                "latency_ms": device.last_latency_ms,
                "packet_loss_pct": device.last_packet_loss_pct,
                "open_ports": probe["open_ports"],
                "closed_ports": probe["closed_ports"]
            }
        }))
    except Exception:
        pass

    return {
        "status": "SUCCESS",
        "device_id": device.id,
        "name": device.name,
        "ip_address": device.ip_address,
        "probe_result": probe
    }

@router.get("/devices/{device_id}/history")
def get_device_monitoring_history(
    device_id: str,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Returns the historical check results and latency timeseries for a device."""
    device = db.query(NetworkDevice).filter(
        NetworkDevice.id == device_id,
        NetworkDevice.tenant_id == current_user.tenant_id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Network device not found.")

    records = db.query(NetworkCheckResult).filter(
        NetworkCheckResult.device_id == device_id,
        NetworkCheckResult.tenant_id == current_user.tenant_id
    ).order_by(NetworkCheckResult.recorded_at.desc()).limit(limit).all()

    history = []
    for r in records:
        try:
            ports = json.loads(r.open_ports) if r.open_ports else []
        except Exception:
            ports = []
        try:
            closed = json.loads(r.closed_ports) if r.closed_ports else []
        except Exception:
            closed = []
        try:
            details = json.loads(r.port_details) if r.port_details else {}
        except Exception:
            details = {}

        history.append({
            "id": r.id,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            "status": r.status,
            "latency_ms": r.latency_ms,
            "packet_loss_pct": r.packet_loss_pct,
            "open_ports": ports,
            "closed_ports": closed,
            "port_details": details
        })

    return {
        "device_id": device.id,
        "name": device.name,
        "ip_address": device.ip_address,
        "current_status": device.status,
        "history": history
    }

@router.get("/summary")
def get_network_monitoring_summary(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Returns aggregated network monitoring summary stats:
    Total devices, online, offline, unreachable, open/closed TCP checks, avg latency, avg packet loss.
    """
    devices = db.query(NetworkDevice).filter(
        NetworkDevice.tenant_id == current_user.tenant_id
    ).all()

    total_devices = len(devices)
    online_count = sum(1 for d in devices if d.status == "ONLINE")
    degraded_count = sum(1 for d in devices if d.status == "DEGRADED")
    offline_count = sum(1 for d in devices if d.status in ("OFFLINE", "UNREACHABLE"))

    latencies = [d.last_latency_ms for d in devices if d.last_latency_ms > 0]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    packet_losses = [d.last_packet_loss_pct for d in devices]
    avg_packet_loss = round(sum(packet_losses) / len(packet_losses), 2) if packet_losses else 0.0

    # Count total open vs failed ports across devices
    total_open_ports = 0
    total_monitored_ports = 0
    for d in devices:
        try:
            ports = json.loads(d.tcp_ports) if d.tcp_ports else []
            open_p = json.loads(d.open_ports_summary) if d.open_ports_summary else []
            total_monitored_ports += len(ports)
            total_open_ports += len(open_p)
        except Exception:
            pass

    # Recent network alerts
    recent_alerts = db.query(IncidentAlert).filter(
        IncidentAlert.tenant_id == current_user.tenant_id,
        IncidentAlert.alert_type.in_(["NETWORK_DEVICE_UNREACHABLE", "NETWORK_SERVICE_DEGRADED", "LATENCY_SPIKE", "PACKET_LOSS_SPIKE"])
    ).order_by(IncidentAlert.detected_at.desc()).limit(10).all()

    alerts_list = [{
        "id": a.id,
        "alert_type": a.alert_type,
        "severity": a.severity,
        "message": a.message,
        "detected_at": a.detected_at.isoformat() if a.detected_at else None
    } for a in recent_alerts]

    return {
        "total_devices": total_devices,
        "online_devices": online_count,
        "degraded_devices": degraded_count,
        "unreachable_devices": offline_count,
        "avg_latency_ms": avg_latency,
        "avg_packet_loss_pct": avg_packet_loss,
        "total_monitored_ports": total_monitored_ports,
        "total_open_ports": total_open_ports,
        "failed_port_checks": max(0, total_monitored_ports - total_open_ports),
        "recent_alerts": alerts_list
    }
