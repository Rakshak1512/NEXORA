-- ====================================================================
-- CYNERA: PRODUCTION DATABASE SCHEMA (Supabase PostgreSQL)
-- Cyber Network Evaluation and Risk Analytics
-- Two-Tier Architecture: Only Approved Metadata & Derived Summaries
-- Raw logs, secrets, and raw credentials are NEVER stored.
-- ====================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. ORGANIZATIONS & TENANTS (Multi-tenant Architecture)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'enterprise',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    region VARCHAR(50) DEFAULT 'us-east-1',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, slug)
);

-- 3. PROFILES & ROLES
CREATE TYPE user_role_enum AS ENUM (
    'Super Administrator',
    'Organization Administrator',
    'Operator',
    'Viewer'
);

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'Operator',
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. COLLECTORS & REGISTRATIONS
CREATE TYPE collector_status_enum AS ENUM ('online', 'offline', 'degraded', 'pending');

CREATE TABLE IF NOT EXISTS collectors (
    id VARCHAR(100) PRIMARY KEY, -- e.g. 'col-us-east-prod-01'
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    ip_address_pseudonym VARCHAR(100) NOT NULL, -- Pseudonymized for privacy
    version VARCHAR(50) NOT NULL,
    status collector_status_enum DEFAULT 'pending',
    auth_token_hash VARCHAR(255) NOT NULL,
    collection_interval_seconds INT DEFAULT 10,
    allowed_metrics JSONB DEFAULT '["cpu", "memory", "disk", "network", "security_summary"]'::jsonb,
    last_seen_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collector_heartbeats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collector_id VARCHAR(100) NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    status collector_status_enum NOT NULL,
    uptime_seconds BIGINT NOT NULL,
    cpu_usage_pct NUMERIC(5,2),
    memory_usage_mb NUMERIC(10,2),
    queue_backlog_count INT DEFAULT 0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. INFRASTRUCTURE & NETWORK METRICS (Approved Aggregated Metadata Only)
CREATE TABLE IF NOT EXISTS infrastructure_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payload_id VARCHAR(100) UNIQUE NOT NULL, -- Idempotency key
    collector_id VARCHAR(100) NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    cpu_utilization_pct NUMERIC(5,2) NOT NULL,
    memory_utilization_pct NUMERIC(5,2) NOT NULL,
    memory_used_mb NUMERIC(12,2) NOT NULL,
    memory_total_mb NUMERIC(12,2) NOT NULL,
    disk_utilization_pct NUMERIC(5,2) NOT NULL,
    disk_used_gb NUMERIC(10,2) NOT NULL,
    disk_total_gb NUMERIC(10,2) NOT NULL,
    system_uptime_seconds BIGINT NOT NULL,
    process_count INT NOT NULL,
    health_state VARCHAR(20) DEFAULT 'EXCELLENT', -- EXCELLENT, GOOD, FAIR, POOR
    health_reason TEXT,
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS network_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payload_id VARCHAR(100) NOT NULL,
    collector_id VARCHAR(100) NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    bytes_sent_rate_kbps NUMERIC(12,2) DEFAULT 0,
    bytes_recv_rate_kbps NUMERIC(12,2) DEFAULT 0,
    latency_ms NUMERIC(8,2) DEFAULT 0,
    packet_loss_pct NUMERIC(5,2) DEFAULT 0,
    active_connections INT DEFAULT 0,
    connectivity_status VARCHAR(50) DEFAULT 'CONNECTED',
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. SECURITY SUMMARIES (Derived summaries only - NO RAW LOGS OR SECRETS)
CREATE TABLE IF NOT EXISTS security_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payload_id VARCHAR(100) NOT NULL,
    collector_id VARCHAR(100) NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    failed_login_count INT DEFAULT 0,
    suspicious_activity_score NUMERIC(5,2) DEFAULT 0, -- 0 to 100
    security_event_severity VARCHAR(20) DEFAULT 'LOW', -- LOW, MEDIUM, HIGH, CRITICAL
    authentication_failure_rate_per_min NUMERIC(8,2) DEFAULT 0,
    pseudonymous_source_cluster VARCHAR(100),
    redacted_tokens_detected INT DEFAULT 0,
    summary_description TEXT,
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. EGRESS METADATA & PROOF CENTER (Audit trail proving exact payloads leaving local environment)
CREATE TABLE IF NOT EXISTS egress_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payload_id VARCHAR(100) UNIQUE NOT NULL,
    collector_id VARCHAR(100) NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    payload_hash_sha256 VARCHAR(64) NOT NULL,
    bytes_transmitted INT NOT NULL,
    redacted_fields_count INT DEFAULT 0,
    redacted_field_types JSONB DEFAULT '[]'::jsonb, -- e.g. ["password", "api_key", "bearer_token"]
    allowlist_validated BOOLEAN DEFAULT TRUE,
    raw_payload_preview_hash VARCHAR(64) NOT NULL, -- SHA256 of local preview (not raw text)
    outgoing_payload_json JSONB NOT NULL, -- The clean approved JSON payload
    destination_endpoint VARCHAR(255) NOT NULL,
    transmission_status VARCHAR(50) DEFAULT 'DELIVERED', -- PENDING, DELIVERED, RETRIED, ACKNOWLEDGED
    latency_transit_ms NUMERIC(8,2),
    sent_at TIMESTAMPTZ NOT NULL,
    delivered_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. ALERTS, INCIDENTS & AIOPS
CREATE TYPE severity_level_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE incident_status_enum AS ENUM ('OPEN', 'INVESTIGATING', 'ACKNOWLEDGED', 'RESOLVING', 'RESOLVED');

CREATE TABLE IF NOT EXISTS incident_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    collector_id VARCHAR(100) NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL, -- e.g. 'CPU_SATURATION', 'MEMORY_LEAK_BURST', 'PACKET_LOSS_SURGE'
    severity severity_level_enum NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC(10,2) NOT NULL,
    threshold_value NUMERIC(10,2) NOT NULL,
    message TEXT NOT NULL,
    is_correlated BOOLEAN DEFAULT FALSE,
    incident_id UUID, -- Back reference once correlated
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_number VARCHAR(50) UNIQUE NOT NULL, -- e.g. 'INC-2026-0042'
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    collector_id VARCHAR(100) NOT NULL REFERENCES collectors(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity severity_level_enum NOT NULL,
    status incident_status_enum DEFAULT 'OPEN',
    affected_components JSONB DEFAULT '[]'::jsonb,
    contributing_signals JSONB DEFAULT '[]'::jsonb,
    correlation_reason TEXT,
    assigned_to UUID REFERENCES profiles(id) ON DELETE SET NULL,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

ALTER TABLE incident_alerts 
ADD CONSTRAINT fk_incident_alert_incident 
FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE SET NULL;

-- 9. AI RECOMMENDATIONS & EXPLAINABILITY
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    detected_anomaly VARCHAR(255) NOT NULL,
    contributing_signals JSONB NOT NULL,
    baseline_comparison TEXT NOT NULL,
    confidence_score NUMERIC(5,2) NOT NULL, -- e.g. 94.50%
    possible_root_cause TEXT NOT NULL,
    recommended_investigation TEXT NOT NULL,
    suggested_action TEXT NOT NULL,
    suggested_action_type VARCHAR(100) NOT NULL, -- e.g. 'RESTART_SERVICE', 'DRAIN_CONNECTIONS', 'FLUSH_CACHE'
    rollback_plan TEXT NOT NULL,
    is_deterministic_fallback BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. APPROVAL CENTER & AUTONOMOUS OPERATIONS (Safe policy-controlled human approval)
CREATE TYPE approval_status_enum AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'EXECUTED', 'ROLLED_BACK');

CREATE TABLE IF NOT EXISTS remediation_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID NOT NULL REFERENCES ai_recommendations(id) ON DELETE CASCADE,
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    action_description TEXT NOT NULL,
    target_component VARCHAR(255) NOT NULL,
    policy_evaluation_result VARCHAR(100) DEFAULT 'POLICY_PASSED_REQUIRES_OPERATOR_SIGN_OFF',
    status approval_status_enum DEFAULT 'PENDING',
    operator_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    operator_comments TEXT,
    simulated_execution_log TEXT,
    rollback_information TEXT NOT NULL,
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    actioned_at TIMESTAMPTZ
);

-- 11. AUDIT LOGS & SYSTEM COMPLIANCE
CREATE TABLE IF NOT EXISTS system_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. PERFORMANCE BENCHMARKS & LATENCY TRACKING
CREATE TABLE IF NOT EXISTS performance_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    p50_latency_ms NUMERIC(8,2) NOT NULL,
    p95_latency_ms NUMERIC(8,2) NOT NULL,
    alert_generation_time_ms NUMERIC(8,2) NOT NULL,
    heartbeat_age_seconds INT NOT NULL,
    queue_backlog_depth INT DEFAULT 0,
    delivery_success_pct NUMERIC(5,2) DEFAULT 100.0,
    duplicate_count INT DEFAULT 0,
    lost_record_count INT DEFAULT 0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. INDEXES FOR HIGH-THROUGHPUT RETRIEVAL
CREATE INDEX IF NOT EXISTS idx_infra_collector ON infrastructure_metrics(collector_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_infra_tenant ON infrastructure_metrics(tenant_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_network_collector ON network_metrics(collector_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_tenant ON security_summaries(tenant_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_egress_payload ON egress_metadata(payload_id);
CREATE INDEX IF NOT EXISTS idx_incidents_tenant ON incidents(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_alerts_incident ON incident_alerts(incident_id);
CREATE INDEX IF NOT EXISTS idx_heartbeats_collector ON collector_heartbeats(collector_id, recorded_at DESC);

-- 14. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE infrastructure_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE network_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE egress_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE remediation_approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_audit_logs ENABLE ROW LEVEL SECURITY;

-- Note: In Supabase environment, auth.uid() matches profiles.id.
-- Policies ensure tenant-isolation across all multi-tenant queries.

