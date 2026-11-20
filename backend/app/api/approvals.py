import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import RemediationApproval, Incident
from ..schemas.schemas import ApprovalActionRequest
from ..services.audit_service import audit_service

router = APIRouter(prefix="/approvals", tags=["Remediation Approvals"])

@router.get("")
def list_approvals(status: str = None, db: Session = Depends(get_db)):
    query = db.query(RemediationApproval).order_by(RemediationApproval.requested_at.desc())
    if status:
        query = query.filter(RemediationApproval.status == status)
    approvals = query.all()

    res = []
    for app in approvals:
        inc = db.query(Incident).filter(Incident.id == app.incident_id).first()
        res.append({
            "id": app.id,
            "incident_id": app.incident_id,
            "incident_number": inc.incident_number if inc else "N/A",
            "action_description": app.action_description,
            "target_component": app.target_component,
            "policy_evaluation_result": app.policy_evaluation_result,
            "status": app.status,
            "operator_comments": app.operator_comments,
            "simulated_execution_log": app.simulated_execution_log,
            "rollback_information": app.rollback_information,
            "requested_at": app.requested_at.isoformat() if app.requested_at else None,
            "actioned_at": app.actioned_at.isoformat() if app.actioned_at else None
        })
    return res

@router.post("/{approval_id}/action")
def take_approval_action(
    approval_id: str,
    data: ApprovalActionRequest,
    db: Session = Depends(get_db)
):
    app = db.query(RemediationApproval).filter(RemediationApproval.id == approval_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Remediation approval request not found")

    now_dt = datetime.datetime.now(datetime.timezone.utc)
    app.actioned_at = now_dt
    app.operator_comments = data.operator_comments

    if data.action == "APPROVE":
        app.status = "APPROVED"
        app.simulated_execution_log = (
            f"[{now_dt.strftime('%H:%M:%S UTC')}] Policy gate: VERIFIED_SAFE.\n"
            f"[{now_dt.strftime('%H:%M:%S UTC')}] Staged container recycle command dispatched.\n"
            f"[{now_dt.strftime('%H:%M:%S UTC')}] Pod 1/4 recycled: OK.\n"
            f"[{now_dt.strftime('%H:%M:%S UTC')}] Pod 2/4 recycled: OK.\n"
            f"[{now_dt.strftime('%H:%M:%S UTC')}] Pod 3/4 recycled: OK.\n"
            f"[{now_dt.strftime('%H:%M:%S UTC')}] Pod 4/4 recycled: OK.\n"
            f"[{now_dt.strftime('%H:%M:%S UTC')}] Target health confirmed. Incident auto-resolved."
        )
        # Update incident status to RESOLVED
        inc = db.query(Incident).filter(Incident.id == app.incident_id).first()
        if inc:
            inc.status = "RESOLVED"
            inc.resolved_at = now_dt
            inc.resolution_notes = f"Autonomous remediation executed following operator approval: {app.action_description}"

        audit_service.log(
            db=db,
            action="REMEDIATION_APPROVED",
            entity_type="RemediationApproval",
            entity_id=app.id,
            details={"action": app.action_description, "status": "APPROVED"}
        )

    elif data.action == "REJECT":
        app.status = "REJECTED"
        app.simulated_execution_log = f"[{now_dt.strftime('%H:%M:%S UTC')}] Remediation action was REJECTED by operator: {data.operator_comments}"
        audit_service.log(
            db=db,
            action="REMEDIATION_REJECTED",
            entity_type="RemediationApproval",
            entity_id=app.id,
            details={"reason": data.operator_comments}
        )

    db.commit()
    return {
        "id": app.id,
        "status": app.status,
        "simulated_execution_log": app.simulated_execution_log
    }

