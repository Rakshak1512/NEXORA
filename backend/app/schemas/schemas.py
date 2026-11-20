from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

# Auth Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "Operator"
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None
    is_active: bool

# Telemetry Ingestion Schemas
class TelemetryIngestPayload(BaseModel):
    payload_id: str
    collector_id: str
    tenant_id: str
    timestamp_utc: str
    version: str = "1.4.2"
    hostname_pseudonym: Optional[str] = None

    # Infrastructure
    cpu_utilization_pct: float
    memory_utilization_pct: float
    memory_used_mb: Optional[float] = 0.0
    memory_total_mb: Optional[float] = 0.0
    disk_utilization_pct: Optional[float] = 0.0
    disk_used_gb: Optional[float] = 0.0
    disk_total_gb: Optional[float] = 0.0
    system_uptime_seconds: Optional[int] = 0
    process_count: Optional[int] = 0
    health_state: Optional[str] = "EXCELLENT"
    health_reason: Optional[str] = None

    # Network
    bytes_sent_rate_kbps: Optional[float] = 0.0
    bytes_recv_rate_kbps: Optional[float] = 0.0
    latency_ms: Optional[float] = 0.0
    packet_loss_pct: Optional[float] = 0.0
    active_connections: Optional[int] = 0
    connectivity_status: Optional[str] = "CONNECTED"

    # Security summary
    failed_login_count: Optional[int] = 0
    suspicious_activity_score: Optional[float] = 0.0
    security_event_severity: Optional[str] = "LOW"
    authentication_failure_rate_per_min: Optional[float] = 0.0
    pseudonymous_source_cluster: Optional[str] = None
    redacted_tokens_detected: Optional[int] = 0
    summary_description: Optional[str] = None

    # Scenario metadata
    is_simulated: Optional[bool] = False
    scenario_name: Optional[str] = "nominal_live"

# Heartbeat
class HeartbeatPayload(BaseModel):
    collector_id: str
    tenant_id: str
    status: str
    uptime_seconds: int
    cpu_usage_pct: float
    memory_usage_mb: float
    queue_backlog_count: int = 0
    version: str = "1.4.2"
    recorded_at: Optional[str] = None

# Egress Proof Schema
class EgressProofPayload(BaseModel):
    payload_id: str
    collector_id: str
    tenant_id: str
    payload_hash_sha256: str
    bytes_transmitted: int
    redacted_fields_count: int
    redacted_field_types: List[str]
    rejected_keys: List[str]
    allowlist_validated: bool
    raw_payload_preview_hash: str
    local_raw_preview: Dict[str, Any]
    outgoing_payload_json: Dict[str, Any]
    destination_endpoint: str
    transmission_status: str = "DELIVERED"
    latency_transit_ms: Optional[float] = 12.0
    sent_at: str
    delivered_at: Optional[str] = None

# Remediation Action Request
class ApprovalActionRequest(BaseModel):
    action: str # "APPROVE" or "REJECT"
    operator_comments: Optional[str] = None

# Incident Status Update
class IncidentUpdateRequest(BaseModel):
    status: str # "INVESTIGATING", "ACKNOWLEDGED", "RESOLVING", "RESOLVED"
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None

# Scenario Trigger
class ScenarioTriggerRequest(BaseModel):
    scenario: str # cpu_spike, memory_spike, disk_spike, failed_logins, saas_outage, recovery_after_outage, etc.
    duration_seconds: Optional[int] = 30

