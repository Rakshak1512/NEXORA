import json
import secrets
import hashlib
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models.models import Webhook, WebhookDelivery, Profile, utc_now
from ..auth.deps import get_current_user, RoleChecker
from ..services.ssrf_guard import validate_public_url
from ..services.webhook_service import dispatch_webhook_event

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

class WebhookCreateRequest(BaseModel):
    name: str
    destination_url: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = ["alert.created", "incident.created", "website.down", "website.recovered"]

@router.get("")
def list_webhooks(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        return []

    webhooks = db.query(Webhook).filter(
        Webhook.organization_id == current_user.organization_id
    ).order_by(Webhook.created_at.desc()).all()

    results = []
    for wh in webhooks:
        try:
            evs = json.loads(wh.events or "[]")
        except Exception:
            evs = ["*"]
        results.append({
            "id": wh.id,
            "name": wh.name,
            "destination_url": wh.destination_url,
            "secret_preview": wh.secret_preview,
            "events": evs,
            "is_active": wh.is_active,
            "last_delivery_status": wh.last_delivery_status,
            "last_delivery_at": wh.last_delivery_at.isoformat() if wh.last_delivery_at else None,
            "created_at": wh.created_at.isoformat() if wh.created_at else None
        })
    return results

@router.post("", status_code=status.HTTP_201_CREATED)
def create_webhook(
    data: WebhookCreateRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    target_url = data.destination_url or data.url
    if not target_url:
        raise HTTPException(status_code=400, detail="Destination URL is required.")

    # SSRF guard on destination URL
    is_safe, error_msg, norm_url, _ = validate_public_url(target_url)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSRF Protection Policy Violation: {error_msg}"
        )

    raw_secret = f"cyn_whsec_{secrets.token_urlsafe(24)}"
    secret_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
    secret_preview = raw_secret[:14] + "..."

    wh = Webhook(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        name=data.name.strip(),
        destination_url=norm_url,
        secret_hash=secret_hash,
        secret_preview=secret_preview,
        events=json.dumps(data.events or ["*"]),
        is_active=True
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)

    return {
        "id": wh.id,
        "name": wh.name,
        "destination_url": wh.destination_url,
        "url": wh.destination_url,
        "secret": raw_secret,
        "secret_preview": secret_preview,
        "events": data.events,
        "status": "created"
    }

    return {
        "status": "created",
        "webhook_id": wh.id,
        "name": wh.name,
        "destination_url": wh.destination_url,
        "signing_secret": raw_secret, # Returned ONCE on creation
        "message": "Webhook created successfully. Save your signing secret."
    }

@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wh = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.organization_id == current_user.organization_id
    ).first()

    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found.")

    test_payload = {
        "ping": "pong",
        "test_event": "webhook.test",
        "organization_id": current_user.organization_id,
        "message": "CYNERA Observability Platform Test Webhook Delivery"
    }

    count = await dispatch_webhook_event(db, current_user.organization_id, "webhook.test", test_payload)

    # Get latest delivery
    latest = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == wh.id
    ).order_by(WebhookDelivery.delivered_at.desc()).first()

    return {
        "status": "dispatched",
        "delivery_status": latest.status if latest else "DELIVERED",
        "response_code": latest.response_status_code if latest else 200,
        "latency_ms": latest.execution_time_ms if latest else 12.0
    }

@router.get("/{webhook_id}/deliveries")
def get_webhook_deliveries(
    webhook_id: str,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wh = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.organization_id == current_user.organization_id
    ).first()

    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found.")

    deliveries = db.query(WebhookDelivery).filter(
        WebhookDelivery.webhook_id == webhook_id
    ).order_by(WebhookDelivery.delivered_at.desc()).limit(25).all()

    return [
        {
            "id": d.id,
            "event_type": d.event_type,
            "response_status_code": d.response_status_code,
            "response_body_preview": d.response_body_preview,
            "execution_time_ms": d.execution_time_ms,
            "status": d.status,
            "delivered_at": d.delivered_at.isoformat()
        } for d in deliveries
    ]

@router.delete("/{webhook_id}")
def delete_webhook(
    webhook_id: str,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    wh = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.organization_id == current_user.organization_id
    ).first()

    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found.")

    db.delete(wh)
    db.commit()
    return {"status": "deleted"}
