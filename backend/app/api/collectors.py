import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import Collector, CollectorHeartbeat, Profile
from ..auth.deps import get_current_user
from ..schemas.schemas import HeartbeatPayload
from ..auth.collector_auth import verify_collector_credentials
from ..services.health_evaluator import check_stale_collectors

router = APIRouter(prefix="/collectors", tags=["Collectors"])

@router.get("")
def list_collectors(current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    # Run stale check before listing
    check_stale_collectors(db)
    collectors = db.query(Collector).filter(Collector.tenant_id == current_user.tenant_id).all()
    return [
        {
            "id": c.id,
            "tenant_id": c.tenant_id,
            "name": c.name,
            "hostname": c.hostname,
            "ip_address_pseudonym": c.ip_address_pseudonym,
            "version": c.version,
            "status": c.status,
            "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None,
            "collection_interval_seconds": c.collection_interval_seconds
        }
        for c in collectors
    ]

@router.get("/{collector_id}")
def get_collector(collector_id: str, current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(Collector).filter(Collector.id == collector_id, Collector.tenant_id == current_user.tenant_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Collector not found")
    return {
        "id": c.id,
        "name": c.name,
        "status": c.status,
        "hostname": c.hostname,
        "version": c.version,
        "last_seen_at": c.last_seen_at.isoformat() if c.last_seen_at else None
    }

@router.post("/heartbeat")
def receive_heartbeat(
    payload: HeartbeatPayload,
    collector_id: str = Depends(verify_collector_credentials),
    db: Session = Depends(get_db)
):
    if payload.collector_id != collector_id:
        raise HTTPException(status_code=403, detail="Heartbeat collector identity does not match authenticated collector.")
    col = db.query(Collector).filter(Collector.id == collector_id).first()
    if not col or col.tenant_id != payload.tenant_id:
        raise HTTPException(status_code=403, detail="Heartbeat tenant does not match registered collector.")
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    col.status = payload.status
    col.last_seen_at = now_dt

    hb_record = CollectorHeartbeat(
        collector_id=payload.collector_id,
        status=payload.status,
        uptime_seconds=payload.uptime_seconds,
        cpu_usage_pct=payload.cpu_usage_pct,
        memory_usage_mb=payload.memory_usage_mb,
        queue_backlog_count=payload.queue_backlog_count,
        recorded_at=now_dt
    )
    db.add(hb_record)
    db.commit()

    return {"status": "ACKNOWLEDGED", "collector_id": payload.collector_id, "timestamp": now_dt.isoformat()}

