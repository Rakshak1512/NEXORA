import os
import json
import datetime
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from . import database as db_module
from .database import engine, Base, SessionLocal, test_database_connection
from .models.models import (
    Organization, Tenant, Profile, Collector, Incident,
    IncidentAlert, AIRecommendation, RemediationApproval, PerformanceBenchmark, EgressMetadata,
    Webhook, WebhookDelivery, CollectorHeartbeat, ReportRecord, WebsiteCheckResult,
    DatabaseMetric, ApplicationEvent,
    InfrastructureMetric, NetworkMetric, SecuritySummary,
    NetworkDevice, NetworkCheckResult, OrganizationMembership,
    APIKey, EmbedWidgetToken, Notification
)
from .auth.jwt import get_password_hash, decode_access_token
from .websocket.manager import ws_manager

# API Routers
from .api.auth import router as auth_router
from .api.admin import router as admin_router
from .api.collectors import router as collectors_router
from .api.telemetry import router as telemetry_router
from .api.metrics import router as metrics_router
from .api.incidents import router as incidents_router
from .api.egress import router as egress_router
from .api.approvals import router as approvals_router
from .api.scenarios import router as operations_router
from .api.settings import router as settings_router
from .api.network import router as network_router
from .api.organization import router as organization_router
from .api.developer import router as developer_router
from .api.reports import router as reports_router
from .api.notifications import router as notifications_router
from .api.websites import router as websites_router
from .api.apm import router as apm_router
from .api.databases import router as databases_router
from .api.alerts import router as alerts_router
from .api.webhooks import router as webhooks_router
from .services.website_scheduler import website_scheduler
from .services.rate_limiter import rate_limiter
from fastapi import Request
from fastapi.responses import JSONResponse
from .models.models import (
    MonitoredWebsite, WebsiteCheckResult, ApplicationService,
    DatabaseIntegration, Alert
)

def seed_database_if_empty():
    """Seed synthetic fixtures only after an explicit DEMO_MODE opt-in."""
    if not settings.DEMO_MODE:
        print("[Database] Demo seeding disabled; set DEMO_MODE=true only on a disposable demo database.")
        return
    active_engine = getattr(db_module, 'engine', engine)
    active_session = getattr(db_module, 'SessionLocal', SessionLocal)
    if not active_engine or not active_session:
        print("[Database] Primary database engine is not configured. Startup seeding skipped (BLOCKED_BY_CONFIGURATION).")
        return
    try:
        Base.metadata.create_all(bind=active_engine)
    except Exception as e:
        print(f"[Database] Warning: Could not complete DDL schema migration on active engine: {e}")
        return

    try:
        db = active_session()
    except Exception as e:
        print(f"[Database] Warning: Could not open database session on active engine: {e}")
        return
    try:
        if db.query(Organization).count() == 0:
            print("[Database] Seeding initial database tables and mock records...")
            # 1. Organization
            org = Organization(
                id="00000000-0000-0000-0000-000000000001",
                name="AcroGlobal Financial",
                slug="acroglobal",
                plan="enterprise"
            )
            db.add(org)
            db.flush()

            # 2. Tenants
            t1 = Tenant(
                id="11111111-1111-1111-1111-111111111111",
                organization_id=org.id,
                name="North America Production (US-East)",
                slug="na-prod-useast",
                region="us-east-1"
            )
            t2 = Tenant(
                id="22222222-2222-2222-2222-222222222222",
                organization_id=org.id,
                name="Europe West Operations (Frankfurt)",
                slug="eu-prod-frankfurt",
                region="eu-central-1"
            )
            db.add_all([t1, t2])
            db.flush()

            # 3. Default Users
            pw_hash_cynera = get_password_hash("Cynera2026!Secure")
            pw_hash_cicada = get_password_hash("Cicada2026!Secure")
            u1 = Profile(
                id="33333333-3333-3333-3333-333333333333",
                email="admin@cynera.io",
                password_hash=pw_hash_cynera,
                full_name="Alex Vance",
                role="Super Administrator",
                organization_id=org.id,
                tenant_id=t1.id
            )
            u2 = Profile(
                id="33333333-3333-3333-3333-333333333334",
                email="operator@cynera.io",
                password_hash=pw_hash_cynera,
                full_name="Sarah Chen",
                role="Operator",
                organization_id=org.id,
                tenant_id=t1.id
            )
            # Backward-compatible accounts
            u_compat1 = Profile(
                id="33333333-3333-3333-3333-333333333331",
                email="admin@cicada.io",
                password_hash=pw_hash_cicada,
                full_name="Alex Vance",
                role="Super Administrator",
                organization_id=org.id,
                tenant_id=t1.id
            )
            u_compat2 = Profile(
                id="33333333-3333-3333-3333-333333333332",
                email="operator@cicada.io",
                password_hash=pw_hash_cicada,
                full_name="Sarah Chen",
                role="Operator",
                organization_id=org.id,
                tenant_id=t1.id
            )
            db.add_all([u1, u2, u_compat1, u_compat2])
            db.flush()

            # 4. Collectors
            now_dt = datetime.datetime.now(datetime.timezone.utc)
            c1 = Collector(
                id="col-prod-core-01",
                tenant_id=t1.id,
                name="Primary Cluster Collector 01",
                hostname="k8s-node-worker-01.prod.internal",
                ip_address_pseudonym="node-hash-8f4b2c",
                version="1.4.2",
                status="online",
                auth_token_hash="secret-collector-token-01",
                collection_interval_seconds=5,
                last_seen_at=now_dt
            )
            c2 = Collector(
                id="col-prod-db-02",
                tenant_id=t1.id,
                name="Postgres Primary Gateway",
                hostname="db-pg-cluster-01.prod.internal",
                ip_address_pseudonym="node-hash-3a9d1e",
                version="1.4.2",
                status="online",
                auth_token_hash="secret-collector-token-02",
                collection_interval_seconds=5,
                last_seen_at=now_dt
            )
            c3 = Collector(
                id="col-edge-ingress-03",
                tenant_id=t1.id,
                name="Edge Envoy Router",
                hostname="gw-edge-ingress-03.prod.internal",
                ip_address_pseudonym="node-hash-5c2f7b",
                version="1.4.2",
                status="online",
                auth_token_hash="secret-collector-token-03",
                collection_interval_seconds=5,
                last_seen_at=now_dt
            )
            c4 = Collector(
                id="col-backup-agent-04",
                tenant_id=t1.id,
                name="Disaster Recovery Replica Agent",
                hostname="dr-standby-04.dr.internal",
                ip_address_pseudonym="node-hash-1e8c9a",
                version="1.4.1",
                status="offline",
                auth_token_hash="secret-collector-token-04",
                collection_interval_seconds=5,
                last_seen_at=now_dt - datetime.timedelta(minutes=45)
            )
            db.add_all([c1, c2, c3, c4])
            db.flush()

            # 5. Realistic Seed Incidents
            inc1 = Incident(
                id="44444444-4444-4444-4444-444444444441",
                incident_number="INC-2026-0042",
                tenant_id=t1.id,
                collector_id=c1.id,
                title="Worker Pool Memory Exhaustion & Cascading Latency",
                description="Correlated anomaly detected: Memory utilization climbed past 88% alongside a 140ms latency jump on API worker nodes.",
                severity="HIGH",
                status="OPEN",
                affected_components=json.dumps(["Worker-Pod-Cluster", "Connection-Pool-TCP", "Redis-Session-Store"]),
                contributing_signals=json.dumps(["Memory surge to 89.4%", "Latency increase to 215ms", "GC pause duration > 800ms"]),
                correlation_reason="Temporal coincidence within 90-second sliding window across same tenant worker node.",
                created_at=now_dt
            )
            inc2 = Incident(
                id="44444444-4444-4444-4444-444444444442",
                incident_number="INC-2026-0039",
                tenant_id=t1.id,
                collector_id=c3.id,
                title="Ingress Gateway Packet Drop & Authentication Burst",
                description="Edge router experienced 4.8% packet loss during a synchronized authentication retry storm from external banking gateway.",
                severity="CRITICAL",
                status="INVESTIGATING",
                affected_components=json.dumps(["Edge-Envoy-Proxy", "TLS-Terminator", "Auth-Rate-Limiter"]),
                contributing_signals=json.dumps(["Packet loss surge to 4.8%", "Failed auth rate reached 124/min", "CPU peak at 93.1%"]),
                correlation_reason="Security summary burst correlated directly with network ingress queue saturation.",
                created_at=now_dt - datetime.timedelta(minutes=15)
            )
            db.add_all([inc1, inc2])
            db.flush()

            # 6. AI Recommendations
            rec1 = AIRecommendation(
                id="55555555-5555-5555-5555-555555555551",
                incident_id=inc1.id,
                tenant_id=t1.id,
                detected_anomaly="Severe JVM / Worker Memory Saturation with Correlated Latency Degrade",
                contributing_signals=json.dumps(["Node memory 89.4%", "HTTP P95 latency 215ms (+180% above 75ms baseline)"]),
                baseline_comparison="Historical 7-day median memory is 54.2% (sigma = 4.1%). Current observation is +8.5 sigmas from baseline.",
                confidence_score=94.80,
                possible_root_cause="Unbounded connection leak or uncollected session token cache in ingress worker thread pool.",
                recommended_investigation="Review recent deployment commits on auth cache, inspect thread dump metadata without extracting payload bodies.",
                suggested_action="Safely trigger worker pod rolling drain and recycle idle connection pools.",
                suggested_action_type="ROLLING_RECYCLE_CONTAINERS",
                rollback_plan="Revert replica count to standby baseline; restore previous image hash if crash-loop occurs.",
                is_deterministic_fallback=True,
                created_at=now_dt
            )
            db.add(rec1)
            db.flush()

            # 7. Remediation Approvals
            app1 = RemediationApproval(
                id="66666666-6666-6666-6666-666666666661",
                recommendation_id=rec1.id,
                incident_id=inc1.id,
                tenant_id=t1.id,
                action_description="Perform staged graceful restart of 4 worker instances and flush expired memory caches.",
                target_component=f"Worker-Pod-Cluster ({c1.id})",
                policy_evaluation_result="POLICY_PASSED_REQUIRES_OPERATOR_SIGN_OFF",
                status="PENDING",
                rollback_information="Automated health check probes will instantly roll back to previous deployment state if 3 consecutive failures occur within 30s.",
                requested_at=now_dt
            )
            db.add(app1)
            db.flush()

            # 8. Performance Benchmarks
            bench = PerformanceBenchmark(
                id="77777777-7777-7777-7777-777777777771",
                tenant_id=t1.id,
                p50_latency_ms=12.4,
                p95_latency_ms=24.8,
                alert_generation_time_ms=45.2,
                heartbeat_age_seconds=5,
                queue_backlog_depth=0,
                delivery_success_pct=100.0,
                duplicate_count=0,
                lost_record_count=0
            )
            db.add(bench)
            db.flush()

            # 9. Initial telemetry time-series seed
            for i in range(15):
                t_step = now_dt - datetime.timedelta(seconds=(15 - i) * 10)
                p_id = f"seed-payload-{i:03d}"
                im = InfrastructureMetric(
                    payload_id=p_id,
                    collector_id=c1.id,
                    tenant_id=t1.id,
                    cpu_utilization_pct=42.0 + (i * 0.8),
                    memory_utilization_pct=52.0 + (i * 0.5),
                    disk_utilization_pct=61.2,
                    health_state="EXCELLENT" if i < 12 else "GOOD",
                    recorded_at=t_step
                )
                nm = NetworkMetric(
                    payload_id=p_id,
                    collector_id=c1.id,
                    tenant_id=t1.id,
                    latency_ms=14.0 + (i * 0.4),
                    packet_loss_pct=0.0,
                    recorded_at=t_step
                )
                db.add_all([im, nm])

            db.commit()
            print("[Database] Seed complete. Default login: admin@cynera.io / Cynera2026!Secure (admin@cicada.io also active)")
        else:
            # Ensure each CYNERA demo account exists independently in pre-existing DBs.
            org = db.query(Organization).first()
            tenant = db.query(Tenant).first()
            if org and tenant:
                demo_accounts = (
                    ("admin@cynera.io", "Alex Vance", "Super Administrator", "33333333-3333-3333-3333-333333333333"),
                    ("operator@cynera.io", "Sarah Chen", "Operator", "33333333-3333-3333-3333-333333333334"),
                )
                for email, full_name, role, user_id in demo_accounts:
                    existing_user = db.query(Profile).filter(Profile.email == email).first()
                    if not existing_user:
                        db.add(Profile(
                            id=user_id,
                            email=email,
                            password_hash=get_password_hash("Cynera2026!Secure"),
                            full_name=full_name,
                            role=role,
                            organization_id=org.id,
                            tenant_id=tenant.id,
                            is_verified=True,
                            is_active=True
                        ))
                db.commit()

        # Seed network devices if empty
        if db.query(NetworkDevice).count() == 0:
            tenant = db.query(Tenant).first()
            if tenant:
                nd1 = NetworkDevice(
                    tenant_id=tenant.id,
                    name="Localhost Security Gateway",
                    ip_address="127.0.0.1",
                    device_type="Server",
                    monitoring_methods=json.dumps(["ping", "tcp"]),
                    tcp_ports=json.dumps([8000, 3000]),
                    monitoring_interval_seconds=15,
                    is_active=True,
                    status="ONLINE",
                    last_latency_ms=0.5,
                    last_packet_loss_pct=0.0,
                    open_ports_summary=json.dumps([8000, 3000]),
                    last_checked_at=datetime.datetime.now(datetime.timezone.utc)
                )
                nd2 = NetworkDevice(
                    tenant_id=tenant.id,
                    name="Core Edge Router (US-East)",
                    ip_address="10.0.1.1",
                    device_type="Router",
                    monitoring_methods=json.dumps(["ping", "tcp", "snmp"]),
                    tcp_ports=json.dumps([80, 443]),
                    monitoring_interval_seconds=30,
                    is_active=True,
                    status="ONLINE",
                    last_latency_ms=1.2,
                    last_packet_loss_pct=0.0,
                    open_ports_summary=json.dumps([80, 443]),
                    last_checked_at=datetime.datetime.now(datetime.timezone.utc)
                )
                nd3 = NetworkDevice(
                    tenant_id=tenant.id,
                    name="Postgres DB Cluster Primary",
                    ip_address="10.0.1.25",
                    device_type="Server",
                    monitoring_methods=json.dumps(["ping", "tcp"]),
                    tcp_ports=json.dumps([5432, 22]),
                    monitoring_interval_seconds=30,
                    is_active=True,
                    status="ONLINE",
                    last_latency_ms=0.8,
                    last_packet_loss_pct=0.0,
                    open_ports_summary=json.dumps([5432]),
                    last_checked_at=datetime.datetime.now(datetime.timezone.utc)
                )
                nd4 = NetworkDevice(
                    tenant_id=tenant.id,
                    name="Perimeter Ingress Firewall",
                    ip_address="10.0.1.254",
                    device_type="Firewall",
                    monitoring_methods=json.dumps(["ping", "tcp", "snmp"]),
                    tcp_ports=json.dumps([443, 22]),
                    monitoring_interval_seconds=30,
                    is_active=True,
                    status="ONLINE",
                    last_latency_ms=1.6,
                    last_packet_loss_pct=0.0,
                    open_ports_summary=json.dumps([443]),
                    last_checked_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.add_all([nd1, nd2, nd3, nd4])
                db.commit()
                print("[Database] Seeded 4 default enterprise network devices.")

        # Ensure memberships exist for existing seeded profiles
        org = db.query(Organization).first()
        if org:
            admin_user = db.query(Profile).filter(Profile.email == "admin@cynera.io").first()
            if admin_user:
                existing_mem = db.query(OrganizationMembership).filter(
                    OrganizationMembership.organization_id == org.id,
                    OrganizationMembership.user_id == admin_user.id
                ).first()
                if not existing_mem:
                    db.add(OrganizationMembership(
                        organization_id=org.id,
                        user_id=admin_user.id,
                        role="Organization Owner"
                    ))
                    db.commit()

            # Seed default API key if empty
            if db.query(APIKey).filter(APIKey.organization_id == org.id).count() == 0:
                import hashlib
                raw_k = "cyn_live_default_demo_api_key_2026"
                db.add(APIKey(
                    organization_id=org.id,
                    name="Default Production Service Key",
                    key_prefix="cyn_live_demo...",
                    key_hash=hashlib.sha256(raw_k.encode()).hexdigest(),
                    permissions=json.dumps(["read", "write"])
                ))
                db.commit()

            # Seed default embed widget token if empty
            if db.query(EmbedWidgetToken).filter(EmbedWidgetToken.organization_id == org.id).count() == 0:
                db.add(EmbedWidgetToken(
                    organization_id=org.id,
                    name="Public Corporate Status Badge",
                    token="cyn_embed_public_live_token",
                    widget_type="health_status",
                    allowed_domains=json.dumps(["*"]),
                    theme="dark"
                ))
                db.commit()

            # Seed demo MonitoredWebsite if empty
            if db.query(MonitoredWebsite).filter(MonitoredWebsite.organization_id == org.id).count() == 0:
                demo_site = MonitoredWebsite(
                    id="web-demo-01",
                    organization_id=org.id,
                    name="Cynera Cloud Platform",
                    url="https://cynera.io",
                    status="ONLINE",
                    is_active=True,
                    is_verified=True,
                    verification_method="instant",
                    monitoring_interval_seconds=60,
                    timeout_seconds=10,
                    expected_status_codes="[200, 201, 301, 302]",
                    uptime_percentage_24h=99.98,
                    last_response_time_ms=78.5,
                    last_status_code=200,
                    ssl_status="VALID",
                    ssl_issuer="Let's Encrypt Authority X3",
                    ssl_days_remaining=74,
                    dns_status="HEALTHY",
                    dns_lookup_time_ms=18.2,
                    dns_resolved_ips='["104.21.55.2", "172.67.180.11"]',
                    last_checked_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.add(demo_site)
                db.commit()

            # Seed demo Alert if empty
            if db.query(Alert).filter(Alert.organization_id == org.id).count() == 0:
                db.add(Alert(
                    id="alt-demo-01",
                    organization_id=org.id,
                    title="Network Latency Anomaly Detected",
                    severity="HIGH",
                    category="network",
                    resource_name="dev-core-router-01",
                    resource_id="dev-core-router-01",
                    evidence="Round-trip time on core router 192.168.1.1 spiked to 142ms (+240% above baseline).",
                    status="ACTIVE"
                ))
                db.commit()

            # Seed demo APM ApplicationService if empty
            if db.query(ApplicationService).filter(ApplicationService.organization_id == org.id).count() == 0:
                db.add(ApplicationService(
                    id="svc-demo-01",
                    organization_id=org.id,
                    name="cynera-backend-api",
                    environment="production",
                    language="Python",
                    version="1.0.0",
                    status="HEALTHY",
                    error_rate_pct=0.12,
                    request_count_24h=2400,
                    avg_latency_ms=45.2,
                    last_heartbeat_at=datetime.datetime.now(datetime.timezone.utc)
                ))
                db.commit()

            # Seed demo DatabaseIntegration if empty
            if db.query(DatabaseIntegration).filter(DatabaseIntegration.organization_id == org.id).count() == 0:
                db.add(DatabaseIntegration(
                    id="db-demo-01",
                    organization_id=org.id,
                    name="Primary Production PostgreSQL",
                    db_type="PostgreSQL",
                    host="pg-cluster.internal",
                    port=5432,
                    database_name="cynera_prod",
                    username_masked="cynera_ro",
                    status="HEALTHY",
                    pool_saturation_pct=24.5,
                    active_connections=18,
                    max_connections=100,
                    avg_query_latency_ms=8.4,
                    slow_queries_count=2,
                    last_checked_at=datetime.datetime.now(datetime.timezone.utc)
                ))
                db.commit()
    finally:
        db.close()

def seed_demo_workspace_data():
    """Create repeatable, clearly synthetic records for every major demo workflow."""
    if not settings.DEMO_MODE:
        return
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "acroglobal").first()
        tenant = db.query(Tenant).filter(Tenant.slug == "na-prod-useast").first()
        if not org or not tenant:
            return

        personas = [
            ("owner@cynera.io", "Morgan Lee", "Organization Owner"),
        ]
        for email, full_name, role in personas:
            user = db.query(Profile).filter(Profile.email == email).first()
            if not user:
                user = Profile(
                    email=email,
                    password_hash=get_password_hash("Cynera2026!Secure"),
                    full_name=full_name,
                    role=role,
                    organization_id=org.id,
                    tenant_id=tenant.id,
                    is_verified=True,
                    is_active=True
                )
                db.add(user)
                db.flush()
            membership = db.query(OrganizationMembership).filter(
                OrganizationMembership.organization_id == org.id,
                OrganizationMembership.user_id == user.id
            ).first()
            if not membership:
                db.add(OrganizationMembership(
                    organization_id=org.id,
                    user_id=user.id,
                    role=role if role != "Super Administrator" else "Organization Owner",
                    is_active=True
                ))

        db.flush()
        now = datetime.datetime.now(datetime.timezone.utc)
        c1 = db.query(Collector).filter(Collector.tenant_id == tenant.id).first()
        if not c1:
            return

        # Alert Center: deliberately include active, acknowledged and resolved cases.
        if db.query(Alert).filter(Alert.organization_id == org.id).count() < 3:
            for suffix, title, severity, category, status_value, evidence in [
                ("demo-warn", "DEMO: API latency above warning threshold", "MEDIUM", "application", "ACTIVE", "Synthetic latency is 135ms; demo warning case."),
                ("demo-crit", "DEMO: Database connection pool near exhaustion", "CRITICAL", "database", "ACTIVE", "Synthetic pool saturation is 97%; demo critical case."),
                ("demo-res", "DEMO: Network packet loss recovered", "LOW", "network", "RESOLVED", "Synthetic packet loss returned to baseline; demo resolved case.")
            ]:
                if not db.query(Alert).filter(Alert.id == suffix).first():
                    db.add(Alert(
                        id=suffix, organization_id=org.id, title=title,
                        severity=severity, category=category,
                        resource_name="demo-service", resource_id="demo-service",
                        evidence=evidence, status=status_value,
                        resolved_at=now if status_value == "RESOLVED" else None
                    ))

        # AIOps and incident workflows: add synthetic records only when absent.
        demo_incident_id = "demo-incident-warning-001"
        incident = db.query(Incident).filter(Incident.id == demo_incident_id).first()
        if not incident:
            incident = Incident(
                id=demo_incident_id,
                incident_number="DEMO-INC-2026-001",
                tenant_id=tenant.id,
                collector_id=c1.id,
                title="DEMO: Elevated API latency and memory pressure",
                description="Synthetic demonstration incident; no production system was affected.",
                severity="HIGH",
                status="INVESTIGATING",
                affected_components=json.dumps(["demo-api", "demo-worker"]),
                contributing_signals=json.dumps(["CPU 91%", "Memory 88%", "Latency 135ms"]),
                correlation_reason="Demo signals grouped in the same correlation window.",
                created_at=now - datetime.timedelta(minutes=8)
            )
            db.add(incident)
            db.flush()
            db.add(AIRecommendation(
                incident_id=incident.id,
                tenant_id=tenant.id,
                detected_anomaly="DEMO: Compound resource pressure",
                contributing_signals=json.dumps(["CPU 91%", "Memory 88%", "Latency 135ms"]),
                baseline_comparison="Synthetic demo baseline: CPU 42%, memory 55%, latency 25ms.",
                confidence_score=91.0,
                possible_root_cause="Synthetic worker saturation used for demonstration.",
                recommended_investigation="Inspect demo worker utilization and recent deployment changes.",
                suggested_action="Simulate a staged worker recycle after operator approval.",
                suggested_action_type="SIMULATED_WORKER_RECYCLE",
                rollback_plan="Restore the demo worker state if the simulated health check fails.",
                is_deterministic_fallback=True
            ))
        if db.query(IncidentAlert).filter(IncidentAlert.tenant_id == tenant.id, IncidentAlert.message.like("DEMO:%")).count() == 0:
            db.add_all([
                IncidentAlert(tenant_id=tenant.id, collector_id=c1.id, alert_type="CPU_THRESHOLD", severity="HIGH", metric_name="cpu_utilization_pct", metric_value=91.0, threshold_value=85.0, message="DEMO: CPU usage reached 91% on the sample worker.", incident_id=demo_incident_id),
                IncidentAlert(tenant_id=tenant.id, collector_id=c1.id, alert_type="MEMORY_THRESHOLD", severity="MEDIUM", metric_name="memory_utilization_pct", metric_value=88.0, threshold_value=80.0, message="DEMO: Memory usage reached 88% on the sample worker.", incident_id=demo_incident_id)
            ])

        # Security Center and egress proof examples.
        if db.query(SecuritySummary).filter(SecuritySummary.payload_id == "demo-security-payload-001").first() is None:
            db.add(SecuritySummary(
                payload_id="demo-security-payload-001", collector_id=c1.id, tenant_id=tenant.id,
                failed_login_count=18, suspicious_activity_score=82.0,
                security_event_severity="HIGH", authentication_failure_rate_per_min=18.0,
                pseudonymous_source_cluster="demo-cluster-a", redacted_tokens_detected=3,
                summary_description="DEMO: Synthetic repeated authentication failures; no real user IPs or credentials."
            ))
        if db.query(EgressMetadata).filter(EgressMetadata.payload_id == "demo-egress-payload-001").first() is None:
            db.add(EgressMetadata(
                payload_id="demo-egress-payload-001", collector_id=c1.id, tenant_id=tenant.id,
                payload_hash_sha256="a" * 64, bytes_transmitted=1240,
                redacted_fields_count=3, redacted_field_types=json.dumps(["email", "token", "password"]),
                rejected_keys=json.dumps(["raw_log", "authorization_header"]),
                allowlist_validated=True, raw_payload_preview_hash="b" * 64,
                local_raw_preview=json.dumps({"note": "DEMO synthetic masked preview"}),
                outgoing_payload_json=json.dumps({"cpu": 91.0, "memory": 88.0, "demo": True}),
                destination_endpoint="/api/telemetry/ingest", transmission_status="DELIVERED",
                latency_transit_ms=24.0, sent_at=now, delivered_at=now
            ))

        # Seed a demonstration report and notifications so their list/detail buttons have content.
        if db.query(ReportRecord).filter(ReportRecord.organization_id == org.id, ReportRecord.title == "DEMO - Weekly Observability Report").first() is None:
            db.add(ReportRecord(
                organization_id=org.id,
                title="DEMO - Weekly Observability Report",
                report_type="executive_summary",
                time_range="last_7_days",
                summary_json=json.dumps({
                    "demo_data": True,
                    "executive_summary": "Synthetic sample report for demonstrating report generation and PDF download.",
                    "telemetry_stats": {"average_cpu_pct": 52.4, "average_memory_pct": 61.2, "sla_availability_pct": 99.2},
                    "incident_stats": {"total_detected": 3, "total_resolved": 2, "mttr_minutes": 12.0},
                    "privacy_and_security": {"zero_trust_compliance": "DEMO", "raw_log_egress_prevention": "DEMO ONLY"}
                })
            ))
        for title, message, kind in [
            ("DEMO: Warning notification", "Sample warning: API latency is above its configured threshold.", "warning"),
            ("DEMO: Critical notification", "Sample critical event: database pool saturation reached 97%.", "critical"),
            ("DEMO: Recovery notification", "Sample recovery: network packet loss returned to normal.", "success")
        ]:
            if db.query(Notification).filter(Notification.organization_id == org.id, Notification.title == title).first() is None:
                db.add(Notification(organization_id=org.id, title=title, message=message, type=kind))

        # Ensure every published demo persona is active and verified, then provide a
        # shared synthetic workspace with healthy, warning, critical, failed and recovered states.
        all_demo_personas = [
            ("admin@cynera.io", "Alex Vance", "Super Administrator"),
            ("owner@cynera.io", "Morgan Lee", "Organization Owner"),
        ]
        for email, full_name, role in all_demo_personas:
            user = db.query(Profile).filter(Profile.email == email).first()
            if not user:
                user = Profile(
                    email=email, password_hash=get_password_hash("Cynera2026!Secure"),
                    full_name=full_name, role=role, organization_id=org.id,
                    tenant_id=tenant.id, is_verified=True, is_active=True
                )
                db.add(user)
                db.flush()
            else:
                user.is_verified = True
                user.is_active = True
                user.organization_id = user.organization_id or org.id
                user.tenant_id = user.tenant_id or tenant.id
            membership = db.query(OrganizationMembership).filter(
                OrganizationMembership.organization_id == org.id,
                OrganizationMembership.user_id == user.id
            ).first()
            if not membership:
                db.add(OrganizationMembership(
                    organization_id=org.id, user_id=user.id, role=role, is_active=True
                ))

        # Retire legacy demo personas so only the two requested accounts remain usable.
        retired_demo_emails = [
            "workspace-admin@cynera.io", "security@cynera.io",
            "infra@cynera.io", "operator@cynera.io", "viewer@cynera.io"
        ]
        db.query(Profile).filter(Profile.email.in_(retired_demo_emails)).update(
            {Profile.is_active: False}, synchronize_session=False
        )

        db.flush()

        # Alert Center: include all severity levels and lifecycle states across every demo login.
        alert_fixtures = [
            ("demo-alert-infra-warning", "DEMO: CPU utilization warning", "MEDIUM", "infrastructure", "ACTIVE", "Synthetic CPU 86%; warning threshold 80%."),
            ("demo-alert-infra-critical", "DEMO: Memory saturation critical", "CRITICAL", "infrastructure", "ACTIVE", "Synthetic memory 96%; critical threshold 90%."),
            ("demo-alert-disk-high", "DEMO: Disk capacity high", "HIGH", "infrastructure", "ACKNOWLEDGED", "Synthetic disk utilization 92%; operator acknowledgement example."),
            ("demo-alert-network-down", "DEMO: Network path unreachable", "CRITICAL", "network", "ACTIVE", "Synthetic network probe failed; no real network request was made."),
            ("demo-alert-network-recovered", "DEMO: Packet loss recovered", "LOW", "network", "RESOLVED", "Synthetic packet loss returned to 0.01%; recovery example."),
            ("demo-alert-security-critical", "DEMO: Authentication attack pattern", "CRITICAL", "security", "ACTIVE", "Synthetic 65 failed logins/minute; no real credentials were used."),
            ("demo-alert-app-degraded", "DEMO: Application error rate elevated", "HIGH", "application", "ACTIVE", "Synthetic application error rate 8.4%; warning and degradation example."),
            ("demo-alert-db-critical", "DEMO: Database pool saturation", "CRITICAL", "database", "ACTIVE", "Synthetic database pool saturation 97%; no real database connection was made."),
            ("demo-alert-website-warning", "DEMO: Website TLS certificate expiring", "MEDIUM", "website", "ACKNOWLEDGED", "Synthetic certificate expiry in 9 days."),
            ("demo-alert-website-failed", "DEMO: Website DNS resolution failure", "HIGH", "website", "ACTIVE", "Synthetic DNS failure example; no public DNS query was issued."),
        ]
        for alert_id, title, severity, category, state, evidence in alert_fixtures:
            if not db.query(Alert).filter(Alert.id == alert_id).first():
                db.add(Alert(
                    id=alert_id, organization_id=org.id, title=title, severity=severity,
                    category=category, resource_name="DEMO synthetic resource",
                    resource_id=alert_id, evidence=evidence, status=state,
                    resolved_at=now if state == "RESOLVED" else None
                ))

        # Website monitoring: healthy, slow, down, timeout, DNS and TLS failure examples.
        website_fixtures = [
            ("demo-web-healthy", "DEMO - Healthy status portal", "ONLINE", 200, 72.0, 99.99, "VALID", 180, "HEALTHY", 18.0),
            ("demo-web-slow", "DEMO - Slow response portal", "DEGRADED", 200, 1850.0, 97.40, "WARNING", 9, "DEGRADED", 145.0),
            ("demo-web-down", "DEMO - Unavailable payment portal", "DOWN", 503, 5000.0, 91.20, "VALID", 45, "HEALTHY", 20.0),
            ("demo-web-timeout", "DEMO - Timeout portal", "TIMEOUT", None, 10000.0, 94.00, "VALID", 35, "HEALTHY", 22.0),
            ("demo-web-dns", "DEMO - DNS failure portal", "DNS_FAILURE", None, 0.0, 88.00, "UNKNOWN", None, "FAILED", 0.0),
            ("demo-web-tls", "DEMO - Expired TLS portal", "TLS_FAILURE", 200, 220.0, 96.00, "EXPIRED", 0, "HEALTHY", 19.0),
        ]
        for wid, name, state, code, latency, uptime, ssl, days, dns, dns_ms in website_fixtures:
            website = db.query(MonitoredWebsite).filter(MonitoredWebsite.id == wid).first()
            if not website:
                website = MonitoredWebsite(
                    id=wid, organization_id=org.id, name=name,
                    url=f"https://{wid}.demo.invalid", status=state, is_active=True,
                    is_verified=True, verification_method="manual",
                    monitoring_interval_seconds=60, timeout_seconds=10,
                    expected_status_codes="[200, 201, 301, 302]",
                    last_checked_at=now, last_status_code=code,
                    last_response_time_ms=latency, uptime_percentage_24h=uptime,
                    ssl_status=ssl, ssl_days_remaining=days, dns_status=dns,
                    dns_lookup_time_ms=dns_ms, dns_resolved_ips="[]"
                )
                db.add(website)
                db.flush()
            result_id = f"{wid}-check"
            if not db.query(WebsiteCheckResult).filter(WebsiteCheckResult.id == result_id).first():
                db.add(WebsiteCheckResult(
                    id=result_id, website_id=website.id, organization_id=org.id,
                    status=state, status_code=code, response_time_ms=latency,
                    dns_lookup_time_ms=dns_ms, ssl_valid=(ssl == "VALID"),
                    ssl_days_remaining=days,
                    error_message=None if state == "ONLINE" else f"DEMO synthetic {state} condition",
                    check_location="CYNERA Demo Lab", recorded_at=now
                ))

        # APM: healthy, degraded and critical services plus warning/error events.
        apm_fixtures = [
            ("demo-apm-healthy", "DEMO - Healthy authentication API", "HEALTHY", 0.12, 42.0, 24000),
            ("demo-apm-degraded", "DEMO - Slow checkout API", "DEGRADED", 4.8, 680.0, 18200),
            ("demo-apm-critical", "DEMO - Failing payment worker", "CRITICAL", 18.6, 2400.0, 9200),
        ]
        for sid, name, state, errors, latency, requests in apm_fixtures:
            service = db.query(ApplicationService).filter(ApplicationService.id == sid).first()
            if not service:
                service = ApplicationService(
                    id=sid, organization_id=org.id, name=name, language="Python",
                    environment="demo", version="2.4.0", status=state,
                    error_rate_pct=errors, avg_latency_ms=latency,
                    request_count_24h=requests, last_heartbeat_at=now
                )
                db.add(service)
                db.flush()
            event_id = f"{sid}-event"
            if state != "HEALTHY" and not db.query(ApplicationEvent).filter(ApplicationEvent.id == event_id).first():
                db.add(ApplicationEvent(
                    id=event_id, service_id=service.id, organization_id=org.id,
                    event_type="warning" if state == "DEGRADED" else "exception",
                    name="DEMO synthetic application event",
                    message=f"Synthetic {state.lower()} service case; no real customer request was processed.",
                    endpoint="/api/demo/checkout", duration_ms=latency,
                    status_code=200 if state == "DEGRADED" else 503, recorded_at=now
                ))

        # Database monitoring: healthy, warning/saturation and unavailable integration states.
        db_fixtures = [
            ("demo-db-healthy", "DEMO - Healthy PostgreSQL", "HEALTHY", 18, 100, 18.0, 8.4, 2),
            ("demo-db-warning", "DEMO - PostgreSQL pool warning", "DEGRADED", 82, 100, 82.0, 185.0, 42),
            ("demo-db-critical", "DEMO - MySQL pool exhausted", "OFFLINE", 100, 100, 100.0, 2500.0, 180),
        ]
        for did, name, state, active, maximum, saturation, latency, slow in db_fixtures:
            integration = db.query(DatabaseIntegration).filter(DatabaseIntegration.id == did).first()
            if not integration:
                integration = DatabaseIntegration(
                    id=did, organization_id=org.id, name=name,
                    db_type="PostgreSQL" if "PostgreSQL" in name else "MySQL",
                    host="demo.invalid", port=5432 if "PostgreSQL" in name else 3306,
                    database_name="cynera_demo", username_masked="demo_readonly",
                    status=state, active_connections=active, max_connections=maximum,
                    pool_saturation_pct=saturation, avg_query_latency_ms=latency,
                    slow_queries_count=slow, last_checked_at=now
                )
                db.add(integration)
                db.flush()

        # Network monitoring: online, degraded, unreachable and offline devices.
        network_fixtures = [
            ("demo-net-online", "DEMO - Core router online", "ONLINE", 12.0, 0.0),
            ("demo-net-degraded", "DEMO - High-latency edge router", "DEGRADED", 310.0, 3.2),
            ("demo-net-unreachable", "DEMO - Unreachable gateway", "UNREACHABLE", 5000.0, 100.0),
            ("demo-net-offline", "DEMO - Offline backup switch", "OFFLINE", 0.0, 100.0),
        ]
        for nid, name, state, latency, loss in network_fixtures:
            if not db.query(NetworkDevice).filter(NetworkDevice.id == nid).first():
                db.add(NetworkDevice(
                    id=nid, tenant_id=tenant.id, name=name,
                    ip_address="demo.invalid", device_type="Router",
                    monitoring_methods=json.dumps(["synthetic"]),
                    tcp_ports="[]", monitoring_interval_seconds=60,
                    is_active=True, status=state, last_latency_ms=latency,
                    last_packet_loss_pct=loss, open_ports_summary="[]",
                    last_checked_at=now
                ))

        db.commit()
        # Populate both healthy and degraded telemetry history for dashboard charts.
        if db.query(InfrastructureMetric).filter(InfrastructureMetric.payload_id.like("demo-series-%")).count() == 0:
            for i in range(20):
                healthy = i < 12
                payload_id = f"demo-series-{i:03d}"
                stamp = now - datetime.timedelta(minutes=(20 - i) * 3)
                db.add(InfrastructureMetric(
                    payload_id=payload_id, collector_id=c1.id, tenant_id=tenant.id,
                    cpu_utilization_pct=42.0 + i * 0.8 if healthy else 88.0 + (i % 4) * 2.0,
                    memory_utilization_pct=54.0 + i * 0.5 if healthy else 86.0 + (i % 5) * 2.0,
                    disk_utilization_pct=61.0 if healthy else 91.0 + (i % 3) * 2.0,
                    health_state="EXCELLENT" if i < 8 else "GOOD" if healthy else "POOR",
                    recorded_at=stamp
                ))
                db.add(NetworkMetric(
                    payload_id=payload_id, collector_id=c1.id, tenant_id=tenant.id,
                    latency_ms=18.0 + i * 1.2 if healthy else 180.0 + i * 35.0,
                    packet_loss_pct=0.0 if healthy else 2.5 + (i % 4) * 1.2,
                    recorded_at=stamp
                ))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY must be configured before starting CYNERA.")

    # Vercel runs this FastAPI app as short-lived serverless functions.
    # Do not launch process-lifetime schedulers or run schema/demo seeding in
    # every serverless instance; both create unnecessary concurrent DB traffic.
    is_vercel = os.getenv("VERCEL", "").lower() in {"1", "true"}

    if is_vercel:
        print(
            "[Lifespan] Vercel serverless runtime detected: automatic database/demo "
            "seeding and the continuous website scheduler are disabled. "
            "Use Supabase migrations for schema setup and request-triggered checks "
            "for website monitoring."
        )
    else:
        seed_database_if_empty()
        seed_demo_workspace_data()
        if settings.DEMO_MODE:
            try:
                from .services.demo_seeder import seed_demo_accounts_and_data
                active_session = getattr(db_module, 'SessionLocal', SessionLocal)
                if active_session:
                    with active_session() as s:
                        seed_demo_accounts_and_data(s)
            except Exception as e:
                print(f"[Lifespan] Demo seeder warning: {e}")
        website_scheduler.start()

    try:
        yield
    finally:
        if not is_vercel:
            website_scheduler.stop()

app = FastAPI(
    title="CYNERA — Cyber Network Evaluation and Risk Analytics",
    description="AI-Powered Secure Infrastructure Observability Platform",
    version="1.4.2",
    lifespan=lifespan
)

# Basic service discovery endpoints (also used by deployment health checks).
@app.get("/", tags=["Health"])
def root_health():
    return {
        "service": "CYNERA API",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def api_health():
    database = test_database_connection()
    if not database.get("connected"):
        return JSONResponse(
            status_code=503,
            content={
                "service": "CYNERA API",
                "status": "degraded",
                "database": database.get("status", "unavailable"),
                "version": app.version
            }
        )
    return {
        "service": "CYNERA API",
        "status": "healthy",
        "database": "connected",
        "version": app.version
    }


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def cynera_security_rate_limit_middleware(request: Request, call_next):
    """
    Applies sliding-window rate limiting per IP address and endpoint sensitivity.
    Allows high throughput for telemetry while protecting auth and sensitive endpoints.
    """
    if request.method == "OPTIONS" or request.url.path in ("/api/health", "/"):
        return await call_next(request)

    client_ip = rate_limiter.get_client_ip(request)
    path = request.url.path

    if any(auth_path in path for auth_path in ("/api/auth/login", "/api/auth/register", "/api/auth/verify-otp", "/api/auth/demo-login", "/api/auth/resend-otp", "/api/auth/forgot-password")):
        allowed, remaining, retry_after = rate_limiter.check_rate_limit(f"auth:{client_ip}:{path}", max_requests=30, window_seconds=60)
    else:
        allowed, remaining, retry_after = rate_limiter.check_rate_limit(f"ip:{client_ip}", max_requests=240, window_seconds=60)

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "CYNERA Security: Rate limit exceeded. Please back off and retry shortly.",
                "retry_after_seconds": retry_after
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Remaining": "0"
            }
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response

# Register Routers
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(collectors_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(egress_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(network_router, prefix="/api")
app.include_router(organization_router, prefix="/api")
app.include_router(developer_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(websites_router, prefix="/api")
app.include_router(apm_router, prefix="/api")
app.include_router(databases_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")

# WebSocket Endpoint. The first client message must authenticate the connection.
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    db = None
    registered = False
    try:
        try:
            auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=8)
        except Exception:
            await websocket.close(code=4401, reason="Authentication required")
            return

        token = auth_message.get("token") if isinstance(auth_message, dict) and auth_message.get("type") == "AUTH" else None
        claims = decode_access_token(token) if isinstance(token, str) and token else None
        subject = claims.get("sub") if claims else None
        if not subject or not SessionLocal:
            await websocket.close(code=4401, reason="Invalid or expired session")
            return

        db = SessionLocal()
        current_user = db.query(Profile).filter(Profile.id == str(subject)).first()
        if (
            not current_user
            or not current_user.is_active
            or not current_user.is_verified
            or not current_user.tenant_id
        ):
            await websocket.close(code=4403, reason="Active tenant membership required")
            return

        await ws_manager.register(
            websocket,
            tenant_id=current_user.tenant_id,
            organization_id=current_user.organization_id
        )
        registered = True
        await websocket.send_json({"type": "AUTHENTICATED"})

        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"type": "PONG", "payload": data}))
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close(code=1011, reason="WebSocket session failed")
        except Exception:
            pass
    finally:
        if registered:
            ws_manager.disconnect(websocket)
        if db is not None:
            db.close()

