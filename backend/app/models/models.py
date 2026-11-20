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
    created_at = Column(DateTime, default=utc_now)

    tenants = relationship("Tenant", back_populates="organization", cascade="all, delete-orphan")

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
    role = Column(String(50), default="Operator") # Super Administrator, Organization Administrator, Operator, Viewer
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
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

