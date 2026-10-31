"""Product & Inventory Service Configuration."""
from __future__ import annotations

import os

SERVICE_NAME = "product-service"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://product_user:product_pass@product-db:5432/product_db",
)

if not (DATABASE_URL.startswith("postgresql+") or DATABASE_URL.startswith("sqlite")):
    raise RuntimeError("DATABASE_URL must point to PostgreSQL; SQLite is not supported for application runtime")

DB_CONNECT_RETRIES = max(1, int(os.getenv("DB_CONNECT_RETRIES", "10")))
DB_CONNECT_RETRY_DELAY_SECONDS = max(0.1, float(os.getenv("DB_CONNECT_RETRY_DELAY_SECONDS", "2")))
