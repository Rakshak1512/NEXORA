import pytest
from app.aiops.anomaly_detector import AIOpsAnomalyDetector
from app.aiops.event_correlator import EventCorrelator
from app.aiops.recommendation_engine import AIRecommendationEngine

def test_anomaly_detection_cpu_spike():
    detector = AIOpsAnomalyDetector()
    telemetry = {
        "cpu_utilization_pct": 98.2,
        "memory_utilization_pct": 50.0,
        "disk_utilization_pct": 50.0,
        "latency_ms": 15.0,
        "packet_loss_pct": 0.0
    }
    anomalies = detector.analyze(telemetry)
    assert len(anomalies) >= 1
    assert any(a["alert_type"] == "CPU_SATURATION" for a in anomalies)

def test_event_correlator_groups_simultaneous_signals():
    correlator = EventCorrelator()
    alerts = [
        {"alert_type": "CPU_SATURATION", "severity": "CRITICAL", "message": "CPU 98%"},
        {"alert_type": "MEMORY_LEAK_BURST", "severity": "HIGH", "message": "Memory 91%"}
    ]
    res = correlator.correlate_alerts(
        tenant_id="tenant-01",
        collector_id="col-01",
        alerts=alerts,
        existing_open_incidents=[]
    )
    assert res is not None
    assert res["action"] == "CREATE_NEW"
    assert "Exhaustion Cascade" in res["title"]
    assert res["severity"] == "CRITICAL"

def test_explainable_ai_recommendation():
    engine = AIRecommendationEngine()
    incident = {"title": "Exhaustion Cascade: High CPU & Memory", "contributing_signals": ["CPU: 98%"]}
    telemetry = {"cpu_utilization_pct": 98.0, "memory_utilization_pct": 90.0}
    rec = engine.generate_recommendation(incident, telemetry)

    assert "possible_root_cause" in rec
    assert "suggested_action" in rec
    assert "rollback_plan" in rec
    assert rec["confidence_score"] > 80.0

