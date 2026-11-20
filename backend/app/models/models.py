import uuid
import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from ..database import Base

def gen_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default="enterprise")
    org_type = Column(String(100), default="Enterprise")
    industry = Column(String(100), default="Technology")
    country = Column(String(100), default="Global")
    website = Column(String(255), nullable=True)
    org_size = Column(String(50), default="10-50")
    owner_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)

    tenants = relationship("Tenant", back_populates="organization", cascade="all, delete-orphan")
    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    embed_tokens = relationship("EmbedWidgetToken", back_populates="organization", cascade="all, delete-orphan")

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    region = Column(String(50), default="us-east-1")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="tenants")
    collectors = relationship("Collector", back_populates="tenant", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="Operator") # Super Administrator, Organization Owner, Admin, Security Analyst, Infrastructure Engineer, Operator, Viewer
    job_title = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    is_verified = Column(Boolean, default=True)
    two_factor_enabled = Column(Boolean, default=False)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    memberships = relationship("OrganizationMembership", back_populates="user", cascade="all, delete-orphan")

class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="Organization Owner") # Organization Owner, Admin, Security Analyst, Infrastructure Engineer, Viewer
    is_active = Column(Boolean, default=True)
    invited_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("Profile", back_populates="memberships")

class OTPChallenge(Base):
    __tablename__ = "otp_challenges"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), index=True, nullable=False)
    otp_hash = Column(String(255), nullable=False)
    purpose = Column(String(50), nullable=False) # signup, login, password_reset
    attempts = Column(Integer, default=0)
    resend_count = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    last_sent_at = Column(DateTime, default=utc_now)
    payload_data = Column(Text, default="{}") # Stores pending signup info until verified
    created_at = Column(DateTime, default=utc_now)

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(30), nullable=False) # e.g. cyn_live_4f8a...
    key_hash = Column(String(255), nullable=False) # SHA-256 hash of complete key
    permissions = Column(Text, default='["read", "write"]')
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="api_keys")

class EmbedWidgetToken(Base):
    __tablename__ = "embed_widget_tokens"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    token = Column(String(64), unique=True, index=True, nullable=False)
    widget_type = Column(String(50), default="health_status") # health_status, incident_summary, collector_fleet, network_uptime
    allowed_domains = Column(Text, default='["*"]')
    theme = Column(String(20), default="dark")
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="embed_tokens")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True) # null = org-wide
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info") # info, warning, critical, success
    is_read = Column(Boolean, default=False)
    link = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now)

class ReportRecord(Base):
    __tablename__ = "report_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), default="executive_summary") # executive_summary, security_audit, sla_uptime, incident_rca
    time_range = Column(String(50), default="last_7_days")
    summary_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

class Collector(Base):
    __tablename__ = "collectors"

    id = Column(String(100), primary_key=True) # e.g. 'col-prod-core-01'
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    hostname = Column(String(255), nullable=False)
    ip_address_pseudonym = Column(String(100), nullable=False)
    version = Column(String(50), default="1.4.2")
    status = Column(String(20), default="online") # online, offline, degraded
    auth_token_hash = Column(String(255), nullable=False)
    collection_interval_seconds = Column(Integer, default=5)
    last_seen_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)

    tenant = relationship("Tenant", back_populates="collectors")

class CollectorHeartbeat(Base):
    __tablename__ = "collector_heartbeats"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    collector_id = Column(String(100), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)
    uptime_seconds = Column(Integer, default=0)
    cpu_usage_pct = Column(Float, default=0.0)
    memory_usage_mb = Column(Float, default=0.0)
    queue_backlog_count = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=utc_now)

class InfrastructureMetric(Base):
    __tablename__ = "infrastructure_metrics"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    payload_id = Column(String(100), unique=True, nullable=False)
    collector_id = Column(String(100), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    cpu_utilization_pct = Column(Float, nullable=False)
    memory_utilization_pct = Column(Float, nullable=False)
    memory_used_mb = Column(Float, default=0.0)
    memory_total_mb = Column(Float, default=0.0)
    disk_utilization_pct = Column(Float, default=0.0)
    disk_used_gb = Column(Float, default=0.0)
    disk_total_gb = Column(Float, default=0.0)
    system_uptime_seconds = Column(Integer, default=0)
    process_count = Column(Integer, default=0)
    health_state = Column(String(20), default="EXCELLENT") # EXCELLENT, GOOD, FAIR, POOR
    health_reason = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=utc_now)

class NetworkMetric(Base):
    __tablename__ = "network_metrics"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    payload_id = Column(String(100), nullable=False)
    collector_id = Column(String(100), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    bytes_sent_rate_kbps = Column(Float, default=0.0)
    bytes_recv_rate_kbps = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    packet_loss_pct = Column(Float, default=0.0)
    active_connections = Column(Integer, default=0)
    connectivity_status = Column(String(50), default="CONNECTED")
    recorded_at = Column(DateTime, default=utc_now)

class SecuritySummary(Base):
    __tablename__ = "security_summaries"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    payload_id = Column(String(100), nullable=False)
    collector_id = Column(String(100), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    failed_login_count = Column(Integer, default=0)
    suspicious_activity_score = Column(Float, default=0.0)
    security_event_severity = Column(String(20), default="LOW")
    authentication_failure_rate_per_min = Column(Float, default=0.0)
    pseudonymous_source_cluster = Column(String(100), nullable=True)
    redacted_tokens_detected = Column(Integer, default=0)
    summary_description = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=utc_now)

class EgressMetadata(Base):
    __tablename__ = "egress_metadata"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    payload_id = Column(String(100), unique=True, nullable=False)
    collector_id = Column(String(100), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    payload_hash_sha256 = Column(String(64), nullable=False)
    bytes_transmitted = Column(Integer, nullable=False)
    redacted_fields_count = Column(Integer, default=0)
    redacted_field_types = Column(Text, default="[]") # JSON string
    rejected_keys = Column(Text, default="[]") # JSON string
    allowlist_validated = Column(Boolean, default=True)
    raw_payload_preview_hash = Column(String(64), nullable=False)
    local_raw_preview = Column(Text, default="{}") # Masked preview json
    outgoing_payload_json = Column(Text, nullable=False) # Clean JSON string
    destination_endpoint = Column(String(255), nullable=False)
    transmission_status = Column(String(50), default="DELIVERED")
    latency_transit_ms = Column(Float, default=0.0)
    sent_at = Column(DateTime, default=utc_now)
    delivered_at = Column(DateTime, default=utc_now)

class IncidentAlert(Base):
    __tablename__ = "incident_alerts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    collector_id = Column(String(100), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    is_correlated = Column(Boolean, default=False)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    detected_at = Column(DateTime, default=utc_now)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    incident_number = Column(String(50), unique=True, nullable=False) # e.g. INC-2026-0042
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    collector_id = Column(String(100), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(20), default="OPEN") # OPEN, INVESTIGATING, ACKNOWLEDGED, RESOLVING, RESOLVED
    affected_components = Column(Text, default="[]") # JSON list
    contributing_signals = Column(Text, default="[]") # JSON list
    correlation_reason = Column(Text, nullable=True)
    assigned_to = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    detected_anomaly = Column(String(255), nullable=False)
    contributing_signals = Column(Text, default="[]")
    baseline_comparison = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    possible_root_cause = Column(Text, nullable=False)
    recommended_investigation = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    suggested_action_type = Column(String(100), nullable=False)
    rollback_plan = Column(Text, nullable=False)
    is_deterministic_fallback = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

class RemediationApproval(Base):
    __tablename__ = "remediation_approvals"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    recommendation_id = Column(String(36), ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    action_description = Column(Text, nullable=False)
    target_component = Column(String(255), nullable=False)
    policy_evaluation_result = Column(String(100), default="POLICY_PASSED_REQUIRES_OPERATOR_SIGN_OFF")
    status = Column(String(20), default="PENDING") # PENDING, APPROVED, REJECTED, EXECUTED, ROLLED_BACK
    operator_id = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    operator_comments = Column(Text, nullable=True)
    simulated_execution_log = Column(Text, nullable=True)
    rollback_information = Column(Text, nullable=False)
    requested_at = Column(DateTime, default=utc_now)
    actioned_at = Column(DateTime, nullable=True)

class SystemAuditLog(Base):
    __tablename__ = "system_audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    details = Column(Text, default="{}")
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)

class PerformanceBenchmark(Base):
    __tablename__ = "performance_benchmarks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    p50_latency_ms = Column(Float, default=12.4)
    p95_latency_ms = Column(Float, default=24.8)
    alert_generation_time_ms = Column(Float, default=45.2)
    heartbeat_age_seconds = Column(Integer, default=5)
    queue_backlog_depth = Column(Integer, default=0)
    delivery_success_pct = Column(Float, default=100.0)
    duplicate_count = Column(Integer, default=0)
    lost_record_count = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=utc_now)

class NetworkDevice(Base):
    __tablename__ = "network_devices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    ip_address = Column(String(100), nullable=False)
    device_type = Column(String(50), default="Server") # Server, Router, Switch, Firewall, Workstation, Other
    monitoring_methods = Column(Text, default='["ping", "tcp"]') # JSON list: ping, tcp, snmp, ssh, syslog
    tcp_ports = Column(Text, default='[80, 443]') # JSON list: e.g. [80, 443, 22]
    monitoring_interval_seconds = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="ONLINE") # ONLINE, DEGRADED, OFFLINE, UNREACHABLE, UNKNOWN
    last_latency_ms = Column(Float, default=0.0)
    last_packet_loss_pct = Column(Float, default=0.0)
    open_ports_summary = Column(Text, default='[]') # JSON list
    snmp_config = Column(Text, default='{}') # Port 161, version v2c/v3, safe metadata
    ssh_config = Column(Text, default='{}')  # Port 22, safe user metadata
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)

class NetworkCheckResult(Base):
    __tablename__ = "network_check_results"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    device_id = Column(String(36), ForeignKey("network_devices.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    collector_id = Column(String(100), nullable=True)
    check_type = Column(String(50), default="ping") # ping, tcp, snmp, ssh, syslog
    status = Column(String(50), default="SUCCESS") # SUCCESS, FAILED, DEGRADED, CLOSED, FILTERED, UNREACHABLE
    latency_ms = Column(Float, default=0.0)
    packet_loss_pct = Column(Float, default=0.0)
    open_ports = Column(Text, default='[]') # JSON list: [80, 443]
    closed_ports = Column(Text, default='[]') # JSON list: [22]
    port_details = Column(Text, default='{}') # JSON dict of port -> {status, latency_ms}
    metrics_payload = Column(Text, default='{}') # Approved metadata (interfaces, etc.)
    error_message = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=utc_now)
