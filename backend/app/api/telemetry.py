from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.schemas import TelemetryIngestPayload
from ..auth.collector_auth import verify_collector_credentials
from ..services.telemetry_service import telemetry_service
from ..models.models import InfrastructureMetric, NetworkMetric, SecuritySummary

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.post("/ingest")
async def ingest_telemetry(
    payload: TelemetryIngestPayload,
    collector_id: str = Depends(verify_collector_credentials),
    db: Session = Depends(get_db)
):
    """
    INGESTION PERIMETER (Tier 2 SaaS)
    Accepts only approved metadata payloads.
    Guarantees idempotency and duplicate elimination via payload_id.
    """
    success, message, result = await telemetry_service.process_ingestion(db, payload)
    return {
        "success": success,
        "message": message,
        "result": result
    }

@router.get("/latest")
def get_latest_telemetry(collector_id: str = None, db: Session = Depends(get_db)):
    query = db.query(InfrastructureMetric).order_by(InfrastructureMetric.recorded_at.desc())
    if collector_id:
        query = query.filter(InfrastructureMetric.collector_id == collector_id)
    latest = query.first()
    if not latest:
        return {"data": None}

    net = db.query(NetworkMetric).filter(NetworkMetric.payload_id == latest.payload_id).first()
    sec = db.query(SecuritySummary).filter(SecuritySummary.payload_id == latest.payload_id).first()

    return {
        "payload_id": latest.payload_id,
        "collector_id": latest.collector_id,
        "cpu_utilization_pct": latest.cpu_utilization_pct,
        "memory_utilization_pct": latest.memory_utilization_pct,
        "disk_utilization_pct": latest.disk_utilization_pct,
        "health_state": latest.health_state,
        "health_reason": latest.health_reason,
        "latency_ms": net.latency_ms if net else 0.0,
        "packet_loss_pct": net.packet_loss_pct if net else 0.0,
        "failed_login_count": sec.failed_login_count if sec else 0,
        "security_severity": sec.security_event_severity if sec else "LOW",
        "recorded_at": latest.recorded_at.isoformat()
    }

