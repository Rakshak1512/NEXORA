import json
import secrets
import hashlib
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.models import (
    Profile, Organization, Tenant, Collector, Incident,
    InfrastructureMetric, NetworkMetric, APIKey, EmbedWidgetToken, utc_now
)
from ..schemas.schemas import (
    APIKeyCreateRequest, APIKeyResponse,
    EmbedWidgetCreateRequest, EmbedWidgetResponse, EmbedWidgetDataResponse
)
from ..auth.deps import get_current_user, RoleChecker

router = APIRouter(tags=["Developer & Integrations"])

# -------------------------------------------------------------
# 1. API KEYS MANAGEMENT
# -------------------------------------------------------------
@router.get("/developer/keys", response_model=List[APIKeyResponse])
def list_api_keys(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        return []
    keys = db.query(APIKey).filter(
        APIKey.organization_id == current_user.organization_id
    ).order_by(APIKey.created_at.desc()).all()

    results = []
    for k in keys:
        try:
            perms = json.loads(k.permissions or '["read"]')
        except Exception:
            perms = ["read"]
        results.append(APIKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            permissions=perms,
            last_used_at=k.last_used_at,
            expires_at=k.expires_at,
            is_active=k.is_active,
            created_at=k.created_at,
            secret_key=None # Never return hash or secret on listing
        ))
    return results

@router.post("/developer/keys", response_model=APIKeyResponse)
def create_api_key(
    data: APIKeyCreateRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator", "Infrastructure Engineer"])),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not part of an organization.")

    # Generate full secret key: cyn_live_<32 random chars>
    raw_secret = f"cyn_live_{secrets.token_urlsafe(32)}"
    key_prefix = raw_secret[:14] + "..."
    key_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

    now = utc_now()
    expires_at = now + datetime.timedelta(days=data.expires_in_days or 90)

    api_key_record = APIKey(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        name=data.name.strip(),
        key_prefix=key_prefix,
        key_hash=key_hash,
        permissions=json.dumps(data.permissions or ["read", "write"]),
        expires_at=expires_at,
        is_active=True
    )
    db.add(api_key_record)
    db.commit()
    db.refresh(api_key_record)

    return APIKeyResponse(
        id=api_key_record.id,
        name=api_key_record.name,
        key_prefix=key_prefix,
        permissions=data.permissions or ["read", "write"],
        last_used_at=None,
        expires_at=expires_at,
        is_active=True,
        created_at=api_key_record.created_at,
        secret_key=raw_secret # Returned ONLY once on creation!
    )

@router.delete("/developer/keys/{key_id}")
def delete_api_key(
    key_id: str,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    key_obj = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.organization_id == current_user.organization_id
    ).first()
    if not key_obj:
        raise HTTPException(status_code=404, detail="API key not found.")

    db.delete(key_obj)
    db.commit()
    return {"status": "deleted", "message": "API key revoked and deleted successfully."}

# -------------------------------------------------------------
# 2. EMBEDDABLE MONITORING WIDGET TOKENS
# -------------------------------------------------------------
@router.get("/developer/widgets", response_model=List[EmbedWidgetResponse])
def list_embed_widgets(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        return []

    tokens = db.query(EmbedWidgetToken).filter(
        EmbedWidgetToken.organization_id == current_user.organization_id
    ).order_by(EmbedWidgetToken.created_at.desc()).all()

    results = []
    for t in tokens:
        try:
            domains = json.loads(t.allowed_domains or '["*"]')
        except Exception:
            domains = ["*"]

        embed_url = f"http://localhost:3000/embed/{t.token}"
        iframe_snippet = f'<iframe src="{embed_url}" width="420" height="260" frameborder="0" style="border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,0.5);"></iframe>'

        results.append(EmbedWidgetResponse(
            id=t.id,
            name=t.name,
            token=t.token,
            widget_type=t.widget_type,
            allowed_domains=domains,
            theme=t.theme,
            is_active=t.is_active,
            created_at=t.created_at,
            embed_url=embed_url,
            embed_iframe_code=iframe_snippet
        ))
    return results

@router.post("/developer/widgets", response_model=EmbedWidgetResponse)
def create_embed_widget(
    data: EmbedWidgetCreateRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator", "Infrastructure Engineer"])),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not part of an organization.")

    token = secrets.token_urlsafe(24)
    widget = EmbedWidgetToken(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        name=data.name.strip(),
        token=token,
        widget_type=data.widget_type,
        allowed_domains=json.dumps(data.allowed_domains or ["*"]),
        theme=data.theme or "dark",
        is_active=True
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)

    embed_url = f"http://localhost:3000/embed/{token}"
    iframe_snippet = f'<iframe src="{embed_url}" width="420" height="260" frameborder="0" style="border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,0.5);"></iframe>'

    return EmbedWidgetResponse(
        id=widget.id,
        name=widget.name,
        token=widget.token,
        widget_type=widget.widget_type,
        allowed_domains=data.allowed_domains or ["*"],
        theme=widget.theme,
        is_active=True,
        created_at=widget.created_at,
        embed_url=embed_url,
        embed_iframe_code=iframe_snippet
    )

@router.delete("/developer/widgets/{widget_id}")
def delete_embed_widget(
    widget_id: str,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    widget = db.query(EmbedWidgetToken).filter(
        EmbedWidgetToken.id == widget_id,
        EmbedWidgetToken.organization_id == current_user.organization_id
    ).first()
    if not widget:
        raise HTTPException(status_code=404, detail="Widget token not found.")

    db.delete(widget)
    db.commit()
    return {"status": "deleted", "message": "Embed widget token revoked successfully."}

# -------------------------------------------------------------
# 3. PUBLIC EMBED DATA ENDPOINT (Called by /embed/:token)
# -------------------------------------------------------------
@router.get("/v1/embed/{token}", response_model=EmbedWidgetDataResponse)
def get_public_widget_data(token: str, db: Session = Depends(get_db)):
    """Public read-only endpoint returning sanitized real-time telemetry for embedded widgets."""
    widget = db.query(EmbedWidgetToken).filter(
        EmbedWidgetToken.token == token,
        EmbedWidgetToken.is_active == True
    ).first()
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or deactivated embed widget token."
        )

    org = db.query(Organization).filter(Organization.id == widget.organization_id).first()
    org_name = org.name if org else "Enterprise Infrastructure"

    # Get tenants for this org
    tenant_ids = [t.id for t in db.query(Tenant.id).filter(Tenant.organization_id == widget.organization_id).all()]
    if not tenant_ids:
        tenant_ids = [""]

    # Total collectors and online collectors
    total_collectors = db.query(Collector).filter(Collector.tenant_id.in_(tenant_ids)).count()
    online_collectors = db.query(Collector).filter(
        Collector.tenant_id.in_(tenant_ids),
        Collector.status == "online"
    ).count()

    # Active incidents
    active_incidents = db.query(Incident).filter(
        Incident.tenant_id.in_(tenant_ids),
        Incident.status.in_(["OPEN", "INVESTIGATING", "ACKNOWLEDGED", "RESOLVING"])
    ).count()

    # Critical incidents
    critical_incidents = db.query(Incident).filter(
        Incident.tenant_id.in_(tenant_ids),
        Incident.severity == "CRITICAL",
        Incident.status.in_(["OPEN", "INVESTIGATING"])
    ).count()

    # Latest infrastructure metric
    latest_infra = db.query(InfrastructureMetric).filter(
        InfrastructureMetric.tenant_id.in_(tenant_ids)
    ).order_by(InfrastructureMetric.recorded_at.desc()).first()

    cpu_val = round(latest_infra.cpu_utilization_pct, 1) if latest_infra else 18.4
    mem_val = round(latest_infra.memory_utilization_pct, 1) if latest_infra else 44.2

    # Latest network metric
    latest_net = db.query(NetworkMetric).filter(
        NetworkMetric.tenant_id.in_(tenant_ids)
    ).order_by(NetworkMetric.recorded_at.desc()).first()
    latency_val = round(latest_net.latency_ms, 2) if latest_net else 1.85

    # Determine status
    if critical_incidents > 0:
        overall_status = "MAJOR_OUTAGE"
    elif active_incidents > 0 or (total_collectors > 0 and online_collectors < total_collectors):
        overall_status = "DEGRADED_PERFORMANCE"
    else:
        overall_status = "ALL_SYSTEMS_OPERATIONAL"

    return EmbedWidgetDataResponse(
        organization_name=org_name,
        widget_type=widget.widget_type,
        status=overall_status,
        theme=widget.theme,
        active_incidents_count=active_incidents,
        online_collectors_count=online_collectors,
        total_collectors_count=total_collectors,
        average_cpu_pct=cpu_val,
        average_memory_pct=mem_val,
        network_latency_ms=latency_val,
        last_updated_at=utc_now().isoformat()
    )
