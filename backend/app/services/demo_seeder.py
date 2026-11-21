import datetime
import json
import logging
from sqlalchemy.orm import Session
from ..models.models import (
    Organization, Tenant, Profile, OrganizationMembership,
    Collector, InfrastructureMetric, NetworkDevice, MonitoredWebsite,
    ApplicationService, DatabaseIntegration, Alert, Incident,
    ReportRecord, Notification, SecuritySummary, utc_now
)
from ..auth.jwt import get_password_hash

logger = logging.getLogger("cynera.demo_seeder")

DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"
DEMO_TENANT_ID = "11111111-1111-1111-1111-111111111111"
ADMIN_USER_ID = "33333333-3333-3333-3333-333333333333"
OWNER_USER_ID = "33333333-3333-3333-3333-333333333335"

def seed_demo_accounts_and_data(db: Session):
    """
    Idempotent seeder that establishes the two official CYNERA demo accounts:
    1. Platform Administrator: admin@cynera.io / Cynera2026!Secure (Super Administrator)
    2. Workspace Account: owner@cynera.io / Cynera2026!Secure (Organization Owner)
    Deactivates any legacy demo personas and ensures comprehensive healthy + failure
    dashboard records in all observability modules.
    """
    now = utc_now()
    pw_hash = get_password_hash("Cynera2026!Secure")

    # 1. Ensure Default Enterprise Organization & Tenant
    org = db.query(Organization).filter(Organization.id == DEMO_ORG_ID).first()
    if not org:
        org = Organization(
            id=DEMO_ORG_ID,
            name="AcroGlobal Financial",
            slug="acroglobal",
            plan="enterprise",
            industry="Financial Technology",
            org_size="50-250",
            country="Global"
        )
        db.add(org)
        db.flush()

    tenant = db.query(Tenant).filter(Tenant.id == DEMO_TENANT_ID).first()
    if not tenant:
        tenant = Tenant(
            id=DEMO_TENANT_ID,
            organization_id=org.id,
            name="North America Production (US-East)",
            slug="na-prod-useast",
            region="us-east-1"
        )
        db.add(tenant)
        db.flush()

    # 2. Deactivate other demo personas
    disabled_emails = [
        "operator@cynera.io", "admin@cicada.io", "operator@cicada.io",
        "analyst@cynera.io", "viewer@cynera.io", "infra@cynera.io",
        "demo-user@cynera.io", "guest@cynera.io"
    ]
    db.query(Profile).filter(Profile.email.in_(disabled_emails)).update(
        {"is_active": False}, synchronize_session=False
    )

    # 3. Provision / Update the TWO Official Active Demo Accounts
    # 3a. Platform Administrator (Super Administrator)
    admin_user = db.query(Profile).filter(Profile.email == "admin@cynera.io").first()
    if not admin_user:
        admin_user = Profile(
            id=ADMIN_USER_ID,
            email="admin@cynera.io",
            password_hash=pw_hash,
            full_name="Platform Administrator",
            role="Super Administrator",
            organization_id=org.id,
            tenant_id=tenant.id,
            is_verified=True,
            is_active=True
        )
        db.add(admin_user)
        db.flush()
    else:
        admin_user.password_hash = pw_hash
        admin_user.role = "Super Administrator"
        admin_user.is_verified = True
        admin_user.is_active = True
        if not admin_user.organization_id:
            admin_user.organization_id = org.id
        if not admin_user.tenant_id:
            admin_user.tenant_id = tenant.id

    # 3b. Workspace Account (Organization Owner)
    owner_user = db.query(Profile).filter(Profile.email == "owner@cynera.io").first()
    if not owner_user:
        owner_user = Profile(
            id=OWNER_USER_ID,
            email="owner@cynera.io",
            password_hash=pw_hash,
            full_name="Workspace Owner",
            role="Organization Owner",
            organization_id=org.id,
            tenant_id=tenant.id,
            is_verified=True,
            is_active=True
        )
        db.add(owner_user)
        db.flush()
    else:
        owner_user.password_hash = pw_hash
        owner_user.role = "Organization Owner"
        owner_user.is_verified = True
        owner_user.is_active = True
        owner_user.organization_id = org.id
        owner_user.tenant_id = tenant.id

    # Ensure OrganizationMemberships exist
    for user_obj, target_role in [(admin_user, "Super Administrator"), (owner_user, "Organization Owner")]:
        mem = db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id == org.id,
            OrganizationMembership.user_id == user_obj.id
        ).first()
        if not mem:
            db.add(OrganizationMembership(
                organization_id=org.id,
                user_id=user_obj.id,
                role=target_role
            ))
        else:
            mem.role = target_role

    db.commit()

    # 4. Collectors: Online and Offline Examples
    c_online = db.query(Collector).filter(Collector.id == "col-prod-core-01").first()
    if not c_online:
        c_online = Collector(
            id="col-prod-core-01",
            tenant_id=tenant.id,
            name="[DEMO] Primary Cluster Edge Collector",
            hostname="k8s-node-worker-01.prod.internal",
            ip_address_pseudonym="node-hash-8f4b2c",
            version="1.4.2",
            status="online",
            auth_token_hash="secret-collector-token-01",
            collection_interval_seconds=5,
            last_seen_at=now
        )
        db.add(c_online)
    else:
        c_online.name = "[DEMO] Primary Cluster Edge Collector"
        c_online.status = "online"
        c_online.last_seen_at = now

    c_offline = db.query(Collector).filter(Collector.id == "col-edge-ingress-03").first()
    if not c_offline:
        c_offline = Collector(
            id="col-edge-ingress-03",
            tenant_id=tenant.id,
            name="[DEMO] Remote DMZ Ingress Collector (Stale)",
            hostname="dmz-edge-collector.sec.internal",
            ip_address_pseudonym="node-hash-dmz-03",
            version="1.3.8",
            status="offline",
            auth_token_hash="secret-collector-token-03",
            collection_interval_seconds=15,
            last_seen_at=now - datetime.timedelta(hours=3)
        )
        db.add(c_offline)
    else:
        c_offline.name = "[DEMO] Remote DMZ Ingress Collector (Stale)"
        c_offline.status = "offline"
        c_offline.last_seen_at = now - datetime.timedelta(hours=3)

    db.commit()

    # 5. Infrastructure: Healthy and Critical CPU/Memory
    if db.query(InfrastructureMetric).filter(InfrastructureMetric.collector_id == "col-prod-core-01").count() == 0:
        for i in range(10):
            t_step = now - datetime.timedelta(seconds=(10 - i) * 15)
            # Healthy sample
            im_healthy = InfrastructureMetric(
                payload_id=f"demo-infra-healthy-{i:03d}",
                collector_id="col-prod-core-01",
                tenant_id=tenant.id,
                cpu_utilization_pct=22.5 + (i * 0.4),
                memory_utilization_pct=46.0 + (i * 0.3),
                memory_used_mb=7360,
                memory_total_mb=16000,
                disk_utilization_pct=51.2,
                disk_used_gb=256,
                disk_total_gb=500,
                system_uptime_seconds=864000,
                process_count=142,
                health_state="EXCELLENT",
                health_reason="Nominal operating telemetry within defined baseline",
                recorded_at=t_step
            )
            # Critical CPU/Memory spike sample
            im_crit = InfrastructureMetric(
                payload_id=f"demo-infra-crit-{i:03d}",
                collector_id="col-edge-ingress-03",
                tenant_id=tenant.id,
                cpu_utilization_pct=92.4 + (i * 0.5 if i < 5 else -i * 0.3),
                memory_utilization_pct=91.8 + (i * 0.2),
                memory_used_mb=14800,
                memory_total_mb=16000,
                disk_utilization_pct=88.5,
                disk_used_gb=442,
                disk_total_gb=500,
                system_uptime_seconds=3600,
                process_count=388,
                health_state="CRITICAL",
                health_reason="Severe CPU & memory saturation (+340% baseline threshold)",
                recorded_at=t_step
            )
            db.add_all([im_healthy, im_crit])
        db.commit()

    # 6. Network: Online, Degraded and Unreachable
    net_items = [
        ("nd-demo-01", "[DEMO] Core Security Gateway", "127.0.0.1", "Server", "ONLINE", 0.5, 0.0, [8000, 3000]),
        ("nd-demo-02", "[DEMO] Core Edge Router (US-East)", "10.0.1.1", "Router", "DEGRADED", 185.4, 4.8, [80, 443]),
        ("nd-demo-03", "[DEMO] Perimeter Ingress Firewall (Offline)", "10.0.1.254", "Firewall", "OFFLINE", 0.0, 100.0, [])
    ]
    for dev_id, name, ip, dtype, status, lat, loss, ports in net_items:
        nd = db.query(NetworkDevice).filter(NetworkDevice.id == dev_id).first()
        if not nd:
            db.add(NetworkDevice(
                id=dev_id,
                tenant_id=tenant.id,
                name=name,
                ip_address=ip,
                device_type=dtype,
                monitoring_methods=json.dumps(["ping", "tcp"]),
                tcp_ports=json.dumps(ports),
                monitoring_interval_seconds=30,
                is_active=True,
                status=status,
                last_latency_ms=lat,
                last_packet_loss_pct=loss,
                open_ports_summary=json.dumps(ports),
                last_checked_at=now
            ))
        else:
            nd.name = name
            nd.status = status
            nd.last_latency_ms = lat
            nd.last_packet_loss_pct = loss
            nd.last_checked_at = now
    db.commit()

    # 7. Website Monitoring: HTTP Success, Slow Response, DNS Failure, Timeout
    web_items = [
        ("web-demo-01", "[DEMO] Production Customer Portal", "https://cynera.io", "ONLINE", 200, 68.4, "VALID", 78, "HEALTHY", "Optimal availability"),
        ("web-demo-02", "[DEMO] API Gateway Service (Slow)", "https://api-gateway.internal.net", "DEGRADED", 200, 1850.2, "VALID", 45, "HEALTHY", "Elevated round-trip response latency"),
        ("web-demo-03", "[DEMO] Legacy Auth Endpoint (DNS Fail)", "https://auth-legacy.internal.cynera", "DNS_FAILURE", 0, 0.0, "UNKNOWN", 0, "FAILED", "DNS NXDOMAIN lookup resolution failure"),
        ("web-demo-04", "[DEMO] Third-Party Webhook Receiver (Timeout)", "https://partner-hook.external.com", "TIMEOUT", 504, 10000.0, "VALID", 120, "HEALTHY", "Gateway timeout: target probe connection timed out after 10000ms")
    ]
    for wid, wname, wurl, wstatus, wcode, wlat, wssl_st, wssl_days, wdns_st, desc in web_items:
        site = db.query(MonitoredWebsite).filter(MonitoredWebsite.id == wid).first()
        if not site:
            db.add(MonitoredWebsite(
                id=wid,
                organization_id=org.id,
                created_by=owner_user.id,
                name=wname,
                url=wurl,
                description=desc,
                is_verified=True,
                verification_method="instant",
                verification_token=f"cynera-demo-verify-{wid}",
                status=wstatus,
                monitoring_interval_seconds=60,
                timeout_seconds=10,
                expected_status_codes="[200, 201, 301, 302]",
                uptime_percentage_24h=99.95 if wstatus == "ONLINE" else (82.4 if wstatus == "DEGRADED" else 0.0),
                last_response_time_ms=wlat,
                last_status_code=wcode,
                ssl_status=wssl_st,
                ssl_issuer="Let's Encrypt Authority X3" if wssl_st == "VALID" else "N/A",
                ssl_days_remaining=wssl_days,
                dns_status=wdns_st,
                dns_lookup_time_ms=18.5 if wdns_st == "HEALTHY" else 0.0,
                dns_resolved_ips='["104.21.55.2", "172.67.180.11"]' if wdns_st == "HEALTHY" else '[]',
                last_checked_at=now,
                is_active=True
            ))
        else:
            site.name = wname
            site.status = wstatus
            site.last_status_code = wcode
            site.last_response_time_ms = wlat
            site.ssl_status = wssl_st
            site.ssl_days_remaining = wssl_days
            site.dns_status = wdns_st
            site.last_checked_at = now
    db.commit()

    # 8. Application Monitoring (APM): Healthy, Degraded and Failed
    apm_items = [
        ("svc-demo-01", "[DEMO] cynera-backend-api", "Python", "HEALTHY", 0.08, 35.2, 4200),
        ("svc-demo-02", "[DEMO] payment-processing-service", "Node.js", "DEGRADED", 5.4, 480.0, 1850),
        ("svc-demo-03", "[DEMO] analytics-worker-cluster", "Go", "CRITICAL", 34.2, 1250.0, 680)
    ]
    for sid, sname, slang, sstatus, s_err, slat, scount in apm_items:
        app = db.query(ApplicationService).filter(ApplicationService.id == sid).first()
        if not app:
            db.add(ApplicationService(
                id=sid,
                organization_id=org.id,
                name=sname,
                language=slang,
                environment="production",
                version="1.4.2",
                status=sstatus,
                error_rate_pct=s_err,
                avg_latency_ms=slat,
                request_count_24h=scount,
                last_heartbeat_at=now
            ))
        else:
            app.name = sname
            app.status = sstatus
            app.error_rate_pct = s_err
            app.avg_latency_ms = slat
            app.last_heartbeat_at = now
    db.commit()

    # 9. Database Monitoring: Healthy, Warning and Offline
    db_items = [
        ("db-demo-01", "[DEMO] Primary Production PostgreSQL", "PostgreSQL", "HEALTHY", 22.4, 18, 100, 6.2, 0),
        ("db-demo-02", "[DEMO] Redis Session Cache (Warning)", "Redis", "WARNING", 88.5, 92, 100, 14.8, 18),
        ("db-demo-03", "[DEMO] Analytics Read Replica (Offline)", "PostgreSQL", "OFFLINE", 0.0, 0, 100, 0.0, 0)
    ]
    for did, dname, dtype, dstatus, dpool, dconns, dmax, dlat, dslow in db_items:
        dbi = db.query(DatabaseIntegration).filter(DatabaseIntegration.id == did).first()
        if not dbi:
            db.add(DatabaseIntegration(
                id=did,
                organization_id=org.id,
                name=dname,
                db_type=dtype,
                host=f"{did}.internal.net",
                port=5432 if dtype == "PostgreSQL" else 6379,
                database_name="cynera_demo",
                username_masked="cynera_ro",
                status=dstatus,
                pool_saturation_pct=dpool,
                active_connections=dconns,
                max_connections=dmax,
                avg_query_latency_ms=dlat,
                slow_queries_count=dslow,
                last_checked_at=now
            ))
        else:
            dbi.name = dname
            dbi.status = dstatus
            dbi.pool_saturation_pct = dpool
            dbi.active_connections = dconns
            dbi.avg_query_latency_ms = dlat
            dbi.slow_queries_count = dslow
            dbi.last_checked_at = now
    db.commit()

    # 10. Alerts: Active, Acknowledged, and Resolved
    alert_items = [
        ("alt-demo-01", "[DEMO] High Memory Saturation on Worker Pods", "CRITICAL", "infrastructure", "col-edge-ingress-03", "ACTIVE", "Memory utilization sustained at 92.5% for > 15 minutes."),
        ("alt-demo-02", "[DEMO] Database Connection Pool Saturation", "HIGH", "database", "db-demo-02", "ACKNOWLEDGED", "Redis session connection pool peaked at 92/100 active clients."),
        ("alt-demo-03", "[DEMO] Ingress Gateway Latency Spike", "MEDIUM", "network", "nd-demo-02", "RESOLVED", "Round-trip time normalized back to 1.2ms following traffic re-route.")
    ]
    for aid, atitle, asev, acat, ares, astat, aev in alert_items:
        al = db.query(Alert).filter(Alert.id == aid).first()
        if not al:
            db.add(Alert(
                id=aid,
                organization_id=org.id,
                title=atitle,
                severity=asev,
                category=acat,
                resource_name=ares,
                resource_id=ares,
                evidence=aev,
                status=astat,
                detected_at=now - datetime.timedelta(hours=1),
                resolved_at=now if astat == "RESOLVED" else None
            ))
        else:
            al.title = atitle
            al.severity = asev
            al.status = astat
            al.evidence = aev
    db.commit()

    # 11. Incidents: Open, Investigating, and Resolved
    inc_items = [
        ("inc-demo-01", "INC-DEMO-2026-0041", "[DEMO] API Gateway Latency Degradation", "CRITICAL", "OPEN", "Service response latency surged to 1850ms on public ingress router.", ["API Gateway", "Public Ingress"]),
        ("inc-demo-02", "INC-DEMO-2026-0038", "[DEMO] Intermittent Packet Loss on Remote Edge Node", "HIGH", "INVESTIGATING", "Packet loss peaked at 4.8% on secondary link.", ["Edge Node Ingress"]),
        ("inc-demo-03", "INC-DEMO-2026-0032", "[DEMO] Analytics Read Replica Failover Recovery", "MEDIUM", "RESOLVED", "Read replica connection pool was re-established after automated cluster failover.", ["Database Cluster", "Analytics Replica"])
    ]
    for i_id, i_num, i_title, i_sev, i_stat, i_desc, i_comps in inc_items:
        inc = db.query(Incident).filter(Incident.id == i_id).first()
        if not inc:
            db.add(Incident(
                id=i_id,
                incident_number=i_num,
                tenant_id=tenant.id,
                collector_id="col-prod-core-01",
                title=i_title,
                description=i_desc,
                severity=i_sev,
                status=i_stat,
                affected_components=json.dumps(i_comps),
                contributing_signals=json.dumps([f"Severity: {i_sev}", f"Status: {i_stat}"]),
                created_at=now - datetime.timedelta(hours=2),
                resolved_at=now if i_stat == "RESOLVED" else None
            ))
        else:
            inc.title = i_title
            inc.severity = i_sev
            inc.status = i_stat
            inc.description = i_desc
    db.commit()

    # 12. Reports: Successful and Failed Example Outcomes
    rep_items = [
        ("rep-demo-01", "[DEMO] Monthly SLA & Zero-Trust Telemetry Audit", "executive_summary", "last_30_days", {
            "status": "COMPLETED",
            "sla_availability_pct": 99.98,
            "zero_trust_compliance": "100%",
            "incidents_resolved": 8,
            "executive_summary": "Zero-trust privacy boundary strictly enforced. 100% of telemetry sanitized with zero raw log egress."
        }),
        ("rep-demo-02", "[DEMO] Disaster Recovery & Failover Drill Assessment", "security_audit", "last_7_days", {
            "status": "FAILED",
            "sla_availability_pct": 94.20,
            "zero_trust_compliance": "98.2%",
            "failed_targets": 3,
            "executive_summary": "Failover drill revealed 3 breached SLA recovery targets on secondary edge replica nodes."
        })
    ]
    for r_id, r_title, r_type, r_range, r_summary in rep_items:
        rep = db.query(ReportRecord).filter(ReportRecord.id == r_id).first()
        if not rep:
            db.add(ReportRecord(
                id=r_id,
                organization_id=org.id,
                created_by=admin_user.id,
                title=r_title,
                report_type=r_type,
                time_range=r_range,
                summary_json=json.dumps(r_summary),
                created_at=now - datetime.timedelta(days=1)
            ))
        else:
            rep.title = r_title
            rep.summary_json = json.dumps(r_summary)
    db.commit()

    # 13. Notifications: Success, Warning, and Critical
    notif_items = [
        ("notif-demo-01", "[DEMO] Automated SSL Certificate Renewal Succeeded", "TLS certificate for https://cynera.io successfully renewed for 90 days.", "success"),
        ("notif-demo-02", "[DEMO] Warning: Edge Collector Memory Nearing Threshold", "Memory utilization on col-edge-ingress-03 exceeded 85%.", "warning"),
        ("notif-demo-03", "[DEMO] CRITICAL: Analytics Replica Connection Offline", "Heartbeat lost on analytics read replica host after 3 failed retries.", "error")
    ]
    for n_id, n_title, n_msg, n_type in notif_items:
        notif = db.query(Notification).filter(Notification.id == n_id).first()
        if not notif:
            db.add(Notification(
                id=n_id,
                organization_id=org.id,
                user_id=admin_user.id,
                title=n_title,
                message=n_msg,
                type=n_type,
                is_read=False,
                created_at=now
            ))
        else:
            notif.title = n_title
            notif.message = n_msg
            notif.type = n_type
    db.commit()

    # 14. Security: Normal and Suspicious Activity
    sec_normal = db.query(SecuritySummary).filter(SecuritySummary.id == "sec-demo-01").first()
    if not sec_normal:
        db.add(SecuritySummary(
            id="sec-demo-01",
            payload_id="demo-sec-normal-01",
            collector_id=c_online.id,
            tenant_id=tenant.id,
            failed_login_count=0,
            suspicious_activity_score=2.0,
            security_event_severity="LOW",
            authentication_failure_rate_per_min=0.0,
            pseudonymous_source_cluster="cluster-trusted-internal",
            redacted_tokens_detected=12,
            summary_description="[DEMO] Zero-trust ingress boundary verified. 100% of telemetry sanitized with zero raw log egress.",
            recorded_at=now
        ))
    else:
        sec_normal.collector_id = c_online.id
        sec_normal.tenant_id = tenant.id
        sec_normal.failed_login_count = 0
        sec_normal.suspicious_activity_score = 2.0
        sec_normal.security_event_severity = "LOW"
        sec_normal.authentication_failure_rate_per_min = 0.0
        sec_normal.summary_description = "[DEMO] Zero-trust ingress boundary verified. 100% of telemetry sanitized with zero raw log egress."
        sec_normal.recorded_at = now

    sec_suspicious = db.query(SecuritySummary).filter(SecuritySummary.id == "sec-demo-02").first()
    if not sec_suspicious:
        db.add(SecuritySummary(
            id="sec-demo-02",
            payload_id="demo-sec-suspicious-02",
            collector_id=c_offline.id,
            tenant_id=tenant.id,
            failed_login_count=84,
            suspicious_activity_score=89.5,
            security_event_severity="CRITICAL",
            authentication_failure_rate_per_min=14.0,
            pseudonymous_source_cluster="external-untrusted-dmz",
            redacted_tokens_detected=4,
            summary_description="[DEMO] Suspicious brute-force credential stuffing detected on edge gateway. Ingress rate limiting automatically engaged.",
            recorded_at=now - datetime.timedelta(minutes=15)
        ))
    else:
        sec_suspicious.collector_id = c_offline.id
        sec_suspicious.tenant_id = tenant.id
        sec_suspicious.failed_login_count = 84
        sec_suspicious.suspicious_activity_score = 89.5
        sec_suspicious.security_event_severity = "CRITICAL"
        sec_suspicious.authentication_failure_rate_per_min = 14.0
        sec_suspicious.summary_description = "[DEMO] Suspicious brute-force credential stuffing detected on edge gateway. Ingress rate limiting automatically engaged."
        sec_suspicious.recorded_at = now - datetime.timedelta(minutes=15)
    db.commit()

    logger.info("[DemoSeeder] Two active demo accounts (admin@cynera.io & owner@cynera.io) and healthy+failure demo records successfully seeded.")
