import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import Incident, IncidentAlert, AIRecommendation
from ..schemas.schemas import IncidentUpdateRequest

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("")
def list_incidents(status: str = None, severity: str = None, db: Session = Depends(get_db)):
    query = db.query(Incident).order_by(Incident.created_at.desc())
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)

    incidents = query.all()
    res = []
    for inc in incidents:
        rec = db.query(AIRecommendation).filter(AIRecommendation.incident_id == inc.id).first()
        res.append({
            "id": inc.id,
            "incident_number": inc.incident_number,
            "tenant_id": inc.tenant_id,
            "collector_id": inc.collector_id,
            "title": inc.title,
            "description": inc.description,
            "severity": inc.severity,
            "status": inc.status,
            "affected_components": json.loads(inc.affected_components or "[]"),
            "contributing_signals": json.loads(inc.contributing_signals or "[]"),
            "correlation_reason": inc.correlation_reason,
            "resolution_notes": inc.resolution_notes,
            "has_ai_recommendation": rec is not None,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None
        })
    return res

@router.get("/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    rec = db.query(AIRecommendation).filter(AIRecommendation.incident_id == inc.id).first()
    alerts = db.query(IncidentAlert).filter(IncidentAlert.incident_id == inc.id).all()

    return {
        "id": inc.id,
        "incident_number": inc.incident_number,
        "tenant_id": inc.tenant_id,
        "collector_id": inc.collector_id,
        "title": inc.title,
        "description": inc.description,
        "severity": inc.severity,
        "status": inc.status,
        "affected_components": json.loads(inc.affected_components or "[]"),
        "contributing_signals": json.loads(inc.contributing_signals or "[]"),
        "correlation_reason": inc.correlation_reason,
        "resolution_notes": inc.resolution_notes,
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
        "recommendation": {
            "id": rec.id,
            "detected_anomaly": rec.detected_anomaly,
            "baseline_comparison": rec.baseline_comparison,
            "confidence_score": rec.confidence_score,
            "possible_root_cause": rec.possible_root_cause,
            "recommended_investigation": rec.recommended_investigation,
            "suggested_action": rec.suggested_action,
            "suggested_action_type": rec.suggested_action_type,
            "rollback_plan": rec.rollback_plan
        } if rec else None,
        "related_alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "metric_value": a.metric_value,
                "threshold_value": a.threshold_value,
                "detected_at": a.detected_at.isoformat()
            }
            for a in alerts
        ]
    }

@router.patch("/{incident_id}")
def update_incident(incident_id: str, data: IncidentUpdateRequest, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    inc.status = data.status
    if data.assigned_to:
        inc.assigned_to = data.assigned_to
    if data.resolution_notes:
        inc.resolution_notes = data.resolution_notes
    if data.status == "RESOLVED":
        inc.resolved_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    return {"message": "Incident status updated successfully", "status": inc.status}

