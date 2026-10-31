"""Security & Gateway Identity Verification for Product Service."""
from __future__ import annotations

from typing import Optional
from fastapi import Depends, Header, HTTPException, status


def require_identity(
    x_auth_user_id: Optional[str] = Header(None),
    x_auth_user_role: Optional[str] = Header(None),
) -> tuple[str, str]:
    """Ensure trusted identity headers injected by API gateway are present."""
    if not x_auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user identity is required",
        )
    return x_auth_user_id, (x_auth_user_role or "CUSTOMER").upper()


def require_admin(identity: tuple[str, str] = Depends(require_identity)) -> tuple[str, str]:
    """Restrict endpoint access to users holding ADMIN or PRODUCT_MANAGER roles."""
    _user_id, role = identity
    if role not in {"ADMIN", "PRODUCT_MANAGER"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator or product-manager role required",
        )
    return identity
