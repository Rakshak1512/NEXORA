from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

# --- Auth Schemas ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    require_2fa: Optional[bool] = False

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "Operator"
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None

class OrganizationRegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: Optional[str] = None
    organization_name: str
    website_url: Optional[str] = None
    org_slug: Optional[str] = None
    industry: Optional[str] = "Technology"
    org_size: Optional[str] = "10-50"
    country: Optional[str] = "United States"
    job_title: Optional[str] = "Lead Systems Architect"

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str
    purpose: str # "signup", "login", "password_reset"

class OTPResendRequest(BaseModel):
    email: EmailStr
    purpose: str # "signup", "login", "password_reset"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    organization: Optional[Dict[str, Any]] = None

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    job_title: Optional[str] = None
    phone: Optional[str] = None
    is_verified: Optional[bool] = True
    two_factor_enabled: Optional[bool] = False
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None
    is_active: bool

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    two_factor_enabled: Optional[bool] = None

# --- Organization & Member Management ---
class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    org_type: Optional[str] = "Enterprise"
    industry: Optional[str] = "Technology"
    country: Optional[str] = "Global"
    website: Optional[str] = None
    org_size: Optional[str] = "10-50"
    is_active: bool
    created_at: Any

class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    org_size: Optional[str] = None
    country: Optional[str] = None

class MemberResponse(BaseModel):
    id: str
    user_id: str
    email: str
    full_name: str
    role: str
    job_title: Optional[str] = None
    is_active: bool
    created_at: Any

class MemberInviteRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "Infrastructure Engineer" # Organization Owner, Admin, Security Analyst, Infrastructure Engineer, Viewer
    job_title: Optional[str] = None

class MemberUpdateRoleRequest(BaseModel):
    role: str # Organization Owner, Admin, Security Analyst, Infrastructure Engineer, Viewer
    is_active: Optional[bool] = True

# --- API Keys & Developer Portal ---
class APIKeyCreateRequest(BaseModel):
    name: str
    permissions: Optional[List[str]] = ["read", "write"]
    expires_in_days: Optional[int] = 90

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    permissions: List[str]
    last_used_at: Optional[Any] = None
    expires_at: Optional[Any] = None
    is_active: bool
    created_at: Any
    secret_key: Optional[str] = None # Only returned once upon creation!

# --- Embeddable Widgets ---
class EmbedWidgetCreateRequest(BaseModel):
    name: str
    widget_type: str = "health_status" # health_status, incident_summary, collector_fleet, network_uptime
    allowed_domains: Optional[List[str]] = ["*"]
    theme: Optional[str] = "dark"

class EmbedWidgetResponse(BaseModel):
    id: str
    name: str
    token: str
    widget_type: str
    allowed_domains: List[str]
    theme: str
    is_active: bool
    created_at: Any
    embed_url: str
    embed_iframe_code: str

class EmbedWidgetDataResponse(BaseModel):
    organization_name: str
    widget_type: str
    status: str # "ALL_SYSTEMS_OPERATIONAL", "DEGRADED_PERFORMANCE", "MAJOR_OUTAGE"
    theme: str
    active_incidents_count: int
    online_collectors_count: int
    total_collectors_count: int
    average_cpu_pct: float
    average_memory_pct: float
    network_latency_ms: float
    last_updated_at: str

# --- Reports & Analytics ---
class ReportGenerateRequest(BaseModel):
    title: str
    report_type: str = "executive_summary" # executive_summary, security_audit, sla_uptime, incident_rca
    time_range: str = "last_7_days" # last_24_hours, last_7_days, last_30_days

class ReportResponse(BaseModel):
    id: str
    title: str
    report_type: str
    time_range: str
    summary_data: Dict[str, Any]
    created_at: Any

# --- Notifications ---
class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str # info, warning, critical, success
    is_read: bool
    link: Optional[str] = None
    created_at: Any

# --- Telemetry Ingestion Schemas ---
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

    # Network devices checks
    network_devices_checks: Optional[List[Dict[str, Any]]] = None

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
    scenario: str
    duration_seconds: Optional[int] = 30
