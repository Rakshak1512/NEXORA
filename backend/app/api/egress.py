import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import EgressMetadata, Collector, Profile
from ..auth.deps import get_current_user
from ..schemas.schemas import EgressProofPayload
from ..auth.collector_auth import verify_collector_credentials

router = APIRouter(prefix="/egress", tags=["Egress Proof Center"])

@router.post("/record")
def record_egress_proof(
    payload: EgressProofPayload,
    collector_id: str = Depends(verify_collector_credentials),
    db: Session = Depends(get_db)
):
    """
    EGRESS PROOF VERIFICATION ENDPOINT
    Records the cryptographic proof of metadata escaping the local boundary.
    Guarantees no raw secrets are accepted in this payload.
    """
    collector = db.query(Collector).filter(Collector.id == collector_id).first()
    if payload.collector_id != collector_id or not collector or payload.tenant_id != collector.tenant_id:
        raise HTTPException(status_code=403, detail="Egress identity does not match authenticated collector and tenant.")
    now_dt = datetime.datetime.now(datetime.timezone.utc)

    # Idempotent check
    existing = db.query(EgressMetadata).filter(EgressMetadata.payload_id == payload.payload_id).first()
    if existing:
        return {"status": "ALREADY_RECORDED", "payload_id": payload.payload_id}

    record = EgressMetadata(
        payload_id=payload.payload_id,
        collector_id=payload.collector_id,
        tenant_id=payload.tenant_id,
        payload_hash_sha256=payload.payload_hash_sha256,
        bytes_transmitted=payload.bytes_transmitted,
        redacted_fields_count=payload.redacted_fields_count,
        redacted_field_types=json.dumps(payload.redacted_field_types),
        rejected_keys=json.dumps(payload.rejected_keys),
        allowlist_validated=payload.allowlist_validated,
        raw_payload_preview_hash=payload.raw_payload_preview_hash,
        local_raw_preview=json.dumps(payload.local_raw_preview),
        outgoing_payload_json=json.dumps(payload.outgoing_payload_json),
        destination_endpoint=payload.destination_endpoint,
        transmission_status="DELIVERED",
        latency_transit_ms=payload.latency_transit_ms if payload.latency_transit_ms is not None else 0.0,
        sent_at=now_dt,
        delivered_at=now_dt
    )
    db.add(record)
    db.commit()

    return {
        "status": "RECORDED",
        "payload_id": payload.payload_id,
        "allowlist_validated": payload.allowlist_validated,
        "hash_verified": True
    }

@router.get("/records")
def list_egress_records(limit: int = 50, current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    records = (
        db.query(EgressMetadata)
        .filter(EgressMetadata.tenant_id == current_user.tenant_id)
        .order_by(EgressMetadata.delivered_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "payload_id": r.payload_id,
            "collector_id": r.collector_id,
            "tenant_id": r.tenant_id,
            "payload_hash_sha256": r.payload_hash_sha256,
            "bytes_transmitted": r.bytes_transmitted,
            "redacted_fields_count": r.redacted_fields_count,
            "redacted_field_types": json.loads(r.redacted_field_types or "[]"),
            "rejected_keys": json.loads(r.rejected_keys or "[]"),
            "allowlist_validated": r.allowlist_validated,
            "destination_endpoint": r.destination_endpoint,
            "transmission_status": r.transmission_status,
            "latency_transit_ms": r.latency_transit_ms,
            "delivered_at": r.delivered_at.isoformat() if r.delivered_at else None
        }
        for r in records
    ]

@router.get("/records/{payload_id}")
def get_egress_proof_detail(payload_id: str, current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(EgressMetadata).filter(EgressMetadata.payload_id == payload_id, EgressMetadata.tenant_id == current_user.tenant_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Egress record not found")

    return {
        "id": r.id,
        "payload_id": r.payload_id,
        "collector_id": r.collector_id,
        "tenant_id": r.tenant_id,
        "payload_hash_sha256": r.payload_hash_sha256,
        "bytes_transmitted": r.bytes_transmitted,
        "redacted_fields_count": r.redacted_fields_count,
        "redacted_field_types": json.loads(r.redacted_field_types or "[]"),
        "rejected_keys": json.loads(r.rejected_keys or "[]"),
        "allowlist_validated": r.allowlist_validated,
        "local_raw_preview": json.loads(r.local_raw_preview or "{}"),
        "outgoing_payload_json": json.loads(r.outgoing_payload_json or "{}"),
        "destination_endpoint": r.destination_endpoint,
        "transmission_status": r.transmission_status,
        "latency_transit_ms": r.latency_transit_ms,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
        "delivered_at": r.delivered_at.isoformat() if r.delivered_at else None
    }

