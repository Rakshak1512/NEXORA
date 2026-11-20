from fastapi import Header, HTTPException, status
from ..config import settings

def verify_collector_credentials(
    authorization: str = Header(...),
    x_collector_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> str:
    """
    Validates collector bearer authentication token and presence of collector headers.
    Enforces that only authorized local collectors can post metadata to SaaS.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed Authorization header. Bearer token required."
        )

    token = authorization.replace("Bearer ", "").strip()
    if token != settings.COLLECTOR_AUTH_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid collector authentication secret."
        )

    if not x_collector_id or not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required X-Collector-ID or X-Tenant-ID headers."
        )

    return x_collector_id

