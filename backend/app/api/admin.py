from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import Profile, Organization, Tenant, OrganizationMembership
from ..auth.deps import RoleChecker
from ..auth.jwt import get_password_hash

router = APIRouter(prefix="/admin", tags=["Super Administrator"])
MANAGED_ROLES = {"Admin", "Organization Owner", "Security Analyst", "Infrastructure Engineer", "Operator", "Viewer"}

class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    role: str = "Admin"
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None

class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/users")
def list_users(admin: Profile = Depends(RoleChecker(["Super Administrator"])), db: Session = Depends(get_db)):
    users = db.query(Profile).order_by(Profile.created_at.desc()).all()
    return [{
        "id": u.id, "email": u.email, "full_name": u.full_name,
        "role": u.role, "organization_id": u.organization_id, "tenant_id": u.tenant_id,
        "is_active": u.is_active, "is_verified": u.is_verified,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users]

@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_managed_user(data: AdminUserCreate, admin: Profile = Depends(RoleChecker(["Super Administrator"])), db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    if data.role not in MANAGED_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported managed role.")
    if db.query(Profile).filter(Profile.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    if data.organization_id and not db.query(Organization).filter(Organization.id == data.organization_id).first():
        raise HTTPException(status_code=400, detail="Organization not found.")
    if data.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == data.tenant_id).first()
        if not tenant or (data.organization_id and tenant.organization_id != data.organization_id):
            raise HTTPException(status_code=400, detail="Tenant does not belong to selected organization.")
    user = Profile(email=email, full_name=data.full_name.strip(), password_hash=get_password_hash(data.password),
                   role=data.role, organization_id=data.organization_id, tenant_id=data.tenant_id,
                   is_active=True, is_verified=True)
    db.add(user)
    db.flush()
    if data.organization_id:
        db.add(OrganizationMembership(organization_id=data.organization_id, user_id=user.id,
                                      role=data.role, is_active=True, invited_by=admin.id))
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role,
            "is_active": user.is_active, "is_verified": user.is_verified}

@router.patch("/users/{user_id}")
def update_managed_user(user_id: str, data: AdminUserUpdate,
                        admin: Profile = Depends(RoleChecker(["Super Administrator"])), db: Session = Depends(get_db)):
    user = db.query(Profile).filter(Profile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id or user.role == "Super Administrator":
        raise HTTPException(status_code=403, detail="Super Administrator accounts cannot be modified here.")
    if data.role is not None:
        if data.role not in MANAGED_ROLES:
            raise HTTPException(status_code=400, detail="Unsupported managed role.")
        user.role = data.role
        membership = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == user.organization_id
        ).first()
        if membership:
            membership.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
        db.query(OrganizationMembership).filter(OrganizationMembership.user_id == user.id).update(
            {"is_active": data.is_active}
        )
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}
