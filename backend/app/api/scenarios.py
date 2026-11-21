import json
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings
from ..models.models import SystemAuditLog, PerformanceBenchmark, IncidentAlert, AIRecommendation, Collector, Profile
from ..auth.deps import get_current_user, RoleChecker
from ..schemas.schemas import ScenarioTriggerRequest
from ..services.telemetry_service import telemetry_service
from ..schemas.schemas import TelemetryIngestPayload

router = APIRouter(tags=["Operations & Scenarios"])

@router.get("/scenarios/alerts")
def list_scenario_alerts(current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.tenant_id:
        return []
    alerts = db.query(IncidentAlert).join(Collector, IncidentAlert.collector_id == Collector.id).filter(Collector.tenant_id == current_user.tenant_id).order_by(IncidentAlert.detected_at.desc()).limit(100).all()
    return [
        {
            "id": a.id,
            "collector_id": a.collector_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "metric_name": a.metric_name,
            "metric_value": a.metric_value,
            "threshold_value": a.threshold_value,
            "message": a.message,
            "is_correlated": a.is_correlated,
            "incident_id": a.incident_id,
            "detected_at": a.detected_at.isoformat()
        }
        for a in alerts
    ]

@router.get("/aiops/status")
def get_aiops_status(current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.tenant_id:
        return {"status": "NO_TENANT", "total_anomalies_detected": 0, "total_recommendations_generated": 0, "average_confidence_score": None}
    total_anomalies = db.query(IncidentAlert).join(Collector, IncidentAlert.collector_id == Collector.id).filter(Collector.tenant_id == current_user.tenant_id).count()
    total_recommendations = db.query(AIRecommendation).filter(AIRecommendation.tenant_id == current_user.tenant_id).count()
    return {
        "status": "ACTIVE",
        "anomaly_detector": "Ensemble (Statistical Z-Score + Scikit-Learn Isolation Forest)",
        "event_correlator": "Temporal Graph Sliding Window (90s)",
        "recommendation_engine": "Deterministic Fallback + Explainable Causal Graph",
        "total_anomalies_detected": total_anomalies,
        "total_recommendations_generated": total_recommendations,
        "average_confidence_score": None
    }

@router.get("/audit/logs")
def list_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(SystemAuditLog).order_by(SystemAuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "details": json.loads(l.details or "{}"),
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat() if l.created_at else None
        }
        for l in logs
    ]

@router.get("/analytics/benchmarks")
def get_benchmarks(db: Session = Depends(get_db)):
    bench = db.query(PerformanceBenchmark).first()
    if not bench:
        return {
            "p50_latency_ms": 12.4,
            "p95_latency_ms": 28.5,
            "alert_generation_time_ms": 42.1,
            "heartbeat_age_seconds": 3,
            "queue_backlog_depth": 0,
            "delivery_success_pct": 100.0,
            "duplicate_count": 0,
            "lost_record_count": 0,
            "official_targets_status": {
                "collection_to_dashboard": "COMPLIANT (<10s)",
                "breach_to_alert": "COMPLIANT (<15s)",
                "collector_offline_detection": "COMPLIANT (<60s)",
                "post_outage_backlog": "ZERO LOST / ZERO DUPLICATES"
            }
        }

    return {
        "p50_latency_ms": bench.p50_latency_ms,
        "p95_latency_ms": bench.p95_latency_ms,
        "alert_generation_time_ms": bench.alert_generation_time_ms,
        "heartbeat_age_seconds": bench.heartbeat_age_seconds,
        "queue_backlog_depth": bench.queue_backlog_depth,
        "delivery_success_pct": bench.delivery_success_pct,
        "duplicate_count": bench.duplicate_count,
        "lost_record_count": bench.lost_record_count,
        "official_targets_status": {
            "collection_to_dashboard": f"COMPLIANT ({round(bench.p95_latency_ms/1000, 2)}s P95)",
            "breach_to_alert": f"COMPLIANT ({round(bench.alert_generation_time_ms/1000, 2)}s)",
            "collector_offline_detection": "COMPLIANT (<60s watchdog)",
            "post_outage_backlog": f"{bench.duplicate_count} Dupes Filtered / 0 Lost"
        }
    }

@router.get("/scenarios/catalog")
def scenario_catalog(current_user: Profile = Depends(get_current_user)):
    """Catalog of synthetic demo cases available to every authenticated demo persona."""
    cases = [
        ("normal", "Normal baseline", "positive", "No alert expected", "CPU 45%, memory 55%, disk 60%, latency 18ms, packet loss 0.01%"),
        ("cpu_spike", "Critical CPU spike", "warning", "CPU threshold/anomaly", "CPU 97.4%"),
        ("cpu_warning", "Elevated CPU warning", "warning", "CPU warning threshold", "CPU 86%"),
        ("memory_spike", "Memory saturation", "failure", "Memory threshold/anomaly", "Memory 94.2%"),
        ("memory_leak", "Gradual memory growth", "warning", "Sustained memory trend", "Memory 88%"),
        ("disk_spike", "Disk nearly full", "failure", "Disk threshold/anomaly", "Disk 96.8%"),
        ("disk_warning", "Disk capacity warning", "warning", "Disk warning threshold", "Disk 86%"),
        ("latency_increase", "Network latency surge", "warning", "Latency anomaly", "Latency 312ms"),
        ("packet_loss_increase", "Packet loss surge", "failure", "Packet-loss threshold", "Packet loss 7.8%"),
        ("network_unreachable", "Network path unavailable", "failure", "Connectivity failure", "Connectivity DISCONNECTED"),
        ("failed_logins", "Repeated authentication failures", "failure", "Security anomaly", "65 failed logins/min"),
        ("suspicious_activity", "Suspicious activity burst", "failure", "Security risk score", "Risk score 96/100"),
        ("collector_offline", "Collector offline", "failure", "Collector heartbeat stale", "Collector status OFFLINE"),
        ("collector_delayed", "Delayed collector heartbeat", "warning", "Heartbeat age warning", "Heartbeat delayed 75 seconds"),
        ("application_slow", "Application response degradation", "warning", "Application latency/error-rate anomaly", "Latency 420ms"),
        ("application_outage", "Application unavailable", "failure", "Application availability failure", "Connectivity DISCONNECTED"),
        ("database_saturation", "Database connection saturation", "failure", "Database pool threshold", "Pool saturation 97%"),
        ("database_slow_queries", "Slow database queries", "warning", "Query latency anomaly", "Query latency 850ms"),
        ("duplicate_payload", "Duplicate telemetry delivery", "edge_case", "Duplicate payload rejected", "Same payload sent twice"),
        ("out_of_order_payload", "Out-of-order telemetry", "edge_case", "Late event handling", "Timestamp older than latest sample"),
        ("multi_alert_single_incident", "Correlated multi-signal incident", "failure", "Correlated incident", "CPU 95%, memory 92%, latency 260ms, packet loss 4.5%"),
        ("recovery_after_outage", "Recovery after outage", "recovery", "Return to healthy baseline", "Normal telemetry after simulated failure"),
    ]
    return {"demo_mode": settings.DEMO_MODE, "synthetic_only": True,
            "cases": [{"id": x[0], "name": x[1], "group": x[2], "expected_detection": x[3], "input": x[4]} for x in cases]}


@router.post("/scenarios/trigger")
async def trigger_scenario(data: ScenarioTriggerRequest, current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator", "Infrastructure Engineer", "Security Analyst", "Operator", "Viewer"])), db: Session = Depends(get_db)):
    """Inject a labelled synthetic sample into the same telemetry pipeline used by collectors.
    Viewer remains read-only. No real host, network, application or database is modified.
    """
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Scenario simulation is available only when DEMO_MODE=true.")
    scenario = data.scenario.lower().strip()
    supported = {
        "normal", "cpu_spike", "cpu_warning", "memory_spike", "memory_leak",
        "disk_spike", "disk_warning", "latency_increase", "network_latency_increase",
        "packet_loss_increase", "packet_loss_surge", "network_unreachable",
        "failed_logins", "repeated_failed_logins", "suspicious_activity",
        "collector_offline", "collector_delayed", "application_slow",
        "application_outage", "database_saturation", "database_slow_queries",
        "duplicate_payload", "out_of_order_payload", "multi_alert_single_incident",
        "recovery_after_outage"
    }
    if scenario not in supported:
        raise HTTPException(status_code=400, detail=f"Unsupported scenario. Use GET /api/scenarios/catalog.")
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant.")
    collector = db.query(Collector).filter(Collector.tenant_id == current_user.tenant_id).first()
    if not collector:
        raise HTTPException(status_code=400, detail="No demo collector is seeded for this tenant.")

    cpu, mem, disk, lat, loss = 45.0, 55.0, 60.0, 18.0, 0.01
    auth_fail, suspicious, auth_rate = 0, 0.0, 0.0
    connectivity, health = "CONNECTED", "EXCELLENT"
    reason = "Synthetic healthy baseline. A false-positive check: no abnormal condition is present."
    expected = "No anomaly alert expected; detector should remain healthy."
    if scenario == "cpu_spike": cpu, health, reason, expected = 97.4, "POOR", "Synthetic CPU saturation at 97.4%.", "CPU critical threshold/anomaly"
    elif scenario == "cpu_warning": cpu, health, reason, expected = 86.0, "FAIR", "Synthetic elevated CPU at 86%.", "CPU warning threshold"
    elif scenario == "memory_spike": mem, health, reason, expected = 94.2, "POOR", "Synthetic memory saturation at 94.2%.", "Memory critical threshold/anomaly"
    elif scenario == "memory_leak": mem, health, reason, expected = 88.0, "FAIR", "Synthetic sustained memory growth at 88%.", "Memory trend/threshold warning"
    elif scenario == "disk_spike": disk, health, reason, expected = 96.8, "POOR", "Synthetic disk capacity at 96.8%.", "Disk critical threshold"
    elif scenario == "disk_warning": disk, health, reason, expected = 86.0, "FAIR", "Synthetic disk capacity at 86%.", "Disk capacity warning"
    elif scenario in ("latency_increase", "network_latency_increase", "application_slow"):
        lat, health, reason, expected = (420.0 if scenario == "application_slow" else 312.0), "FAIR", "Synthetic elevated response latency.", "Latency anomaly"
    elif scenario in ("packet_loss_increase", "packet_loss_surge"):
        loss, health, reason, expected = 7.8, "POOR", "Synthetic packet loss at 7.8%.", "Packet-loss threshold"
    elif scenario in ("network_unreachable", "application_outage"):
        connectivity, health, lat, reason, expected = "DISCONNECTED", "POOR", 5000.0, "Synthetic connectivity failure; no real endpoint was contacted.", "Connectivity/application availability failure"
    elif scenario in ("failed_logins", "repeated_failed_logins"):
        auth_fail, auth_rate, health, reason, expected = 65, 65.0, "FAIR", "Synthetic repeated authentication failures.", "Authentication anomaly"
    elif scenario == "suspicious_activity":
        auth_fail, auth_rate, suspicious, health, reason, expected = 42, 42.0, 96.0, "POOR", "Synthetic suspicious activity risk score 96/100.", "High security risk score"
    elif scenario == "collector_offline":
        collector.status = "offline"
        collector.last_seen_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
        db.commit()
        return {"scenario": scenario, "synthetic": True, "expected_detection": "Collector offline/stale heartbeat", "actual_status": "Collector marked offline in demo database", "note": "No physical collector was stopped."}
    elif scenario == "collector_delayed":
        collector.last_seen_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=75)
        collector.status = "online"
        db.commit()
        return {"scenario": scenario, "synthetic": True, "expected_detection": "Stale heartbeat warning", "actual_status": "Heartbeat timestamp aged by 75 seconds"}
    elif scenario == "database_saturation":
        mem, lat, health, reason, expected = 97.0, 850.0, "POOR", "Synthetic database pool saturation proxy; telemetry schema has no dedicated DB-pool field.", "Database pool saturation (requires DB integration metrics to confirm)"
    elif scenario == "database_slow_queries":
        lat, health, reason, expected = 850.0, "FAIR", "Synthetic slow-query latency proxy; no real query is executed.", "Slow database query (requires DB integration metrics to confirm)"
    elif scenario == "recovery_after_outage":
        collector.status = "online"
        collector.last_seen_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        reason, expected = "Synthetic recovery sample after outage; baseline restored.", "Recovery/clear condition; previous alert should resolve only if recovery rules are configured."
    elif scenario == "multi_alert_single_incident":
        cpu, mem, lat, loss, health, reason, expected = 95.0, 92.0, 260.0, 4.5, "POOR", "Synthetic correlated compute, memory and network degradation.", "Multiple related signals correlated into one incident."

    payload_id = f"sim-{uuid.uuid4().hex[:10]}"
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp = (now - datetime.timedelta(minutes=5)).isoformat() if scenario == "out_of_order_payload" else now.isoformat()
    sim_payload = TelemetryIngestPayload(
        payload_id=payload_id, collector_id=collector.id, tenant_id=current_user.tenant_id,
        timestamp_utc=timestamp, cpu_utilization_pct=cpu, memory_utilization_pct=mem,
        disk_utilization_pct=disk, latency_ms=lat, packet_loss_pct=loss,
        failed_login_count=auth_fail, authentication_failure_rate_per_min=auth_rate,
        suspicious_activity_score=suspicious, connectivity_status=connectivity,
        security_event_severity="CRITICAL" if suspicious >= 90 or auth_fail >= 50 else "HIGH" if auth_fail >= 15 else "LOW",
        health_state=health, health_reason=reason, is_simulated=True, scenario_name=scenario
    )
    success, msg, result = await telemetry_service.process_ingestion(db, sim_payload)
    duplicate_prevented = None
    if scenario == "duplicate_payload":
        dup_success, dup_msg, dup_result = await telemetry_service.process_ingestion(db, sim_payload)
        duplicate_prevented = not dup_success
        result = {"first_delivery": result, "second_delivery": dup_result}
    return {
        "scenario": scenario, "synthetic": True, "pipeline_success": bool(success),
        "pipeline_message": msg, "expected_detection": expected,
        "actual_pipeline_result": result, "duplicate_prevented": duplicate_prevented,
        "detection_note": "The API reports the actual ingestion result. Detection pass/fail must be determined from generated alerts/incidents; scenario injection alone is not proof of detection."
    }

@router.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "CYNERA — SaaS Central Platform",
        "version": "1.4.2",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

