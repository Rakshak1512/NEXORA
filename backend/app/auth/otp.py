import secrets
import hashlib
import datetime
import json
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from ..config import settings
from ..models.models import OTPChallenge, utc_now

OTP_EXPIRY_MINUTES = 10
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60

def generate_otp() -> str:
    """Generates a secure 6-digit numeric OTP."""
    # 100000 to 999999
    return str(secrets.randbelow(900000) + 100000)

def hash_otp(email: str, otp: str, purpose: str) -> str:
    """Hashes the OTP combined with email, purpose and server secret."""
    secret = getattr(settings, "OTP_HASH_SECRET", "cynera_secret_hash_key_2026")
    raw = f"{email.lower().strip()}:{purpose}:{otp}:{secret}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def create_otp_challenge(
    db: Session,
    email: str,
    purpose: str,
    payload_data: Optional[Dict[str, Any]] = None
) -> Tuple[OTPChallenge, str]:
    """Creates a new OTP challenge, invalidates previous unused ones for this email+purpose."""
    clean_email = email.lower().strip()
    
    # Mark older unused challenges as expired/used
    db.query(OTPChallenge).filter(
        OTPChallenge.email == clean_email,
        OTPChallenge.purpose == purpose,
        OTPChallenge.is_used == False
    ).update({"is_used": True})
    
    otp_code = generate_otp()
    otp_hashed = hash_otp(clean_email, otp_code, purpose)
    
    now = utc_now()
    expires_at = now + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    challenge = OTPChallenge(
        email=clean_email,
        otp_hash=otp_hashed,
        purpose=purpose,
        attempts=0,
        resend_count=0,
        is_used=False,
        expires_at=expires_at,
        last_sent_at=now,
        payload_data=json.dumps(payload_data or {})
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    
    return challenge, otp_code

def verify_otp_challenge(
    db: Session,
    email: str,
    otp: str,
    purpose: str
) -> Tuple[bool, str, Optional[OTPChallenge]]:
    """Verifies a 6-digit OTP challenge against the database."""
    clean_email = email.lower().strip()
    clean_otp = str(otp).strip()
    
    challenge = db.query(OTPChallenge).filter(
        OTPChallenge.email == clean_email,
        OTPChallenge.purpose == purpose,
        OTPChallenge.is_used == False
    ).order_by(OTPChallenge.created_at.desc()).first()
    
    if not challenge:
        return False, "No active verification code found. Please request a new code.", None
        
    now = utc_now()
    # Check expiry (handle both timezone-aware and naive SQLite dates)
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
        
    if now > expires_at:
        challenge.is_used = True
        db.commit()
        return False, "Verification code has expired. Please request a new code.", None
        
    if challenge.attempts >= MAX_ATTEMPTS:
        challenge.is_used = True
        db.commit()
        return False, "Maximum verification attempts exceeded. Please request a new code.", None
        
    # Increment attempt count
    challenge.attempts += 1
    
    # Verify hash
    expected_hash = hash_otp(clean_email, clean_otp, purpose)
    if challenge.otp_hash != expected_hash:
        db.commit()
        remaining = MAX_ATTEMPTS - challenge.attempts
        return False, f"Invalid verification code. {remaining} attempt(s) remaining.", None
        
    # Mark as successfully used
    challenge.is_used = True
    db.commit()
    return True, "Verification successful.", challenge

def resend_otp_challenge(
    db: Session,
    email: str,
    purpose: str
) -> Tuple[bool, str, Optional[str], Optional[OTPChallenge]]:
    """Generates a refreshed OTP honoring the 60-second cooldown."""
    clean_email = email.lower().strip()
    
    challenge = db.query(OTPChallenge).filter(
        OTPChallenge.email == clean_email,
        OTPChallenge.purpose == purpose,
        OTPChallenge.is_used == False
    ).order_by(OTPChallenge.created_at.desc()).first()
    
    now = utc_now()
    if challenge:
        last_sent = challenge.last_sent_at
        if last_sent.tzinfo is None:
            last_sent = last_sent.replace(tzinfo=datetime.timezone.utc)
            
        elapsed = (now - last_sent).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            remaining_sec = int(RESEND_COOLDOWN_SECONDS - elapsed)
            return False, f"Please wait {remaining_sec} seconds before requesting another code.", None, None
            
        # Re-use payload data
        try:
            payload = json.loads(challenge.payload_data or "{}")
        except Exception:
            payload = {}
    else:
        payload = {}
        
    new_challenge, otp_code = create_otp_challenge(db, clean_email, purpose, payload)
    return True, "A new verification code has been dispatched.", otp_code, new_challenge
