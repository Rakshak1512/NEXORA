from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import Profile, Notification, utc_now
from ..schemas.schemas import NotificationResponse
from ..auth.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        return []
    notifs = db.query(Notification).filter(
        Notification.organization_id == current_user.organization_id,
        (Notification.user_id == current_user.id) | (Notification.user_id == None)
    ).order_by(Notification.created_at.desc()).limit(50).all()

    return notifs

@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: str,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.organization_id == current_user.organization_id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    return {"status": "marked_read", "id": notification_id}

@router.post("/read-all")
def mark_all_as_read(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.organization_id:
        db.query(Notification).filter(
            Notification.organization_id == current_user.organization_id,
            (Notification.user_id == current_user.id) | (Notification.user_id == None)
        ).update({"is_read": True})
        db.commit()
    return {"status": "all_marked_read"}

