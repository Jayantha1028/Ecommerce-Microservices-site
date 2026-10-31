"""Cart Service Configuration & Environment Settings."""
from __future__ import annotations

import os

SERVICE_NAME = "cart-service"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://cart_user:cart_pass@cart-db:5432/cart_db",
)
if not (DATABASE_URL.startswith("postgresql+") or DATABASE_URL.startswith("sqlite")):
    raise RuntimeError("DATABASE_URL must point to PostgreSQL; SQLite is not supported for application runtime")

# Inter-service endpoints
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002").rstrip("/")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8004").rstrip("/")

# Inter-service HTTP timeouts (in seconds)
PRODUCT_TIMEOUT = float(os.getenv("PRODUCT_TIMEOUT_SECONDS", "5"))
ORDER_TIMEOUT = float(os.getenv("ORDER_TIMEOUT_SECONDS", "15"))

# Database connection retry parameters
DB_CONNECT_RETRIES = max(1, int(os.getenv("DB_CONNECT_RETRIES", "10")))
DB_CONNECT_RETRY_DELAY_SECONDS = max(0.1, float(os.getenv("DB_CONNECT_RETRY_DELAY_SECONDS", "2")))
