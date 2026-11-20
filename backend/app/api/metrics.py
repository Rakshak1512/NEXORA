import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.models import (
    InfrastructureMetric, NetworkMetric, SecuritySummary,
    Collector, Incident, IncidentAlert
)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.get("/summary")
def get_metrics_summary(db: Session = Depends(get_db)):
    collectors = db.query(Collector).all()
    total_cols = len(collectors)
    online_cols = sum(1 for c in collectors if c.status == "online")
    offline_cols = total_cols - online_cols

    # Latest infrastructure metrics
    latest_metrics = db.query(InfrastructureMetric).order_by(InfrastructureMetric.recorded_at.desc()).limit(10).all()
    
    # Calculate health states distribution across collectors
    excellent = 0
    good = 0
    fair = 0
    poor = 0

    if latest_metrics:
        for m in latest_metrics:
            if m.health_state == "EXCELLENT": excellent += 1
            elif m.health_state == "GOOD": good += 1
            elif m.health_state == "FAIR": fair += 1
            elif m.health_state == "POOR": poor += 1
    else:
        excellent = max(0, online_cols)

    avg_cpu = round(sum(m.cpu_utilization_pct for m in latest_metrics) / max(1, len(latest_metrics)), 2) if latest_metrics else 45.2
    avg_mem = round(sum(m.memory_utilization_pct for m in latest_metrics) / max(1, len(latest_metrics)), 2) if latest_metrics else 54.8
    avg_disk = round(sum(m.disk_utilization_pct for m in latest_metrics) / max(1, len(latest_metrics)), 2) if latest_metrics else 62.4

    # Latest network metrics
    latest_net = db.query(NetworkMetric).order_by(NetworkMetric.recorded_at.desc()).limit(10).all()
    avg_lat = round(sum(n.latency_ms for n in latest_net) / max(1, len(latest_net)), 2) if latest_net else 18.5
    avg_loss = round(sum(n.packet_loss_pct for n in latest_net) / max(1, len(latest_net)), 2) if latest_net else 0.05

    active_incidents = db.query(Incident).filter(Incident.status.in_(["OPEN", "INVESTIGATING"])).count()
    critical_alerts = db.query(IncidentAlert).filter(IncidentAlert.severity == "CRITICAL").count()

    return {
        "total_collectors": total_cols,
        "online_collectors": online_cols,
        "offline_collectors": offline_cols,
        "total_monitored_systems": total_cols,
        "health_states": {
            "excellent": excellent,
            "good": good,
            "fair": fair,
            "poor": poor
        },
        "critical_alerts": critical_alerts,
        "active_incidents": active_incidents,
        "cpu_usage": avg_cpu,
        "memory_usage": avg_mem,
        "disk_usage": avg_disk,
        "network_latency": avg_lat,
        "packet_loss": avg_loss
    }

@router.get("/timeseries")
def get_metrics_timeseries(limit: int = 30, db: Session = Depends(get_db)):
    metrics = db.query(InfrastructureMetric).order_by(InfrastructureMetric.recorded_at.desc()).limit(limit).all()
    metrics.reverse()

    results = []
    for m in metrics:
        net = db.query(NetworkMetric).filter(NetworkMetric.payload_id == m.payload_id).first()
        results.append({
            "timestamp": m.recorded_at.strftime("%H:%M:%S"),
            "cpu": m.cpu_utilization_pct,
            "memory": m.memory_utilization_pct,
            "disk": m.disk_utilization_pct,
            "latency": net.latency_ms if net else 15.0,
            "packet_loss": net.packet_loss_pct if net else 0.0,
            "health_state": m.health_state
        })

    return results

