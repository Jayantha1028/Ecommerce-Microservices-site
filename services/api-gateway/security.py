"""API Gateway Security, Token Validation & Route Resolution."""
from __future__ import annotations

from typing import Optional
import jwt

from config import JWT_ALGORITHM, JWT_SECRET, PUBLIC_EXACT, ROUTES


def service_for(path: str) -> Optional[str]:
    """Map a request URL path to its designated upstream service base URL."""
    for prefix, base_url in ROUTES:
        if path == prefix or path.startswith(prefix + "/"):
            return base_url
    return None


def requires_auth(method: str, path: str) -> bool:
    """Determine whether an incoming HTTP request requires Bearer token authentication."""
    # HTTP OPTIONS preflight requests never require authentication
    if method.upper() == "OPTIONS":
        return False

    if (method.upper(), path.rstrip("/")) in PUBLIC_EXACT:
        return False

    # Product catalogue reads are public; modifications (POST, PUT, DELETE) require admin auth.
    if path == "/products" or path.startswith("/products/"):
        return method.upper() not in {"GET", "HEAD"}

    return path.startswith(("/users", "/inventory", "/cart", "/orders", "/payments", "/auth/profile"))


def verify_bearer(value: Optional[str]) -> Optional[dict]:
    """Validate and decode a Bearer JWT token from an Authorization header."""
    if not value or not value.lower().startswith("bearer "):
        return None

    token = value.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        # Include 30 seconds leeway to tolerate minor clock skew across distributed containers.
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], leeway=30)
    except jwt.PyJWTError:
        return None
