import json
import uuid
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, HttpUrl

from ..database import get_db
from ..models.models import (
    MonitoredWebsite, WebsiteCheckResult, WebsiteEndpoint, Profile, utc_now
)
from ..auth.deps import get_current_user, RoleChecker
from ..services.ssrf_guard import validate_public_url
from ..services.website_checker import execute_website_check, verify_website_ownership
from ..services.website_scheduler import website_scheduler

router = APIRouter(prefix="/websites", tags=["Website Monitoring"])

# --- Pydantic Schemas ---
class WebsiteCreateRequest(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    monitoring_interval_seconds: Optional[int] = 60
    expected_status_codes: Optional[Any] = [200, 201, 204, 301, 302]
    timeout_seconds: Optional[int] = 10
    verification_method: Optional[str] = "dns_txt"

class WebsiteUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    monitoring_interval_seconds: Optional[int] = None
    expected_status_codes: Optional[Any] = None
    timeout_seconds: Optional[int] = None
    is_active: Optional[bool] = None

class EndpointCreateRequest(BaseModel):
    name: str
    endpoint_url: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = "GET"
    http_method: Optional[str] = None
    expected_status_code: Optional[int] = 200

# --- Endpoints ---
@router.get("")
def list_monitored_websites(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        return []

    websites = db.query(MonitoredWebsite).filter(
        MonitoredWebsite.organization_id == current_user.organization_id
    ).order_by(MonitoredWebsite.created_at.desc()).all()

    results = []
    for w in websites:
        try:
            expected_codes = json.loads(w.expected_status_codes or "[]")
        except Exception:
            expected_codes = [200]
        try:
            resolved_ips = json.loads(w.dns_resolved_ips or "[]")
        except Exception:
            resolved_ips = []

        results.append({
            "id": w.id,
            "name": w.name,
            "url": w.url,
            "description": w.description,
            "is_verified": w.is_verified,
            "verification_method": w.verification_method,
            "verification_token": w.verification_token,
            "status": w.status,
            "monitoring_interval_seconds": w.monitoring_interval_seconds,
            "expected_status_codes": expected_codes,
            "timeout_seconds": w.timeout_seconds,
            "is_active": w.is_active,
            "last_checked_at": w.last_checked_at.isoformat() if w.last_checked_at else None,
            "last_status_code": w.last_status_code,
            "last_response_time_ms": w.last_response_time_ms,
            "uptime_percentage_24h": w.uptime_percentage_24h,
            "ssl_status": w.ssl_status,
            "ssl_issuer": w.ssl_issuer,
            "ssl_days_remaining": w.ssl_days_remaining,
            "dns_status": w.dns_status,
            "dns_resolved_ips": resolved_ips,
            "created_at": w.created_at.isoformat() if w.created_at else None
        })

    return results

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_monitored_website(
    data: WebsiteCreateRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator", "Infrastructure Engineer"])),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization.")

    # 1. Strict SSRF Guard check
    is_safe, error_msg, norm_url, resolved_ips = validate_public_url(data.url)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSRF Protection Policy Violation: {error_msg}"
        )

    # 2. Check duplicate URL in same organization
    existing = db.query(MonitoredWebsite).filter(
        MonitoredWebsite.organization_id == current_user.organization_id,
        MonitoredWebsite.url == norm_url
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This website URL is already registered in your organization."
        )

    exp_codes = data.expected_status_codes
    if isinstance(exp_codes, str):
        try:
            exp_codes = [int(c.strip()) for c in exp_codes.split(",") if c.strip().isdigit()]
        except Exception:
            exp_codes = [200, 201, 204, 301, 302]
    elif not isinstance(exp_codes, list):
        exp_codes = [200, 201, 204, 301, 302]

    verification_token = f"cynera-verify-{uuid.uuid4().hex[:16]}"

    # 3. Create website record
    site = MonitoredWebsite(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        name=data.name.strip(),
        url=norm_url,
        description=data.description,
        is_verified=True, # Auto-verified for seamless self-service, ownership verification token available
        verification_method=data.verification_method or "dns_txt",
        verification_token=verification_token,
        status="PENDING",
        monitoring_interval_seconds=data.monitoring_interval_seconds or 60,
        expected_status_codes=json.dumps(exp_codes),
        timeout_seconds=data.timeout_seconds or 10,
        is_active=True,
        dns_resolved_ips=json.dumps(resolved_ips)
    )
    db.add(site)
    db.commit()
    db.refresh(site)

    # 4. Trigger initial inspection asynchronously
    asyncio_task = website_scheduler.check_single_website(site.id)
    import asyncio
    asyncio.create_task(asyncio_task)

    return {
        "id": site.id,
        "website_id": site.id,
        "name": site.name,
        "url": site.url,
        "verification_token": verification_token,
        "status": "created",
        "message": "Website registered successfully. Initial availability probe scheduled."
    }

@router.get("/{website_id}")
def get_website_details(
    website_id: str,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    site = db.query(MonitoredWebsite).filter(
        MonitoredWebsite.id == website_id,
        MonitoredWebsite.organization_id == current_user.organization_id
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="Monitored website not found.")

    # Recent check results (last 50 checks)
    checks = db.query(WebsiteCheckResult).filter(
        WebsiteCheckResult.website_id == website_id
    ).order_by(WebsiteCheckResult.recorded_at.desc()).limit(50).all()

    # Endpoints
    endpoints = db.query(WebsiteEndpoint).filter(
        WebsiteEndpoint.website_id == website_id
    ).all()

    # Compute uptime & average latency
    avg_latency = db.query(func.avg(WebsiteCheckResult.response_time_ms)).filter(
        WebsiteCheckResult.website_id == website_id
    ).scalar() or site.last_response_time_ms

    try:
        resolved_ips = json.loads(site.dns_resolved_ips or "[]")
    except Exception:
        resolved_ips = []

    try:
        expected_codes = json.loads(site.expected_status_codes or "[]")
    except Exception:
        expected_codes = [200]

    return {
        "id": site.id,
        "name": site.name,
        "url": site.url,
        "description": site.description,
        "is_verified": site.is_verified,
        "verification_token": site.verification_token,
        "verification_method": site.verification_method,
        "status": site.status,
        "monitoring_interval_seconds": site.monitoring_interval_seconds,
        "expected_status_codes": expected_codes,
        "timeout_seconds": site.timeout_seconds,
        "is_active": site.is_active,
        "last_checked_at": site.last_checked_at.isoformat() if site.last_checked_at else None,
        "last_status_code": site.last_status_code,
        "last_response_time_ms": site.last_response_time_ms,
        "average_response_time_ms": round(float(avg_latency), 2),
        "uptime_percentage_24h": site.uptime_percentage_24h,
        "ssl": {
            "status": site.ssl_status,
            "issuer": site.ssl_issuer,
            "days_remaining": site.ssl_days_remaining,
            "expiry_date": site.ssl_expiry_date.isoformat() if site.ssl_expiry_date else None
        },
        "dns": {
            "status": site.dns_status,
            "resolved_ips": resolved_ips,
            "lookup_time_ms": site.dns_lookup_time_ms
        },
        "endpoints": [
            {
                "id": ep.id,
                "name": ep.name,
                "endpoint_url": ep.endpoint_url,
                "method": ep.method,
                "expected_status_code": ep.expected_status_code,
                "last_status": ep.last_status,
                "last_latency_ms": ep.last_latency_ms
            } for ep in endpoints
        ],
        "recent_checks": [
            {
                "id": c.id,
                "status": c.status,
                "status_code": c.status_code,
                "response_time_ms": c.response_time_ms,
                "dns_lookup_time_ms": c.dns_lookup_time_ms,
                "tls_handshake_time_ms": c.tls_handshake_time_ms,
                "ssl_valid": c.ssl_valid,
                "error_message": c.error_message,
                "recorded_at": c.recorded_at.isoformat()
            } for c in checks
        ]
    }

@router.post("/{website_id}/check")
async def trigger_manual_check(
    website_id: str,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    site = db.query(MonitoredWebsite).filter(
        MonitoredWebsite.id == website_id,
        MonitoredWebsite.organization_id == current_user.organization_id
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="Monitored website not found.")

    await website_scheduler.check_single_website(site.id)

    # Refresh
    db.refresh(site)

    return {
        "status": "check_completed",
        "website_id": site.id,
        "new_status": site.status,
        "status_code": site.last_status_code,
        "response_time_ms": site.last_response_time_ms,
        "checked_at": site.last_checked_at.isoformat() if site.last_checked_at else None
    }

@router.post("/{website_id}/verify")
@router.post("/{website_id}/verify-ownership")
async def verify_domain(
    website_id: str,
    body: Optional[Dict[str, Any]] = None,
    method: str = "dns_txt",
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    site = db.query(MonitoredWebsite).filter(
        MonitoredWebsite.id == website_id,
        MonitoredWebsite.organization_id == current_user.organization_id
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    chosen_method = (body.get("method") if body else None) or method or "dns_txt"
    verified, msg = await verify_website_ownership(site.url, site.verification_token, method=chosen_method)
    if verified:
        site.is_verified = True
        site.verification_method = chosen_method
        db.commit()
        return {"verified": True, "status": "verified", "message": msg}
    else:
        raise HTTPException(status_code=400, detail=msg)

@router.patch("/{website_id}")
def update_website(
    website_id: str,
    data: WebsiteUpdateRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    site = db.query(MonitoredWebsite).filter(
        MonitoredWebsite.id == website_id,
        MonitoredWebsite.organization_id == current_user.organization_id
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    if data.name is not None:
        site.name = data.name.strip()
    if data.description is not None:
        site.description = data.description
    if data.monitoring_interval_seconds is not None:
        site.monitoring_interval_seconds = data.monitoring_interval_seconds
    if data.expected_status_codes is not None:
        site.expected_status_codes = json.dumps(data.expected_status_codes)
    if data.timeout_seconds is not None:
        site.timeout_seconds = data.timeout_seconds
    if data.is_active is not None:
        site.is_active = data.is_active

    site.updated_at = utc_now()
    db.commit()
    db.refresh(site)
    return {"status": "updated", "website_id": site.id}

@router.delete("/{website_id}")
def delete_website(
    website_id: str,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    site = db.query(MonitoredWebsite).filter(
        MonitoredWebsite.id == website_id,
        MonitoredWebsite.organization_id == current_user.organization_id
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    db.delete(site)
    db.commit()
    return {"status": "deleted", "message": "Website removed from monitoring."}

# --- Endpoints ---
@router.post("/{website_id}/endpoints", status_code=status.HTTP_201_CREATED)
def add_website_endpoint(
    website_id: str,
    data: EndpointCreateRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    site = db.query(MonitoredWebsite).filter(
        MonitoredWebsite.id == website_id,
        MonitoredWebsite.organization_id == current_user.organization_id
    ).first()

    if not site:
        raise HTTPException(status_code=404, detail="Website not found.")

    # SSRF validation on endpoint URL
    raw_ep = data.endpoint_url or data.path or "/health"
    if raw_ep.startswith("/"):
        raw_ep = site.url.rstrip("/") + raw_ep
    is_safe, error_msg, norm_url, _ = validate_public_url(raw_ep)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"SSRF Protection: {error_msg}")

    endpoint = WebsiteEndpoint(
        website_id=site.id,
        name=data.name.strip(),
        endpoint_url=norm_url,
        method=data.method or data.http_method or "GET",
        expected_status_code=data.expected_status_code or 200,
        is_active=True
    )
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)

    return {
        "status": "created",
        "id": endpoint.id,
        "endpoint_id": endpoint.id,
        "name": endpoint.name,
        "endpoint_url": endpoint.endpoint_url,
        "path": endpoint.endpoint_url.replace(site.url, "") or "/"
    }

@router.delete("/{website_id}/endpoints/{endpoint_id}")
def delete_website_endpoint(
    website_id: str,
    endpoint_id: str,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    ep = db.query(WebsiteEndpoint).filter(
        WebsiteEndpoint.id == endpoint_id,
        WebsiteEndpoint.website_id == website_id
    ).first()

    if not ep:
        raise HTTPException(status_code=404, detail="Endpoint not found.")

    db.delete(ep)
    db.commit()
    return {"status": "deleted"}
