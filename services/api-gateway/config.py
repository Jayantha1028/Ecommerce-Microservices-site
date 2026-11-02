"""API Gateway Configuration & Route Registry."""
from __future__ import annotations

import os
from dotenv import load_dotenv

try:
    load_dotenv()
except (PermissionError, OSError):
    pass

# Cryptographic token verification parameters
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"

# Internal microservice endpoints
USER_AUTH_URL = os.getenv("USER_AUTH_URL", "http://user-auth-service:8001").rstrip("/")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002").rstrip("/")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8004").rstrip("/")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8003").rstrip("/")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8005").rstrip("/")

# Proxy timeout in seconds
TIMEOUT_SECONDS = float(os.getenv("GATEWAY_TIMEOUT_SECONDS", "10"))

# Service route registry: Maps URL path prefixes to upstream microservice base URLs.
ROUTES = (
    ("/auth", USER_AUTH_URL),
    ("/users", USER_AUTH_URL),
    ("/products", PRODUCT_SERVICE_URL),
    ("/categories", PRODUCT_SERVICE_URL),
    ("/inventory", PRODUCT_SERVICE_URL),
    ("/cart", CART_SERVICE_URL),
    ("/orders", ORDER_SERVICE_URL),
    ("/payments", PAYMENT_SERVICE_URL),
)

# Endpoints that do not require authentication
PUBLIC_EXACT = {
    ("POST", "/auth/register"),
    ("POST", "/auth/verify-email"),
    ("POST", "/auth/login"),
    ("POST", "/auth/verify-token"),
}

# Hop-by-hop headers that must not be forwarded by reverse proxies
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def validate_configuration() -> None:
    """Validate that critical environment variables are properly set before serving traffic."""
    if not JWT_SECRET or len(JWT_SECRET) < 32:
        raise RuntimeError("JWT_SECRET must be configured and contain at least 32 characters")
