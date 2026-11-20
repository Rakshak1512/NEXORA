import asyncio
import json
import logging
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.models import (
    MonitoredWebsite, WebsiteCheckResult, Incident, Alert,
    Notification, utc_now
)
from .website_checker import execute_website_check
from .webhook_service import dispatch_webhook_event
from .email_service import send_email, get_styled_email_template
from ..websocket.manager import ws_manager

logger = logging.getLogger("cynera.scheduler")

class WebsiteMonitoringScheduler:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._scheduler_loop())
            logger.info("[Scheduler] Website monitoring background scheduler started.")

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("[Scheduler] Website monitoring background scheduler stopped.")

    async def _scheduler_loop(self):
        """Main polling loop running every 5 seconds to schedule due checks."""
        while self._running:
            try:
                await self.run_due_checks()
            except Exception as e:
                logger.error(f"[Scheduler Error] Exception in check loop: {e}")
            await asyncio.sleep(5)

    async def run_due_checks(self):
        """Identifies and checks all due websites across all active organizations."""
        db = SessionLocal()
        try:
            now = utc_now()
            websites = db.query(MonitoredWebsite).filter(
                MonitoredWebsite.is_active == True,
                MonitoredWebsite.is_verified == True
            ).all()

            for site in websites:
                should_check = False
                if site.last_checked_at is None:
                    should_check = True
                else:
                    last_check = site.last_checked_at
                    if last_check.tzinfo is None:
                        last_check = last_check.replace(tzinfo=datetime.timezone.utc)
                    elapsed = (now - last_check).total_seconds()
                    interval = site.monitoring_interval_seconds or 60
                    if elapsed >= interval:
                        should_check = True

                if should_check:
                    await self.check_single_website(site.id)
        finally:
            db.close()

    async def check_single_website(self, website_id: str):
        """Executes a check on a single website, recording metrics and handling failure/recovery confirmation."""
        db = SessionLocal()
        try:
            site = db.query(MonitoredWebsite).filter(MonitoredWebsite.id == website_id).first()
            if not site or not site.is_active:
                return

            try:
                expected_codes = json.loads(site.expected_status_codes or "[200, 201, 204, 301, 302]")
            except Exception:
                expected_codes = [200, 201, 204, 301, 302]

            # 1. Run live inspection
            result = await execute_website_check(
                url=site.url,
                expected_status_codes=expected_codes,
                timeout_sec=float(site.timeout_seconds or 10)
            )

            # 2. Failure Confirmation Logic (Double check before declaring DOWN)
            if not result["is_online"]:
                site.consecutive_failures += 1
                if site.consecutive_failures == 1:
                    # Quick retry to confirm
                    await asyncio.sleep(1.5)
                    retry_result = await execute_website_check(
                        url=site.url,
                        expected_status_codes=expected_codes,
                        timeout_sec=float(site.timeout_seconds or 10)
                    )
                    if retry_result["is_online"]:
                        result = retry_result
                        site.consecutive_failures = 0
            else:
                site.consecutive_failures = 0

            # 3. Record historical check result
            check_rec = WebsiteCheckResult(
                website_id=site.id,
                organization_id=site.organization_id,
                status=result["status"],
                status_code=result["status_code"],
                response_time_ms=result["response_time_ms"],
                dns_lookup_time_ms=result["dns_lookup_time_ms"],
                tls_handshake_time_ms=result["tls_handshake_time_ms"],
                dns_resolved_ips=json.dumps(result.get("dns_resolved_ips", [])),
                ssl_valid=result["ssl_valid"],
                ssl_days_remaining=result.get("ssl_days_remaining", 0),
                error_message=result.get("error_message"),
                check_location="SaaS Primary Cloud"
            )
            db.add(check_rec)

            previous_status = site.status
            new_status = result["status"]
            was_down = previous_status in ("DOWN", "TIMEOUT", "DNS_FAILURE", "TLS_FAILURE", "HTTP_ERROR")
            is_now_down = new_status in ("DOWN", "TIMEOUT", "DNS_FAILURE", "TLS_FAILURE", "HTTP_ERROR")

            # Update site fields
            site.status = new_status
            site.last_checked_at = utc_now()
            site.last_status_code = result["status_code"]
            site.last_response_time_ms = result["response_time_ms"]
            site.ssl_status = result["ssl_status"]
            site.ssl_days_remaining = result["ssl_days_remaining"]
            site.ssl_issuer = result.get("ssl_issuer")
            site.dns_status = result["dns_status"]
            site.dns_resolved_ips = json.dumps(result.get("dns_resolved_ips", []))
            site.dns_lookup_time_ms = result["dns_lookup_time_ms"]

            # 4. Handle OUTAGE Incident & Alert Creation
            if is_now_down and (not was_down or site.consecutive_failures >= 2):
                inc_num = f"INC-WEB-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Check for existing open incident for this website
                open_inc = db.query(Incident).filter(
                    Incident.tenant_id == site.organization_id,
                    Incident.title.like(f"%{site.name}%"),
                    Incident.status.in_(["OPEN", "INVESTIGATING", "ACKNOWLEDGED"])
                ).first()

                if not open_inc:
                    new_incident = Incident(
                        incident_number=inc_num,
                        tenant_id=site.organization_id,
                        collector_id="saas-synthetic-probe",
                        title=f"Website Outage: {site.name} is {new_status}",
                        description=f"Automated probe confirmed failure for {site.url}. Reason: {result.get('error_message') or 'Probe unreachable'}.",
                        severity="CRITICAL",
                        status="OPEN",
                        affected_components=json.dumps([site.name, "Public Web Gateway"]),
                        contributing_signals=json.dumps([f"Status: {new_status}", f"Code: {result['status_code']}"])
                    )
                    db.add(new_incident)
                    db.flush()

                    # Create Central Alert
                    alert = Alert(
                        organization_id=site.organization_id,
                        title=f"Website Down: {site.name}",
                        severity="CRITICAL",
                        category="website",
                        resource_name=site.name,
                        resource_id=site.id,
                        evidence=result.get("error_message") or f"HTTP {result['status_code']}",
                        status="ACTIVE",
                        incident_id=new_incident.id,
                        notification_sent=True
                    )
                    db.add(alert)

                    # Create Notification
                    notif = Notification(
                        organization_id=site.organization_id,
                        title=f"CRITICAL: {site.name} is DOWN",
                        message=f"{site.url} failed availability check with status '{new_status}'. Immediate investigation recommended.",
                        type="critical"
                    )
                    db.add(notif)

                    # Trigger Webhook
                    asyncio.create_task(dispatch_webhook_event(
                        db, site.organization_id, "website.down", {
                            "website_id": site.id,
                            "website_name": site.name,
                            "url": site.url,
                            "status": new_status,
                            "error": result.get("error_message")
                        }
                    ))

            # 5. Handle RECOVERY
            elif was_down and not is_now_down:
                # Resolve incident
                open_incs = db.query(Incident).filter(
                    Incident.tenant_id == site.organization_id,
                    Incident.title.like(f"%{site.name}%"),
                    Incident.status.in_(["OPEN", "INVESTIGATING", "ACKNOWLEDGED"])
                ).all()

                for inc in open_incs:
                    inc.status = "RESOLVED"
                    inc.resolved_at = utc_now()
                    inc.resolution_notes = f"Automatic recovery confirmed. Status returned to {new_status} with {result['response_time_ms']}ms latency."

                # Resolve Alerts
                db.query(Alert).filter(
                    Alert.organization_id == site.organization_id,
                    Alert.resource_id == site.id,
                    Alert.status == "ACTIVE"
                ).update({"status": "RESOLVED", "resolved_at": utc_now()})

                # Create Recovery Notification
                notif = Notification(
                    organization_id=site.organization_id,
                    title=f"RECOVERY: {site.name} is ONLINE",
                    message=f"{site.url} has recovered and is accepting connections normally ({result['response_time_ms']}ms).",
                    type="success"
                )
                db.add(notif)

                # Trigger Webhook
                asyncio.create_task(dispatch_webhook_event(
                    db, site.organization_id, "website.recovered", {
                        "website_id": site.id,
                        "website_name": site.name,
                        "url": site.url,
                        "status": "ONLINE",
                        "latency_ms": result["response_time_ms"]
                    }
                ))

            db.commit()

            # 6. Broadcast Real-Time Update over WebSocket
            asyncio.create_task(ws_manager.broadcast_json({
                "type": "WEBSITE_STATUS_UPDATE",
                "organization_id": site.organization_id,
                "payload": {
                    "website_id": site.id,
                    "name": site.name,
                    "url": site.url,
                    "status": site.status,
                    "response_time_ms": site.last_response_time_ms,
                    "status_code": site.last_status_code,
                    "ssl_days": site.ssl_days_remaining,
                    "checked_at": site.last_checked_at.isoformat()
                }
            }))

        except Exception as e:
            logger.error(f"[Scheduler] Error checking website {website_id}: {e}")
        finally:
            db.close()

website_scheduler = WebsiteMonitoringScheduler()

