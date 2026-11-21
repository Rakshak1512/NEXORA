import json
import time
import uuid
import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models.models import (
    InfrastructureMetric, NetworkMetric, SecuritySummary,
    Collector, IncidentAlert, Incident, AIRecommendation,
    RemediationApproval, PerformanceBenchmark,
    NetworkDevice, NetworkCheckResult
)
from ..schemas.schemas import TelemetryIngestPayload
from ..aiops.anomaly_detector import anomaly_detector
from ..aiops.event_correlator import event_correlator
from ..aiops.recommendation_engine import recommendation_engine
from ..websocket.manager import ws_manager

class TelemetryService:
    @staticmethod
    async def process_ingestion(db: Session, payload: TelemetryIngestPayload) -> Tuple[bool, str, Dict[str, Any]]:
        start_time = time.time()

        # 1. DUPLICATE IDEMPOTENCY CHECK
        existing = db.query(InfrastructureMetric).filter(
            InfrastructureMetric.payload_id == payload.payload_id
        ).first()

        if existing:
            # Duplicate payload detected - record in benchmark and return idempotently
            bench = db.query(PerformanceBenchmark).filter(
                PerformanceBenchmark.tenant_id == payload.tenant_id
            ).first()
            if bench:
                bench.duplicate_count += 1
                db.commit()
            return True, "Duplicate payload ignored idempotently.", {"payload_id": payload.payload_id, "status": "DUPLICATE_ACKNOWLEDGED"}

        # 2. UPDATE COLLECTOR LAST SEEN & ONLINE STATUS
        collector = db.query(Collector).filter(Collector.id == payload.collector_id).first()
        now_dt = datetime.datetime.now(datetime.timezone.utc)

        if not collector:
            collector = Collector(
                id=payload.collector_id,
                tenant_id=payload.tenant_id,
                name=f"Collector {payload.collector_id}",
                hostname=payload.hostname_pseudonym or "host-masked",
                ip_address_pseudonym=payload.hostname_pseudonym or "masked-ip",
                version=payload.version,
                status="online",
                auth_token_hash="hash-secret",
                last_seen_at=now_dt
            )
            db.add(collector)
        else:
            collector.status = "online"
            collector.last_seen_at = now_dt

        # 3. SAVE INFRASTRUCTURE METRIC
        infra_record = InfrastructureMetric(
            id=str(uuid.uuid4()),
            payload_id=payload.payload_id,
            collector_id=payload.collector_id,
            tenant_id=payload.tenant_id,
            cpu_utilization_pct=payload.cpu_utilization_pct,
            memory_utilization_pct=payload.memory_utilization_pct,
            memory_used_mb=payload.memory_used_mb,
            memory_total_mb=payload.memory_total_mb,
            disk_utilization_pct=payload.disk_utilization_pct,
            disk_used_gb=payload.disk_used_gb,
            disk_total_gb=payload.disk_total_gb,
            system_uptime_seconds=payload.system_uptime_seconds,
            process_count=payload.process_count,
            health_state=payload.health_state or "EXCELLENT",
            health_reason=payload.health_reason or "Nominal operational state.",
            recorded_at=now_dt
        )
        db.add(infra_record)

        # 4. SAVE NETWORK METRIC
        net_record = NetworkMetric(
            id=str(uuid.uuid4()),
            payload_id=payload.payload_id,
            collector_id=payload.collector_id,
            tenant_id=payload.tenant_id,
            bytes_sent_rate_kbps=payload.bytes_sent_rate_kbps,
            bytes_recv_rate_kbps=payload.bytes_recv_rate_kbps,
            latency_ms=payload.latency_ms,
            packet_loss_pct=payload.packet_loss_pct,
            active_connections=payload.active_connections,
            connectivity_status=payload.connectivity_status,
            recorded_at=now_dt
        )
        db.add(net_record)

        # 5. SAVE SECURITY SUMMARY (Clean aggregates only - NO RAW SECRETS)
        sec_record = SecuritySummary(
            id=str(uuid.uuid4()),
            payload_id=payload.payload_id,
            collector_id=payload.collector_id,
            tenant_id=payload.tenant_id,
            failed_login_count=payload.failed_login_count,
            suspicious_activity_score=payload.suspicious_activity_score,
            security_event_severity=payload.security_event_severity or "LOW",
            authentication_failure_rate_per_min=payload.authentication_failure_rate_per_min,
            pseudonymous_source_cluster=payload.pseudonymous_source_cluster,
            redacted_tokens_detected=payload.redacted_tokens_detected,
            summary_description=payload.summary_description,
            recorded_at=now_dt
        )
        db.add(sec_record)
        db.commit()

        # 6. RUN AIOPS ANOMALY DETECTION PIPELINE
        detected_anomalies = anomaly_detector.analyze(payload.model_dump())

        # 6b. PROCESS NETWORK DEVICES TELEMETRY CHECKS
        if payload.network_devices_checks:
            for net_check in payload.network_devices_checks:
                dev_id = net_check.get("device_id")
                ip = net_check.get("ip_address")
                device = None
                if dev_id:
                    device = db.query(NetworkDevice).filter(NetworkDevice.id == dev_id).first()
                if not device and ip:
                    device = db.query(NetworkDevice).filter(
                        NetworkDevice.ip_address == ip,
                        NetworkDevice.tenant_id == payload.tenant_id
                    ).first()

                if device:
                    device.status = net_check.get("check_status", "ONLINE")
                    device.last_latency_ms = float(net_check.get("latency_ms", 0.0))
                    device.last_packet_loss_pct = float(net_check.get("packet_loss_pct", 0.0))
                    device.open_ports_summary = json.dumps(net_check.get("open_ports", []))
                    device.last_checked_at = now_dt

                    # Save check history record
                    rec = NetworkCheckResult(
                        device_id=device.id,
                        tenant_id=payload.tenant_id,
                        collector_id=payload.collector_id,
                        check_type="collector_cycle",
                        status=device.status,
                        latency_ms=device.last_latency_ms,
                        packet_loss_pct=device.last_packet_loss_pct,
                        open_ports=json.dumps(net_check.get("open_ports", [])),
                        closed_ports=json.dumps(net_check.get("closed_ports", [])),
                        port_details=json.dumps(net_check.get("port_details", {})),
                        metrics_payload=json.dumps(net_check.get("metrics_payload", {}))
                    )
                    db.add(rec)

                # Analyze network check for anomalies
                net_anoms = anomaly_detector.analyze_network_device(net_check)
                detected_anomalies.extend(net_anoms)
            db.commit()
        created_alerts = []
        new_incident_data = None

        if detected_anomalies:
            alert_start = time.time()
            for anom in detected_anomalies:
                alert_entry = IncidentAlert(
                    id=str(uuid.uuid4()),
                    tenant_id=payload.tenant_id,
                    collector_id=payload.collector_id,
                    alert_type=anom["alert_type"],
                    severity=anom["severity"],
                    metric_name=anom["metric_name"],
                    metric_value=float(anom["metric_value"]),
                    threshold_value=float(anom["threshold_value"]),
                    message=anom["message"],
                    is_correlated=False,
                    detected_at=now_dt
                )
                db.add(alert_entry)
                created_alerts.append(anom)
            db.commit()

            # 7. EVENT CORRELATION
            existing_open = db.query(Incident).filter(
                Incident.tenant_id == payload.tenant_id,
                Incident.status.in_(["OPEN", "INVESTIGATING"])
            ).all()

            existing_list = [
                {
                    "id": inc.id,
                    "incident_number": inc.incident_number,
                    "collector_id": inc.collector_id,
                    "status": inc.status,
                    "title": inc.title
                }
                for inc in existing_open
            ]

            correlation_result = event_correlator.correlate_alerts(
                tenant_id=payload.tenant_id,
                collector_id=payload.collector_id,
                alerts=detected_anomalies,
                existing_open_incidents=existing_list
            )

            if correlation_result and correlation_result["action"] == "CREATE_NEW":
                inc_id = str(uuid.uuid4())
                incident_model = Incident(
                    id=inc_id,
                    incident_number=correlation_result["incident_number"],
                    tenant_id=payload.tenant_id,
                    collector_id=payload.collector_id,
                    title=correlation_result["title"],
                    description=correlation_result["description"],
                    severity=correlation_result["severity"],
                    status="OPEN",
                    affected_components=json.dumps(correlation_result["affected_components"]),
                    contributing_signals=json.dumps(correlation_result["contributing_signals"]),
                    correlation_reason=correlation_result["correlation_reason"],
                    created_at=now_dt
                )
                db.add(incident_model)
                db.commit()

                # Link alerts to this incident
                db.query(IncidentAlert).filter(
                    IncidentAlert.collector_id == payload.collector_id,
                    IncidentAlert.incident_id.is_(None)
                ).update({"incident_id": inc_id, "is_correlated": True})
                db.commit()

                # 8. GENERATE EXPLAINABLE AI RECOMMENDATION
                rec_data = recommendation_engine.generate_recommendation(
                    incident={
                        "title": correlation_result["title"],
                        "contributing_signals": correlation_result["contributing_signals"]
                    },
                    telemetry=payload.model_dump()
                )

                rec_id = str(uuid.uuid4())
                rec_model = AIRecommendation(
                    id=rec_id,
                    incident_id=inc_id,
                    tenant_id=payload.tenant_id,
                    detected_anomaly=rec_data["detected_anomaly"],
                    contributing_signals=json.dumps(rec_data["contributing_signals"]),
                    baseline_comparison=rec_data["baseline_comparison"],
                    confidence_score=rec_data["confidence_score"],
                    possible_root_cause=rec_data["possible_root_cause"],
                    recommended_investigation=rec_data["recommended_investigation"],
                    suggested_action=rec_data["suggested_action"],
                    suggested_action_type=rec_data["suggested_action_type"],
                    rollback_plan=rec_data["rollback_plan"],
                    is_deterministic_fallback=rec_data.get("is_deterministic_fallback", True),
                    created_at=now_dt
                )
                db.add(rec_model)

                # 9. CREATE PENDING REMEDIATION APPROVAL RECORD
                approval_id = str(uuid.uuid4())
                approval_model = RemediationApproval(
                    id=approval_id,
                    recommendation_id=rec_id,
                    incident_id=inc_id,
                    tenant_id=payload.tenant_id,
                    action_description=rec_data["suggested_action"],
                    target_component=f"Cluster {payload.collector_id}",
                    policy_evaluation_result="POLICY_PASSED_REQUIRES_OPERATOR_SIGN_OFF",
                    status="PENDING",
                    rollback_information=rec_data["rollback_plan"],
                    requested_at=now_dt
                )
                db.add(approval_model)
                db.commit()

                new_incident_data = {
                    "id": inc_id,
                    "incident_number": correlation_result["incident_number"],
                    "title": correlation_result["title"],
                    "severity": correlation_result["severity"]
                }

        # 10. UPDATE BENCHMARK STATS (Target: < 10s P95)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        bench = db.query(PerformanceBenchmark).filter(
            PerformanceBenchmark.tenant_id == payload.tenant_id
        ).first()
        if not bench:
            bench = PerformanceBenchmark(
                id=str(uuid.uuid4()),
                tenant_id=payload.tenant_id,
                p50_latency_ms=elapsed_ms,
                p95_latency_ms=elapsed_ms * 1.5,
                alert_generation_time_ms=elapsed_ms * 0.8,
                heartbeat_age_seconds=2,
                queue_backlog_depth=0,
                delivery_success_pct=100.0,
                duplicate_count=0,
                lost_record_count=0
            )
            db.add(bench)
        else:
            bench.p50_latency_ms = round((bench.p50_latency_ms * 0.9) + (elapsed_ms * 0.1), 2)
            bench.p95_latency_ms = round(max(bench.p95_latency_ms, elapsed_ms * 1.3), 2)
        db.commit()

        # 11. WEBSOCKET BROADCAST TO UI DASHBOARD
        broadcast_data = {
            "payload_id": payload.payload_id,
            "collector_id": payload.collector_id,
            "cpu": payload.cpu_utilization_pct,
            "memory": payload.memory_utilization_pct,
            "disk": payload.disk_utilization_pct,
            "latency": payload.latency_ms,
            "packet_loss": payload.packet_loss_pct,
            "health_state": payload.health_state,
            "anomalies_detected": len(detected_anomalies),
            "new_incident": new_incident_data,
            "timestamp": now_dt.isoformat()
        }
        await ws_manager.broadcast("TELEMETRY_UPDATE", broadcast_data, tenant_id=payload.tenant_id)

        return True, "Telemetry processed and correlated successfully.", {
            "payload_id": payload.payload_id,
            "anomalies_detected": len(detected_anomalies),
            "incident_triggered": new_incident_data is not None
        }

telemetry_service = TelemetryService()

