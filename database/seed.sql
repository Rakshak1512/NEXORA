-- ====================================================================
-- CICADA OBSERVE: REALISTIC SEED DATA (Simulated & Initial Setup)
-- Clearly marked as realistic operational test data.
-- ====================================================================

-- 1. Insert Initial Organization
INSERT INTO organizations (id, name, slug, plan)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'AcroGlobal Financial', 'acroglobal', 'enterprise'),
    ('00000000-0000-0000-0000-000000000002', 'Nexus Health Technologies', 'nexushealth', 'enterprise')
ON CONFLICT (id) DO NOTHING;

-- 2. Insert Tenants
INSERT INTO tenants (id, organization_id, name, slug, region)
VALUES 
    ('11111111-1111-1111-1111-111111111111', '00000000-0000-0000-0000-000000000001', 'North America Production (US-East)', 'na-prod-useast', 'us-east-1'),
    ('22222222-2222-2222-2222-222222222222', '00000000-0000-0000-0000-000000000001', 'Europe West Operations (Frankfurt)', 'eu-prod-frankfurt', 'eu-central-1')
ON CONFLICT (id) DO NOTHING;

-- 3. Default Users (Password: 'Cicada2026!Secure')
-- Bcrypt hash for 'Cicada2026!Secure'
-- $2b$12$ljZt1mK4gL1xZqB/97QnZ.LhY09O9e0x4KjR7B98e5T4H3kG6oXWy
INSERT INTO profiles (id, email, password_hash, full_name, role, organization_id, tenant_id)
VALUES 
    ('33333333-3333-3333-3333-333333333331', 'admin@cicada.io', '$2b$12$tO3O22p6W3oNvhZ92Psh6u1u7Jv/QzO2U0jE18Kz/Y7PzJ0p6QzOy', 'Alex Vance', 'Super Administrator', '00000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111'),
    ('33333333-3333-3333-3333-333333333332', 'operator@cicada.io', '$2b$12$tO3O22p6W3oNvhZ92Psh6u1u7Jv/QzO2U0jE18Kz/Y7PzJ0p6QzOy', 'Sarah Chen', 'Operator', '00000000-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111')
ON CONFLICT (id) DO NOTHING;

-- 4. Collectors
INSERT INTO collectors (id, tenant_id, name, hostname, ip_address_pseudonym, version, status, auth_token_hash, collection_interval_seconds, last_seen_at)
VALUES 
    ('col-prod-core-01', '11111111-1111-1111-1111-111111111111', 'Primary Cluster Collector 01', 'k8s-node-worker-01.prod.internal', 'node-hash-8f4b2c', '1.4.2', 'online', 'secret-collector-token-01', 10, NOW()),
    ('col-prod-db-02', '11111111-1111-1111-1111-111111111111', 'Postgres Primary Gateway', 'db-pg-cluster-01.prod.internal', 'node-hash-3a9d1e', '1.4.2', 'online', 'secret-collector-token-02', 10, NOW()),
    ('col-edge-ingress-03', '11111111-1111-1111-1111-111111111111', 'Edge Envoy Router', 'gw-edge-ingress-03.prod.internal', 'node-hash-5c2f7b', '1.4.2', 'online', 'secret-collector-token-03', 10, NOW()),
    ('col-backup-agent-04', '11111111-1111-1111-1111-111111111111', 'Disaster Recovery Replica Agent', 'dr-standby-04.dr.internal', 'node-hash-1e8c9a', '1.4.1', 'offline', 'secret-collector-token-04', 10, NOW() - INTERVAL '30 minutes')
ON CONFLICT (id) DO NOTHING;

-- 5. Incidents
INSERT INTO incidents (id, incident_number, tenant_id, collector_id, title, description, severity, status, affected_components, contributing_signals, correlation_reason)
VALUES 
    (
        '44444444-4444-4444-4444-444444444441',
        'INC-2026-0042',
        '11111111-1111-1111-1111-111111111111',
        'col-prod-core-01',
        'Worker Pool Memory Exhaustion & Latency Cascading',
        'Correlated anomaly detected: Memory utilization climbed past 88% alongside a 140ms latency jump on API worker nodes.',
        'HIGH',
        'OPEN',
        '["Worker-Pod-Cluster", "Connection-Pool-TCP", "Redis-Session-Store"]'::jsonb,
        '["Memory surge to 89.4%", "Latency increase to 215ms", "GC pause duration > 800ms"]'::jsonb,
        'Temporal coincidence within 90-second sliding window across same tenant worker node.'
    ),
    (
        '44444444-4444-4444-4444-444444444442',
        'INC-2026-0039',
        '11111111-1111-1111-1111-111111111111',
        'col-edge-ingress-03',
        'Ingress Gateway Packet Drop & Authentication Burst',
        'Edge router experienced 4.8% packet loss during a synchronized authentication retry storm from external banking gateway.',
        'CRITICAL',
        'INVESTIGATING',
        '["Edge-Envoy-Proxy", "TLS-Terminator", "Auth-Rate-Limiter"]'::jsonb,
        '["Packet loss surge from 0.02% to 4.8%", "Failed auth rate reached 124/min", "CPU peak at 93.1%"]'::jsonb,
        'Security summary burst correlated directly with network ingress queue saturation.'
    )
ON CONFLICT (id) DO NOTHING;

-- 6. AI Recommendations
INSERT INTO ai_recommendations (id, incident_id, tenant_id, detected_anomaly, contributing_signals, baseline_comparison, confidence_score, possible_root_cause, recommended_investigation, suggested_action, suggested_action_type, rollback_plan, is_deterministic_fallback)
VALUES 
    (
        '55555555-5555-5555-5555-555555555551',
        '44444444-4444-4444-4444-444444444441',
        '11111111-1111-1111-1111-111111111111',
        'Severe JVM / Worker Memory Saturation with Correlated Latency Degrade',
        '["Node memory 89.4%", "HTTP P95 latency 215ms (+180% above 75ms baseline)"]'::jsonb,
        'Historical 7-day median memory is 54.2% (sigma = 4.1%). Current observation is +8.5 sigmas from baseline.',
        94.80,
        'Unbounded connection leak or uncollected session token cache in ingress worker thread pool.',
        'Review recent deployment commits on auth cache, inspect thread dump metadata without extracting payload bodies.',
        'Safely trigger worker pod rolling drain and recycle idle connection pools.',
        'ROLLING_RECYCLE_CONTAINERS',
        'Revert replica count to standby baseline; restore previous image hash if crash-loop occurs.',
        TRUE
    ),
    (
        '55555555-5555-5555-5555-555555555552',
        '44444444-4444-4444-4444-444444444442',
        '11111111-1111-1111-1111-111111111111',
        'Ingress Gateway SYN / Auth Buffer Exhaustion',
        '["Failed auth spike: 124/min", "Packet drop: 4.8%", "Ingress CPU: 93.1%"]'::jsonb,
        'Normal baseline failed logins: < 3/min. Normal packet loss: < 0.05%. Anomaly deviation score: 98.7/100.',
        96.20,
        'Distributed credential stuffing pattern or unthrottled client retry loop overwhelming gateway rate limits.',
        'Inspect pseudonymous source hash distribution to identify origin cluster without accessing raw IP addresses.',
        'Engage proactive adaptive edge rate limiting on pseudonymous cluster hash node-hash-5c2f7b.',
        'ENGAGE_ADAPTIVE_EDGE_THROTTLING',
        'Release temporary rate limit policy after 15-minute cooling window or manual operator override.',
        TRUE
    )
ON CONFLICT (id) DO NOTHING;

-- 7. Remediation Approvals
INSERT INTO remediation_approvals (id, recommendation_id, incident_id, tenant_id, action_description, target_component, policy_evaluation_result, status, rollback_information)
VALUES 
    (
        '66666666-6666-6666-6666-666666666661',
        '55555555-5555-5555-5555-555555555551',
        '44444444-4444-4444-4444-444444444441',
        '11111111-1111-1111-1111-111111111111',
        'Perform staged graceful restart of 4 worker instances and flush expired memory caches.',
        'Worker-Pod-Cluster (col-prod-core-01)',
        'POLICY_PASSED_REQUIRES_OPERATOR_SIGN_OFF',
        'PENDING',
        'Automated health check probes will instantly roll back to previous deployment state if 3 consecutive failures occur within 30s.'
    ),
    (
        '66666666-6666-6666-6666-666666666662',
        '55555555-5555-5555-5555-555555555552',
        '44444444-4444-4444-4444-444444444442',
        '11111111-1111-1111-1111-111111111111',
        'Enforce adaptive rate limiting on edge router node-hash-5c2f7b (50 req/sec ceiling).',
        'Edge-Envoy-Proxy (col-edge-ingress-03)',
        'POLICY_PASSED_REQUIRES_OPERATOR_SIGN_OFF',
        'APPROVED',
        'Policy timer automatically expires in 900 seconds or can be manually revoked via Operator Console.'
    )
ON CONFLICT (id) DO NOTHING;

