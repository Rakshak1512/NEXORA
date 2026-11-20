from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models.models import Collector

def verify_collector_credentials(
    authorization: str = Header(...),
    x_collector_id: str = Header(...),
    x_tenant_id: str = Header(...),
    db: Session = Depends(get_db)
) -> str:
    """Authenticates the collector credential and binds it to a registered collector/tenant."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed Authorization header.")
    token = authorization[len("Bearer "):].strip()
    configured = {
        value.strip() for value in (
            getattr(settings, "COLLECTOR_CREDENTIAL", ""),
            getattr(settings, "COLLECTOR_AUTH_SECRET", "")
        ) if value and value.strip()
    }
    if not configured or token not in configured:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid collector authentication secret.")
    if not x_collector_id or not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing collector or tenant identity headers.")
    collector = db.query(Collector).filter(
        Collector.id == x_collector_id,
        Collector.tenant_id == x_tenant_id
    ).first()
    if not collector:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Collector is not registered for the supplied tenant.")
    return collector.id
