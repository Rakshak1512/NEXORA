import re
import json
import secrets
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import (
    Profile, Organization, Tenant, OrganizationMembership,
    Collector, Notification, MonitoredWebsite, utc_now
)
from ..schemas.schemas import (
    UserLogin, UserRegister, OrganizationRegisterRequest,
    OTPVerifyRequest, OTPResendRequest, ForgotPasswordRequest,
    PasswordResetRequest, TokenResponse, UserProfileResponse
)
from ..auth.jwt import verify_password, get_password_hash, create_access_token
from ..auth.deps import get_current_user
from ..auth.otp import create_otp_challenge, verify_otp_challenge, resend_otp_challenge
from ..services.email_service import (
    send_signup_otp, send_login_2fa_otp, send_password_reset_otp
)
from ..services.ssrf_guard import validate_public_url

router = APIRouter(prefix="/auth", tags=["Authentication"])

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-') or "org"

@router.post("/register-org")
def register_organization(data: OrganizationRegisterRequest, db: Session = Depends(get_db)):
    """Initiates self-registration for an independent organization with 6-digit email OTP verification."""
    clean_email = data.email.lower().strip()
    
    # 1. Check if user already exists
    existing = db.query(Profile).filter(Profile.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in instead."
        )

    # 2. Validate password strength & confirmation
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    if data.confirm_password and data.confirm_password != data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation does not match password."
        )

    # 3. Validate website URL if provided (SSRF Protection)
    norm_website_url = None
    if data.website_url and data.website_url.strip():
        is_safe, ssrf_err, norm_url, _ = validate_public_url(data.website_url.strip())
        if not is_safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Website URL: {ssrf_err}"
            )
        norm_website_url = norm_url

    # 4. Derive or validate slug
    slug = data.org_slug.strip().lower() if data.org_slug else slugify(data.organization_name)
    existing_org = db.query(Organization).filter(Organization.slug == slug).first()
    if existing_org:
        # Append short random token if conflict
        slug = f"{slug}-{secrets.token_hex(2)}"

    # 5. Hash password securely for pending storage
    pw_hash = get_password_hash(data.password)

    payload = {
        "full_name": data.full_name.strip(),
        "email": clean_email,
        "password_hash": pw_hash,
        "organization_name": data.organization_name.strip(),
        "website_url": norm_website_url,
        "org_slug": slug,
        "industry": data.industry,
        "org_size": data.org_size,
        "country": data.country,
        "job_title": data.job_title
    }

    # 5. Create OTP Challenge & dispatch email
    challenge, otp_code = create_otp_challenge(db, clean_email, "signup", payload)
    send_signup_otp(clean_email, data.full_name, otp_code, data.organization_name)

    return {
        "status": "otp_sent",
        "email": clean_email,
        "purpose": "signup",
        "message": f"A 6-digit verification code has been dispatched to {clean_email}.",
        "expires_in_minutes": 10
    }

@router.post("/register", response_model=TokenResponse)
def register_legacy(data: UserRegister, db: Session = Depends(get_db)):
    """Legacy/direct registration endpoint for backwards compatibility."""
    clean_email = data.email.lower().strip()
    existing = db.query(Profile).filter(Profile.email == clean_email).first()
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
        email=clean_email,
        password_hash=hashed_pw,
        full_name=data.full_name,
        role=data.role or "Operator",
        organization_id=org_id,
        tenant_id=tenant_id,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if org_id:
        membership = OrganizationMembership(
            organization_id=org_id,
            user_id=user.id,
            role=data.role or "Operator"
        )
        db.add(membership)
        db.commit()

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

@router.post("/verify-otp")
def verify_otp(data: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verifies the 6-digit OTP. On signup verification, automatically provisions Organization, Tenant, Profile & Membership."""
    is_valid, msg, challenge = verify_otp_challenge(db, data.email, data.otp, data.purpose)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # If purpose == signup, provision the entire tenant & user
    if data.purpose == "signup":
        try:
            payload = json.loads(challenge.payload_data or "{}")
        except Exception:
            payload = {}

        if not payload or "email" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration session expired or corrupted. Please register again."
            )

        # Check if user was already created
        user = db.query(Profile).filter(Profile.email == payload["email"]).first()
        if not user:
            # 1. Create Organization
            org = Organization(
                name=payload.get("organization_name", "Enterprise Workspace"),
                slug=payload.get("org_slug", f"org-{secrets.token_hex(3)}"),
                plan="enterprise",
                industry=payload.get("industry", "Technology"),
                org_size=payload.get("org_size", "10-50"),
                country=payload.get("country", "Global")
            )
            db.add(org)
            db.flush() # Populate org.id

            # 2. Create Default Production Tenant
            tenant = Tenant(
                organization_id=org.id,
                name=f"{org.name} - Primary Cloud",
                slug="primary-cloud",
                region="us-east-1"
            )
            db.add(tenant)
            db.flush()

            # 3. Create User Profile
            user = Profile(
                email=payload["email"],
                password_hash=payload["password_hash"],
                full_name=payload.get("full_name", "Administrator"),
                role="Organization Owner",
                job_title=payload.get("job_title", "Lead Systems Architect"),
                is_verified=True,
                organization_id=org.id,
                tenant_id=tenant.id,
                is_active=True
            )
            db.add(user)
            db.flush()

            # Set org owner
            org.owner_id = user.id

            # 4. Create Organization Membership as Owner
            membership = OrganizationMembership(
                organization_id=org.id,
                user_id=user.id,
                role="Organization Owner",
                is_active=True
            )
            db.add(membership)

            # 5. Provision Default Primary Collector for this new tenant
            collector_id = f"col-{org.slug[:8]}-{secrets.token_hex(3)}"
            default_token = secrets.token_urlsafe(32)
            collector = Collector(
                id=collector_id,
                tenant_id=tenant.id,
                name=f"{org.name} Core Collector 01",
                hostname=f"collector.{org.slug}.internal",
                ip_address_pseudonym="10.240.0.12",
                version="1.4.2",
                status="online",
                auth_token_hash=get_password_hash(default_token),
                collection_interval_seconds=5
            )
            db.add(collector)

            # 6. Provision Initial Monitored Website if supplied during registration
            website_url = payload.get("website_url")
            if website_url:
                site = MonitoredWebsite(
                    organization_id=org.id,
                    created_by=user.id,
                    name=f"{org.name} Production Website",
                    url=website_url,
                    description="Primary corporate web property registered during onboarding",
                    is_verified=True,
                    verification_method="dns_txt",
                    verification_token=f"cynera-verify-{uuid.uuid4().hex[:16]}",
                    status="PENDING",
                    monitoring_interval_seconds=60,
                    is_active=True
                )
                db.add(site)
                org.website = website_url

            # 7. Add welcome notification
            welcome_notif = Notification(
                organization_id=org.id,
                user_id=user.id,
                title="Welcome to CYNERA Observability Platform",
                message=f"Your enterprise organization '{org.name}' has been successfully provisioned with active website monitoring.",
                type="success"
            )
            db.add(welcome_notif)

            db.commit()
            db.refresh(user)
            db.refresh(org)
        else:
            org = db.query(Organization).filter(Organization.id == user.organization_id).first()

        token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
        return {
            "status": "verified",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "job_title": user.job_title,
                "organization_id": user.organization_id,
                "tenant_id": user.tenant_id
            },
            "organization": {
                "id": org.id if org else None,
                "name": org.name if org else None,
                "slug": org.slug if org else None,
                "plan": org.plan if org else "enterprise"
            }
        }

    # If purpose == login
    elif data.purpose == "login":
        user = db.query(Profile).filter(Profile.email == data.email.lower().strip()).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or deactivated."
            )
        token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
        org = db.query(Organization).filter(Organization.id == user.organization_id).first()
        return {
            "status": "verified",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "organization_id": user.organization_id,
                "tenant_id": user.tenant_id
            },
            "organization": {
                "id": org.id if org else None,
                "name": org.name if org else None,
                "slug": org.slug if org else None
            }
        }

    # If purpose == password_reset
    elif data.purpose == "password_reset":
        return {
            "status": "verified",
            "email": data.email,
            "message": "Security code verified. You may now enter your new password."
        }

    return {"status": "verified", "message": "Verification completed."}

@router.post("/resend-otp")
def resend_otp(data: OTPResendRequest, db: Session = Depends(get_db)):
    """Dispatches a new 6-digit OTP code, honoring the 60-second cooldown rate limit."""
    success, msg, new_code, challenge = resend_otp_challenge(db, data.email, data.purpose)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg
        )

    # Send appropriate email template
    clean_email = data.email.lower().strip()
    if data.purpose == "signup":
        try:
            payload = json.loads(challenge.payload_data or "{}")
            name = payload.get("full_name", "Administrator")
            org_name = payload.get("organization_name", "CYNERA")
        except Exception:
            name = "Administrator"
            org_name = "CYNERA"
        send_signup_otp(clean_email, name, new_code, org_name)
    elif data.purpose == "login":
        user = db.query(Profile).filter(Profile.email == clean_email).first()
        name = user.full_name if user else "Operator"
        send_login_2fa_otp(clean_email, name, new_code)
    elif data.purpose == "password_reset":
        user = db.query(Profile).filter(Profile.email == clean_email).first()
        name = user.full_name if user else "Operator"
        send_password_reset_otp(clean_email, name, new_code)

    return {
        "status": "otp_resent",
        "message": "A refreshed 6-digit verification code has been dispatched to your email."
    }

@router.post("/login")
def login_user(data: UserLogin, db: Session = Depends(get_db)):
    clean_email = data.email.lower().strip()
    user = db.query(Profile).filter(Profile.email == clean_email).first()
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

    # Check if 2FA is required or requested
    if user.two_factor_enabled or data.require_2fa:
        challenge, otp_code = create_otp_challenge(db, clean_email, "login")
        send_login_2fa_otp(clean_email, user.full_name, otp_code)
        return {
            "status": "otp_required",
            "email": clean_email,
            "purpose": "login",
            "message": "Two-factor authentication code sent to your email."
        }

    # Direct login without 2FA
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    return {
        "status": "authenticated",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "job_title": user.job_title,
            "organization_id": user.organization_id,
            "tenant_id": user.tenant_id
        },
        "organization": {
            "id": org.id if org else None,
            "name": org.name if org else None,
            "slug": org.slug if org else None,
            "plan": org.plan if org else "enterprise"
        }
    }

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    clean_email = data.email.lower().strip()
    user = db.query(Profile).filter(Profile.email == clean_email).first()
    if user and user.is_active:
        challenge, otp_code = create_otp_challenge(db, clean_email, "password_reset")
        send_password_reset_otp(clean_email, user.full_name, otp_code)
    
    # Generic message for security (prevents user enumeration)
    return {
        "status": "otp_sent",
        "email": clean_email,
        "message": "If the account exists, a 6-digit password reset code has been sent to your email."
    }

@router.post("/reset-password")
def reset_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    clean_email = data.email.lower().strip()
    is_valid, msg, challenge = verify_otp_challenge(db, clean_email, data.otp, "password_reset")
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    user = db.query(Profile).filter(Profile.email == clean_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    user.password_hash = get_password_hash(data.new_password)
    db.commit()

    return {
        "status": "password_reset_success",
        "message": "Your password has been successfully updated. You may now log in."
    }

@router.get("/me")
def get_me(current_user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == current_user.organization_id,
        OrganizationMembership.user_id == current_user.id
    ).first()

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": membership.role if membership else current_user.role,
        "job_title": current_user.job_title,
        "phone": current_user.phone,
        "is_verified": current_user.is_verified,
        "two_factor_enabled": current_user.two_factor_enabled,
        "organization_id": current_user.organization_id,
        "tenant_id": current_user.tenant_id,
        "is_active": current_user.is_active,
        "organization": {
            "id": org.id if org else None,
            "name": org.name if org else None,
            "slug": org.slug if org else None,
            "plan": org.plan if org else "enterprise",
            "industry": org.industry if org else None,
            "country": org.country if org else None
        } if org else None
    }
