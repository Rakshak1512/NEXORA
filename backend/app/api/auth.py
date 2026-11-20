import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import Profile, Organization, Tenant
from ..schemas.schemas import UserLogin, UserRegister, TokenResponse, UserProfileResponse
from ..auth.jwt import verify_password, get_password_hash, create_access_token
from ..auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register_user(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(Profile).filter(Profile.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Resolve default organization and tenant
    org = db.query(Organization).first()
    org_id = data.organization_id or (org.id if org else None)

    tenant = db.query(Tenant).first()
    tenant_id = data.tenant_id or (tenant.id if tenant else None)

    hashed_pw = get_password_hash(data.password)
    user = Profile(
        email=data.email,
        password_hash=hashed_pw,
        full_name=data.full_name,
        role=data.role or "Operator",
        organization_id=org_id,
        tenant_id=tenant_id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": user.organization_id,
            "tenant_id": user.tenant_id
        }
    }

@router.post("/login", response_model=TokenResponse)
def login_user(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(Profile).filter(Profile.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact an Administrator."
        )

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": user.organization_id,
            "tenant_id": user.tenant_id
        }
    }

@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: Profile = Depends(get_current_user)):
    return current_user

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(Profile).filter(Profile.email == email).first()
    return {"message": "If the account exists, password reset instructions have been generated."}

