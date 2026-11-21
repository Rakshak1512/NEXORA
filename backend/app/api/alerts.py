import uuid
import json
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from ..database import get_db
from ..models.models import Alert, Profile, utc_now
from ..auth.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/alerts", tags=["Alert Center"])

class AlertCreateRequest(BaseModel):
    title: str
    severity: Optional[str] = "MEDIUM"
    category: Optional[str] = "SYSTEM"
    message: Optional[str] = None
    resource_name: Optional[str] = None
    resource_id: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

@router.get("")
def list_alerts(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    alert_status: Optional[str] = None,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        return []

    query = db.query(Alert).filter(Alert.organization_id == current_user.organization_id)

    if category:
        query = query.filter(func.upper(Alert.category) == category.upper())
    if severity and severity.upper() != "ALL":
        normalized_severity = severity.upper()
        if normalized_severity == "WARNING":
            query = query.filter(func.upper(Alert.severity).in_(["WARNING", "HIGH", "MEDIUM"]))
        elif normalized_severity == "INFO":
            query = query.filter(func.upper(Alert.severity).in_(["INFO", "LOW"]))
        else:
            query = query.filter(func.upper(Alert.severity) == normalized_severity)
    if alert_status and alert_status.upper() != "ALL":
        query = query.filter(func.upper(Alert.status) == alert_status.upper())

    alerts = query.order_by(Alert.detected_at.desc() if hasattr(Alert, "detected_at") else Alert.created_at.desc()).limit(100).all()

    return [
        {
            "id": a.id,
            "title": a.title,
            "severity": ("critical" if (a.severity or "").upper() == "CRITICAL" else "warning" if (a.severity or "").upper() in ("WARNING", "HIGH", "MEDIUM") else "info"),
            "category": getattr(a, "category", "SYSTEM") or "SYSTEM",
            "message": getattr(a, "message", a.title) or a.title,
            "resource_name": getattr(a, "resource_name", None),
            "resource_id": getattr(a, "resource_id", getattr(a, "entity_id", None)),
            "entity_id": getattr(a, "entity_id", None),
            "evidence": getattr(a, "evidence", None),
            "status": (a.status or "active").lower(),
            "acknowledged": getattr(a, "acknowledged", False) or (a.status or "").upper() == "ACKNOWLEDGED",
            "created_at": (getattr(a, "detected_at", None) or getattr(a, "created_at", None) or utc_now()).isoformat()
        } for a in alerts
    ]

@router.get("/summary")
def get_alerts_summary(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        return {"total_active": 0, "critical": 0, "warning": 0, "info": 0, "total": 0}

    alerts = db.query(Alert).filter(Alert.organization_id == current_user.organization_id).all()
    active_alerts = [a for a in alerts if (a.status or "").upper() in ("ACTIVE", "OPEN", "WARNING", "CRITICAL")]
    critical = len([a for a in active_alerts if (a.severity or "").upper() == "CRITICAL"])
    warning = len([a for a in active_alerts if (a.severity or "").upper() in ("WARNING", "HIGH", "MEDIUM")])
    info = len([a for a in active_alerts if (a.severity or "").upper() in ("INFO", "LOW")])

    return {
        "total_active": len(active_alerts),
        "critical": critical,
        "warning": warning,
        "info": info,
        "total": len(alerts)
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_alert(
    data: AlertCreateRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization.")

    alert = Alert(
        id=f"alt-{uuid.uuid4().hex[:12]}",
        organization_id=current_user.organization_id,
        title=data.title,
        severity=data.severity.upper() if data.severity else "MEDIUM",
        category=data.category.lower() if data.category else "system",
        resource_name=data.resource_name or data.title,
        resource_id=data.resource_id or "res-01",
        evidence=json.dumps(data.evidence or {"message": data.message or data.title}),
        status="ACTIVE"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {
        "id": alert.id,
        "title": alert.title,
        "severity": alert.severity,
        "status": alert.status
    }

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.organization_id == current_user.organization_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.status = "ACKNOWLEDGED"
    db.commit()
    return {"status": "acknowledged", "alert_id": alert.id}

@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: str,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.organization_id == current_user.organization_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.status = "RESOLVED"
    alert.resolved_at = utc_now()
    db.commit()
    return {"status": "resolved", "alert_id": alert.id}
