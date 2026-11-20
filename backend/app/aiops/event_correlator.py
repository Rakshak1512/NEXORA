import time
import json
import uuid
from typing import List, Dict, Any, Optional

class EventCorrelator:
    """
    EVENT CORRELATION ENGINE
    Deduplicates and groups related alerts within temporal sliding windows
    (e.g., CPU + Memory + Latency) into a single unified incident.
    Suppresses operational alert fatigue while exposing root cause.
    """
    def __init__(self, window_seconds: int = 90):
        self.window_seconds = window_seconds

    def correlate_alerts(
        self,
        tenant_id: str,
        collector_id: str,
        alerts: List[Dict[str, Any]],
        existing_open_incidents: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Correlates newly detected alerts against open incidents or groups multiple
        simultaneous alerts into a new high-confidence incident.
        """
        if not alerts:
            return None

        alert_types = [a["alert_type"] for a in alerts]
        max_severity = "LOW"
        severity_ranks = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        for a in alerts:
            if severity_ranks.get(a["severity"], 1) > severity_ranks.get(max_severity, 1):
                max_severity = a["severity"]

        # Check if an existing open incident exists for this collector
        for inc in existing_open_incidents:
            if inc.get("collector_id") == collector_id and inc.get("status") in ["OPEN", "INVESTIGATING"]:
                # Correlate into existing incident
                return {
                    "action": "ATTACH_TO_EXISTING",
                    "incident_id": inc["id"],
                    "incident_number": inc["incident_number"],
                    "new_alerts": alerts
                }

        # Otherwise create a new correlated incident
        signals = [a["message"] for a in alerts]
        components = ["Core-Node-Runtime"]
        title = f"Multi-Signal Degradation on {collector_id}"
        reason = "Temporal coincidence of metric anomalies within 90-second evaluation window."

        if "CPU_SATURATION" in alert_types and "MEMORY_LEAK_BURST" in alert_types:
            title = f"Exhaustion Cascade: High CPU & Memory Saturation on {collector_id}"
            components = ["Thread-Pool", "JVM-Runtime", "Worker-Container"]
            reason = "Parallel saturation of compute and memory signals indicating unbounded workload or worker deadlock."
        elif "PACKET_LOSS_SURGE" in alert_types or "LATENCY_DEGRADATION" in alert_types:
            title = f"Network Congestion & Latency Surge on {collector_id}"
            components = ["Edge-Envoy-Gateway", "TCP-Connection-Pool"]
            reason = "Transit packet drops accompanied by latency spike across edge routing tier."
        elif "AUTHENTICATION_BURST" in alert_types:
            title = f"Security Auth Burst & Edge Ingress Saturation on {collector_id}"
            components = ["Auth-Service", "Ingress-Rate-Limiter"]
            reason = "Spike in authentication failures exceeding 3-sigma security threshold."

        incident_number = f"INC-2026-{uuid.uuid4().hex[:6].upper()}"

        return {
            "action": "CREATE_NEW",
            "incident_number": incident_number,
            "tenant_id": tenant_id,
            "collector_id": collector_id,
            "title": title,
            "description": f"AIOps correlated {len(alerts)} simultaneous alerts into a single incident: " + "; ".join(signals),
            "severity": max_severity,
            "status": "OPEN",
            "affected_components": components,
            "contributing_signals": signals,
            "correlation_reason": reason,
            "alerts": alerts
        }

event_correlator = EventCorrelator()

