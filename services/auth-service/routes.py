"""FastAPI Route Handlers for User & Auth Service."""
from __future__ import annotations

import hmac
import secrets
from datetime import timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from config import DUMMY_PASSWORD_HASH, EXPOSE_VERIFICATION_CODE, JWT_EXPIRE_MINUTES
from database import get_db
from models import LoginHistory, User, UserProfile, VerificationCode
from schemas import LoginIn, RegisterIn, TokenIn, UpdateProfileIn, UserProfileIn, VerifyEmailIn
from security import (
    check_password,
    decode_token,
    hash_password,
    hash_verification_code,
    issue_token,
    now,
    user_public,
)

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Service health and database probe endpoint."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "UP", "service": "user-auth", "database": "UP"}
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Auth PostgreSQL database unavailable") from exc


@router.post("/auth/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)) -> dict:
    """Register a new user account and generate an email verification code."""
    normalized_email = str(data.email).lower()
    current = now()

    # Generate a cryptographically secure 6-digit numeric verification code
    code = f"{secrets.randbelow(900000) + 100000}"

    user = User(
        name=data.name.strip(),
        email=normalized_email,
        password_hash=hash_password(data.password),
        role="CUSTOMER",
        verified=False,
        status="PENDING",
        created_at=current,
    )
    user.profile = UserProfile(name=data.name.strip(), email=normalized_email)
    user.verification_codes.append(
        VerificationCode(
            code_hash=hash_verification_code(code),
            expires_at=current + timedelta(hours=24),
            used=False,
            created_at=current,
        )
    )

    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc

    result = {
        "message": "Account created. Verify the email address before logging in.",
        "user": {**user_public(user), "createdAt": user.created_at.isoformat()},
    }

    if EXPOSE_VERIFICATION_CODE:
        result["verificationCode"] = code

    return result


@router.post("/auth/verify-email")
def verify_email(data: VerifyEmailIn, db: Session = Depends(get_db)) -> dict:
    """Verify an account using the one-time code sent upon registration."""
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification details")

    code_row = db.scalar(
        select(VerificationCode)
        .where(VerificationCode.user_id == user.id)
        .order_by(VerificationCode.created_at.desc())
        .limit(1)
    )

    if not code_row or code_row.used or not hmac.compare_digest(code_row.code_hash, hash_verification_code(data.code)):
        raise HTTPException(status_code=400, detail="Invalid or already-used verification code")

    expiry = code_row.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry < now():
        raise HTTPException(status_code=400, detail="Verification code expired")

    user.verified = True
    user.status = "ACTIVE"
    code_row.used = True
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/auth/login")
def login(
    data: LoginIn,
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """Authenticate user credentials, log login history, and issue JWT token."""
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))

    if user:
        password_ok = check_password(data.password, user.password_hash)
    else:
        check_password(data.password, DUMMY_PASSWORD_HASH)
        password_ok = False

    success = bool(user and password_ok and user.verified and user.status == "ACTIVE")

    db.add(
        LoginHistory(
            user_id=user.id if user else None,
            attempt="SUCCESS" if success else "FAILED",
            ip=(x_forwarded_for or "")[:255],
            user_agent=(user_agent or "")[:1000],
            created_at=now(),
        )
    )
    db.commit()

    if not user or not password_ok:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.verified or user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Account must be verified and active before login")

    return {
        "message": "Login successful",
        "token": issue_token(user),
        "tokenType": "Bearer",
        "expiresIn": JWT_EXPIRE_MINUTES * 60,
    }


@router.post("/auth/verify-token")
def verify_token(data: TokenIn, db: Session = Depends(get_db)) -> dict:
    """Validate a JWT token and confirm the user account is active in the database."""
    decoded = decode_token(data.token)
    user = db.get(User, decoded.get("sub") or decoded.get("id"))

    if not user or user.status != "ACTIVE" or not user.verified:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"user": user_public(user)}


@router.post("/users", status_code=201)
def create_user_profile(
    data: UserProfileIn,
    x_auth_user_id: Optional[str] = Header(None),
    x_auth_user_role: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """Create a customer profile for an authenticated user."""
    if not x_auth_user_id:
        raise HTTPException(status_code=401, detail="Authenticated user identity is required")

    if data.authUserId != x_auth_user_id and (x_auth_user_role or "CUSTOMER").upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="You cannot create a profile for another account")

    user = db.get(User, data.authUserId)
    if not user:
        raise HTTPException(status_code=404, detail="Authentication user not found")

    if user.profile:
        raise HTTPException(status_code=409, detail="A profile already exists for this account")

    profile = UserProfile(
        auth_user_id=user.id,
        name=data.name.strip(),
        email=str(data.email).lower(),
    )
    user.name = profile.name
    user.email = profile.email

    db.add(profile)
    try:
        db.commit()
        db.refresh(profile)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A profile already exists for this account") from exc

    return {
        "message": "User profile created",
        "data": {
            "id": profile.id,
            "authUserId": profile.auth_user_id,
            "name": profile.name,
            "email": profile.email,
        },
    }


@router.get("/users/{user_id}")
def get_user_profile(
    user_id: str,
    field: Optional[str] = Query(None),
    x_auth_user_id: Optional[str] = Header(None),
    x_auth_user_role: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve user profile information by profile ID or auth user ID."""
    if field not in (None, "authUserId"):
        raise HTTPException(status_code=400, detail="Unsupported lookup field")

    if not x_auth_user_id:
        raise HTTPException(status_code=401, detail="Authenticated user identity is required")

    lookup_auth_id = user_id if field == "authUserId" else None
    profile = (
        db.scalar(select(UserProfile).where(UserProfile.auth_user_id == lookup_auth_id))
        if lookup_auth_id
        else db.get(UserProfile, user_id)
    )

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    if profile.auth_user_id != x_auth_user_id and (x_auth_user_role or "CUSTOMER").upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="You cannot access another user's profile")

    return {
        "user": {
            "id": profile.id,
            "authUserId": profile.auth_user_id,
            "name": profile.name,
            "email": profile.email,
            "phone": profile.phone or "",
            "address": profile.address or "",
        }
    }


@router.get("/auth/profile")
def get_my_profile(
    x_auth_user_id: Optional[str] = Header(None),
    x_auth_user_role: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve current authenticated user's profile and account details."""
    if not x_auth_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = db.get(User, x_auth_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")

    if not user.profile:
        user.profile = UserProfile(
            auth_user_id=user.id,
            name=user.name,
            email=user.email,
            phone="",
            address="",
        )
        db.add(user.profile)
        db.commit()
        db.refresh(user)

    return {
        "status": "success",
        "profile": {
            "id": user.profile.id,
            "authUserId": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.profile.phone or "",
            "address": user.profile.address or "",
            "role": user.role,
            "status": user.status,
            "verified": user.verified,
            "createdAt": user.created_at.isoformat(),
        },
    }


@router.put("/auth/profile")
@router.patch("/auth/profile")
def update_my_profile(
    data: UpdateProfileIn,
    x_auth_user_id: Optional[str] = Header(None),
    x_auth_user_role: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """Update current authenticated user's profile details and optional password."""
    if not x_auth_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = db.get(User, x_auth_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")

    if not user.profile:
        user.profile = UserProfile(
            auth_user_id=user.id,
            name=user.name,
            email=user.email,
            phone="",
            address="",
        )
        db.add(user.profile)

    # Update name if provided
    if data.name and data.name.strip():
        new_name = data.name.strip()
        user.name = new_name
        user.profile.name = new_name

    # Update email if provided and changed
    if data.email:
        normalized_email = str(data.email).lower().strip()
        if normalized_email != user.email:
            existing = db.scalar(
                select(User).where(User.email == normalized_email, User.id != user.id)
            )
            if existing:
                raise HTTPException(status_code=409, detail="An account with this email already exists")
            user.email = normalized_email
            user.profile.email = normalized_email

    # Update phone if provided
    if data.phone is not None:
        user.profile.phone = data.phone.strip()

    # Update address if provided
    if data.address is not None:
        user.profile.address = data.address.strip()

    # Update password if requested
    if data.new_password:
        if not data.current_password:
            raise HTTPException(
                status_code=400,
                detail="Current password is required to set a new password",
            )
        if not check_password(data.current_password, user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="Incorrect current password",
            )
        user.password_hash = hash_password(data.new_password)

    try:
        db.commit()
        db.refresh(user)
        db.refresh(user.profile)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not update profile due to unique constraint") from exc

    # Generate fresh token with updated claims
    fresh_token = issue_token(user)

    return {
        "status": "success",
        "message": "Profile updated successfully",
        "profile": {
            "id": user.profile.id,
            "authUserId": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.profile.phone or "",
            "address": user.profile.address or "",
            "role": user.role,
        },
        "token": fresh_token,
    }


@router.put("/users/{user_id}")
@router.patch("/users/{user_id}")
def update_user_profile_endpoint(
    user_id: str,
    data: UpdateProfileIn,
    x_auth_user_id: Optional[str] = Header(None),
    x_auth_user_role: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """Update user profile by user ID or 'me'."""
    target_id = x_auth_user_id if user_id == "me" else user_id
    if target_id != x_auth_user_id and (x_auth_user_role or "CUSTOMER").upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="You cannot edit another user's profile")
    return update_my_profile(data=data, x_auth_user_id=target_id, x_auth_user_role=x_auth_user_role, db=db)
