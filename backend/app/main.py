import os
import json
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base, SessionLocal
from .models.models import (
    Organization, Tenant, Profile, Collector, Incident,
    IncidentAlert, AIRecommendation, RemediationApproval, PerformanceBenchmark,
    InfrastructureMetric, NetworkMetric, SecuritySummary
)
from .auth.jwt import get_password_hash
from .websocket.manager import ws_manager

# API Routers
from .api.auth import router as auth_router
from .api.collectors import router as collectors_router
from .api.telemetry import router as telemetry_router
from .api.metrics import router as metrics_router
from .api.incidents import router as incidents_router
from .api.egress import router as egress_router
from .api.approvals import router as approvals_router
from .api.scenarios import router as operations_router
from .api.settings import router as settings_router

def seed_database_if_empty():
    """Initializes tables and populates with realistic enterprise seed data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
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
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database_if_empty()
    yield

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

# Register Routers
app.include_router(auth_router, prefix="/api")
app.include_router(collectors_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(egress_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

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

