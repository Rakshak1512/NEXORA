import json
import uuid
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.models import SystemAuditLog

class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> SystemAuditLog:
        audit_entry = SystemAuditLog(
            id=str(uuid.uuid4()),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            tenant_id=tenant_id,
            details=json.dumps(details or {}),
            ip_address=ip_address,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(audit_entry)
        db.commit()
        return audit_entry

audit_service = AuditService()

