from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import Profile, Organization, OrganizationMembership, utc_now
from ..schemas.schemas import (
    OrganizationResponse, OrganizationUpdateRequest,
    MemberResponse, MemberInviteRequest, MemberUpdateRoleRequest
)
from ..auth.deps import get_current_user, RoleChecker
from ..services.email_service import send_member_invite
from ..auth.jwt import get_password_hash
import secrets

router = APIRouter(prefix="/organization", tags=["Organization & Members"])

@router.get("/current", response_model=OrganizationResponse)
def get_current_organization(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not associated with an organization."
        )
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found."
        )
    return org

@router.patch("/current", response_model=OrganizationResponse)
def update_current_organization(
    data: OrganizationUpdateRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found."
        )
    if data.name is not None:
        org.name = data.name.strip()
    if data.industry is not None:
        org.industry = data.industry
    if data.website is not None:
        org.website = data.website.strip()
    if data.org_size is not None:
        org.org_size = data.org_size
    if data.country is not None:
        org.country = data.country

    org.updated_at = utc_now()
    db.commit()
    db.refresh(org)
    return org

@router.get("/members")
def list_organization_members(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        return []

    # Get memberships
    memberships = db.query(OrganizationMembership, Profile).join(
        Profile, OrganizationMembership.user_id == Profile.id
    ).filter(
        OrganizationMembership.organization_id == current_user.organization_id
    ).all()

    results = []
    for mem, prof in memberships:
        results.append({
            "membership_id": mem.id,
            "user_id": prof.id,
            "email": prof.email,
            "full_name": prof.full_name,
            "role": mem.role,
            "job_title": prof.job_title,
            "is_active": mem.is_active and prof.is_active,
            "created_at": mem.created_at.isoformat() if mem.created_at else None
        })

    # If memberships table had no rows for this org, fall back to profiles with this organization_id
    if not results:
        profiles = db.query(Profile).filter(Profile.organization_id == current_user.organization_id).all()
        for prof in profiles:
            results.append({
                "membership_id": prof.id,
                "user_id": prof.id,
                "email": prof.email,
                "full_name": prof.full_name,
                "role": prof.role,
                "job_title": prof.job_title,
                "is_active": prof.is_active,
                "created_at": prof.created_at.isoformat() if prof.created_at else None
            })

    return results

@router.post("/members/invite")
def invite_member(
    data: MemberInviteRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    clean_email = data.email.lower().strip()
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    # Check if user already exists
    user = db.query(Profile).filter(Profile.email == clean_email).first()
    if not user:
        # Create user account with a temporary secure random password
        temp_pw = f"Cyn!{secrets.token_hex(6)}"
        user = Profile(
            email=clean_email,
            password_hash=get_password_hash(temp_pw),
            full_name=data.full_name.strip(),
            role=data.role,
            job_title=data.job_title,
            organization_id=org.id,
            tenant_id=current_user.tenant_id,
            is_verified=True,
            is_active=True
        )
        db.add(user)
        db.flush()

    # Check if membership already exists
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org.id,
        OrganizationMembership.user_id == user.id
    ).first()

    if membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already a member of this organization."
        )

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=data.role,
        is_active=True,
        invited_by=current_user.id
    )
    db.add(membership)
    db.commit()

    # Dispatch branded invitation email
    send_member_invite(clean_email, current_user.full_name, org.name, data.role)

    return {
        "status": "invited",
        "email": clean_email,
        "role": data.role,
        "message": f"Invitation successfully sent to {clean_email}."
    }

@router.patch("/members/{membership_id}")
def update_member_role(
    membership_id: str,
    data: MemberUpdateRoleRequest,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    mem = db.query(OrganizationMembership).filter(
        OrganizationMembership.id == membership_id,
        OrganizationMembership.organization_id == current_user.organization_id
    ).first()

    if not mem:
        # Fallback check by user_id
        mem = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == membership_id,
            OrganizationMembership.organization_id == current_user.organization_id
        ).first()

    if not mem:
        raise HTTPException(status_code=404, detail="Member record not found.")

    mem.role = data.role
    if data.is_active is not None:
        mem.is_active = data.is_active

    # Update profile role if matched
    user = db.query(Profile).filter(Profile.id == mem.user_id).first()
    if user:
        user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active

    db.commit()
    return {"status": "updated", "role": mem.role, "is_active": mem.is_active}

@router.delete("/members/{membership_id}")
def remove_member(
    membership_id: str,
    current_user: Profile = Depends(RoleChecker(["Super Administrator", "Organization Owner", "Admin", "Organization Administrator"])),
    db: Session = Depends(get_db)
):
    mem = db.query(OrganizationMembership).filter(
        OrganizationMembership.id == membership_id,
        OrganizationMembership.organization_id == current_user.organization_id
    ).first()

    if not mem:
        mem = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == membership_id,
            OrganizationMembership.organization_id == current_user.organization_id
        ).first()

    if not mem:
        raise HTTPException(status_code=404, detail="Member record not found.")

    if mem.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from your own organization."
        )

    db.delete(mem)
    db.commit()
    return {"status": "removed", "message": "Member removed from organization."}

