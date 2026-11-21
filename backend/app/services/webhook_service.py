import hmac
import hashlib
import json
import time
import datetime
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.models import Webhook, WebhookDelivery, utc_now
from .ssrf_guard import validate_public_url

async def dispatch_webhook_event(
    db: Optional[Session] = None,
    organization_id: str = "",
    event_type: str = "",
    payload: Optional[Dict[str, Any]] = None
) -> int:
    """
    Finds all active webhooks for the organization subscribed to this event type,
    signs the payload with HMAC-SHA256, and dispatches it asynchronously.
    """
    from .. import database as db_module
    payload = payload or {}
    should_close = False
    session = db
    if session is None:
        active_session = getattr(db_module, "SessionLocal", None)
        if not active_session:
            return 0
        session = active_session()
        should_close = True

    try:
        webhooks = session.query(Webhook).filter(
            Webhook.organization_id == organization_id,
            Webhook.is_active == True
        ).all()

        dispatched_count = 0
        full_payload = {
            "event": event_type,
            "timestamp": utc_now().isoformat(),
            "organization_id": organization_id,
            "data": payload
        }
        payload_str = json.dumps(full_payload)

        for wh in webhooks:
            try:
                subscribed_events = json.loads(wh.events or '["*"]')
            except Exception:
                subscribed_events = ["*"]

            if "*" not in subscribed_events and event_type not in subscribed_events:
                continue

            # SSRF safety check on webhook URL
            is_safe, _, norm_url, _ = validate_public_url(wh.destination_url)
            if not is_safe:
                continue

            # Compute HMAC signature using webhook secret hash
            signature = hmac.new(
                wh.secret_hash.encode("utf-8"),
                payload_str.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "CYNERA-Webhook-Dispatcher/1.4",
                "X-Cynera-Signature": f"sha256={signature}",
                "X-Cynera-Event": event_type
            }

            delivery_status = "SUCCESS"
            status_code = None
            body_preview = None
            t0 = time.perf_counter()

            try:
                async with httpx.AsyncClient(timeout=6.0, verify=False) as client:
                    res = await client.post(norm_url, data=payload_str, headers=headers)
                    status_code = res.status_code
                    body_preview = res.text[:250] if res.text else None
                    if res.status_code >= 400:
                        delivery_status = "FAILED"
            except Exception as e:
                delivery_status = "FAILED"
                body_preview = str(e)[:250]

            exec_ms = round((time.perf_counter() - t0) * 1000, 2)

            # Update webhook last delivery
            wh.last_delivery_status = delivery_status
            wh.last_delivery_at = utc_now()

            # Log delivery
            delivery = WebhookDelivery(
                webhook_id=wh.id,
                event_type=event_type,
                payload_json=payload_str,
                response_status_code=status_code,
                response_body_preview=body_preview,
                execution_time_ms=exec_ms,
                status=delivery_status
            )
            session.add(delivery)
            dispatched_count += 1

        if dispatched_count > 0:
            session.commit()

        return dispatched_count
    finally:
        if should_close and session:
            session.close()

