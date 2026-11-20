import os
import json
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from . import database as db_module
from .database import engine, Base, SessionLocal
from .models.models import (
    Organization, Tenant, Profile, Collector, Incident,
    IncidentAlert, AIRecommendation, RemediationApproval, PerformanceBenchmark,
    InfrastructureMetric, NetworkMetric, SecuritySummary,
    NetworkDevice, NetworkCheckResult, OrganizationMembership,
    APIKey, EmbedWidgetToken, Notification
)
from .auth.jwt import get_password_hash
from .websocket.manager import ws_manager

# API Routers
from .api.auth import router as auth_router
from .api.admin import router as admin_router
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
    """Seeds demo fixtures only in explicit development/test environments."""
    runtime_env = (settings.APP_ENV or settings.ENVIRONMENT or "production").strip().lower()
    if runtime_env not in {"development", "dev", "test", "testing"}:
        print("[Database] Demo seeding disabled outside development/test environments.")
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
            # Ensure CYNERA default users exist in pre-existing DB
            cynera_admin = db.query(Profile).filter(Profile.email == "admin@cynera.io").first()
            if not cynera_admin:
                org = db.query(Organization).first()
                tenant = db.query(Tenant).first()
                if org and tenant:
                    pw_hash_cynera = get_password_hash("Cynera2026!Secure")
                    u_cynera1 = Profile(
                        id="33333333-3333-3333-3333-333333333333",
                        email="admin@cynera.io",
                        password_hash=pw_hash_cynera,
                        full_name="Alex Vance",
                        role="Super Administrator",
                        organization_id=org.id,
                        tenant_id=tenant.id
                    )
                    u_cynera2 = Profile(
                        id="33333333-3333-3333-3333-333333333334",
                        email="operator@cynera.io",
                        password_hash=pw_hash_cynera,
                        full_name="Sarah Chen",
                        role="Operator",
                        organization_id=org.id,
                        tenant_id=tenant.id
                    )
                    db.add_all([u_cynera1, u_cynera2])
                    db.commit()
                    print("[Database] CYNERA credentials provisioned: admin@cynera.io / Cynera2026!Secure")

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database_if_empty()
    website_scheduler.start()
    yield
    website_scheduler.stop()

app = FastAPI(
    title="CYNERA — Cyber Network Evaluation and Risk Analytics",
    description="AI-Powered Secure Infrastructure Observability Platform",
    version="1.4.2",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
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

    if any(auth_path in path for auth_path in ("/api/auth/login", "/api/auth/register", "/api/auth/verify-otp")):
        allowed, remaining, retry_after = rate_limiter.check_rate_limit(f"auth:{client_ip}", max_requests=30, window_seconds=60)
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

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process client ping
            await websocket.send_text(json.dumps({"type": "PONG", "payload": data}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

