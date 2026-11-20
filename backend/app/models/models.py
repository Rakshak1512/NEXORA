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

# =====================================================================
# 1. ORGANIZATIONS, TENANTS, PROFILES & SAAS MEMBERSHIPS
# =====================================================================
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
    websites = relationship("MonitoredWebsite", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")
    app_services = relationship("ApplicationService", back_populates="organization", cascade="all, delete-orphan")
    db_integrations = relationship("DatabaseIntegration", back_populates="organization", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="organization", cascade="all, delete-orphan")

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

# =====================================================================
# 2. WEBSITE & APPLICATION MONITORING (PRODUCT A - Zero Collector Required)
# =====================================================================
class MonitoredWebsite(Base):
    __tablename__ = "monitored_websites"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(50), default="dns_txt") # dns_txt, http_file, meta_tag, manual
    verification_token = Column(String(100), nullable=False, default=lambda: f"cynera-verify-{uuid.uuid4().hex[:16]}")
    status = Column(String(50), default="PENDING") # ONLINE, DEGRADED, DOWN, TIMEOUT, DNS_FAILURE, TLS_FAILURE, HTTP_ERROR, PAUSED, PENDING
    monitoring_interval_seconds = Column(Integer, default=60) # 30, 60, 300, 600
    expected_status_codes = Column(Text, default='[200, 201, 204, 301, 302]')
    timeout_seconds = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    consecutive_failures = Column(Integer, default=0)
    consecutive_successes = Column(Integer, default=0)
    last_checked_at = Column(DateTime, nullable=True)
    last_status_code = Column(Integer, nullable=True)
    last_response_time_ms = Column(Float, default=0.0)
    uptime_percentage_24h = Column(Float, default=100.0)
    ssl_status = Column(String(50), default="VALID") # VALID, WARNING, EXPIRED, INVALID, UNKNOWN
    ssl_issuer = Column(String(255), nullable=True)
    ssl_expiry_date = Column(DateTime, nullable=True)
    ssl_days_remaining = Column(Integer, nullable=True)
    dns_status = Column(String(50), default="HEALTHY") # HEALTHY, DEGRADED, FAILED
    dns_resolved_ips = Column(Text, default='[]') # JSON list
    dns_lookup_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="websites")
    check_results = relationship("WebsiteCheckResult", back_populates="website", cascade="all, delete-orphan")
    endpoints = relationship("WebsiteEndpoint", back_populates="website", cascade="all, delete-orphan")

class WebsiteCheckResult(Base):
    __tablename__ = "website_check_results"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    website_id = Column(String(36), ForeignKey("monitored_websites.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False) # ONLINE, DEGRADED, DOWN, TIMEOUT, DNS_FAILURE, TLS_FAILURE, HTTP_ERROR
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, default=0.0)
    dns_lookup_time_ms = Column(Float, default=0.0)
    tls_handshake_time_ms = Column(Float, default=0.0)
    dns_resolved_ips = Column(Text, default='[]')
    ssl_valid = Column(Boolean, default=True)
    ssl_days_remaining = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    check_location = Column(String(50), default="SaaS Primary Cloud")
    recorded_at = Column(DateTime, default=utc_now)

    website = relationship("MonitoredWebsite", back_populates="check_results")

class WebsiteEndpoint(Base):
    __tablename__ = "website_endpoints"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    website_id = Column(String(36), ForeignKey("monitored_websites.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    endpoint_url = Column(String(500), nullable=False)
    method = Column(String(10), default="GET")
    expected_status_code = Column(Integer, default=200)
    is_active = Column(Boolean, default=True)
    last_status = Column(String(50), default="ONLINE")
    last_latency_ms = Column(Float, default=0.0)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    website = relationship("MonitoredWebsite", back_populates="endpoints")

# =====================================================================
# 3. APPLICATION PERFORMANCE MONITORING (APM - SDK Integrations)
# =====================================================================
class ApplicationService(Base):
    __tablename__ = "application_services"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False) # e.g. "Payment Gateway API"
    language = Column(String(50), default="Python") # Python, JavaScript/Node, Go
    environment = Column(String(50), default="production") # production, staging, development
    version = Column(String(50), default="1.0.0")
    api_key_id = Column(String(36), nullable=True)
    status = Column(String(50), default="HEALTHY") # HEALTHY, DEGRADED, CRITICAL
    last_heartbeat_at = Column(DateTime, nullable=True)
    avg_latency_ms = Column(Float, default=0.0)
    error_rate_pct = Column(Float, default=0.0)
    request_count_24h = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="app_services")
    events = relationship("ApplicationEvent", back_populates="service", cascade="all, delete-orphan")

class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    service_id = Column(String(36), ForeignKey("application_services.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), default="error") # error, exception, trace, warning, metric
    name = Column(String(255), nullable=False) # e.g. "DatabaseConnectionError"
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    duration_ms = Column(Float, default=0.0)
    status_code = Column(Integer, nullable=True)
    recorded_at = Column(DateTime, default=utc_now)

    service = relationship("ApplicationService", back_populates="events")

# =====================================================================
# 4. DATABASE MONITORING (PostgreSQL / MySQL Integrations)
# =====================================================================
class DatabaseIntegration(Base):
    __tablename__ = "database_integrations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    db_type = Column(String(50), default="PostgreSQL") # PostgreSQL, MySQL, Redis
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=5432)
    database_name = Column(String(100), default="postgres")
    username_masked = Column(String(100), default="cynera_monitor_ro")
    status = Column(String(50), default="HEALTHY") # HEALTHY, DEGRADED, OFFLINE
    avg_query_latency_ms = Column(Float, default=0.0)
    active_connections = Column(Integer, default=0)
    max_connections = Column(Integer, default=100)
    pool_saturation_pct = Column(Float, default=0.0)
    slow_queries_count = Column(Integer, default=0)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="db_integrations")
    metrics = relationship("DatabaseMetric", back_populates="integration", cascade="all, delete-orphan")

class DatabaseMetric(Base):
    __tablename__ = "database_metrics"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    integration_id = Column(String(36), ForeignKey("database_integrations.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    connection_status = Column(String(50), default="CONNECTED")
    latency_ms = Column(Float, default=0.0)
    active_connections = Column(Integer, default=0)
    slow_query_count = Column(Integer, default=0)
    cache_hit_ratio_pct = Column(Float, default=99.2)
    recorded_at = Column(DateTime, default=utc_now)

    integration = relationship("DatabaseIntegration", back_populates="metrics")

# =====================================================================
# 5. ALERT CENTER & WEBHOOKS
# =====================================================================
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    severity = Column(String(20), default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    category = Column(String(50), default="website") # website, infrastructure, network, application, database, security
    resource_name = Column(String(255), nullable=False)
    resource_id = Column(String(100), nullable=True)
    evidence = Column(Text, nullable=False)
    status = Column(String(20), default="ACTIVE") # ACTIVE, ACKNOWLEDGED, RESOLVED
    incident_id = Column(String(36), nullable=True)
    notification_sent = Column(Boolean, default=False)
    detected_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="alerts")

class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    destination_url = Column(String(500), nullable=False) # HTTPS required, SSRF protected
    secret_hash = Column(String(255), nullable=False) # HMAC secret hash
    secret_preview = Column(String(30), nullable=False) # e.g. "whsec_4f..."
    events = Column(Text, default='["alert.created", "incident.created", "website.down", "website.recovered"]')
    is_active = Column(Boolean, default=True)
    last_delivery_status = Column(String(50), nullable=True) # SUCCESS, FAILED, TIMEOUT
    last_delivery_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    webhook_id = Column(String(36), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload_json = Column(Text, nullable=False)
    response_status_code = Column(Integer, nullable=True)
    response_body_preview = Column(Text, nullable=True)
    execution_time_ms = Column(Float, default=0.0)
    status = Column(String(50), default="SUCCESS") # SUCCESS, FAILED
    delivered_at = Column(DateTime, default=utc_now)

    webhook = relationship("Webhook", back_populates="deliveries")

# =====================================================================
# 6. INFRASTRUCTURE & COLLECTORS (PRODUCT B - Tier 1 Local Collector)
# =====================================================================
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

# =====================================================================
# 7. AIOPS INCIDENTS, ALERTS & AUTONOMOUS RECOMMENDATIONS
# =====================================================================
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
    collector_id = Column(String(100), ForeignKey("collectors.id", ondelete="CASCADE"), nullable=True)
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

# =====================================================================
# 8. TCP/IP & IP-BASED NETWORK DEVICES
# =====================================================================
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
