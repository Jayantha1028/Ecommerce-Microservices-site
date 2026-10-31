"""User & Authentication Service Configuration."""
from __future__ import annotations

import os
from dotenv import load_dotenv

try:
    load_dotenv()
except (PermissionError, OSError):
    pass

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://auth_user:auth_pass@auth-db:5432/auth_db",
)
if not (DATABASE_URL.startswith("postgresql+") or DATABASE_URL.startswith("sqlite")):
    raise RuntimeError("DATABASE_URL must point to PostgreSQL; SQLite is not supported for application runtime")

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # Default 24 hours
EXPOSE_VERIFICATION_CODE = os.getenv("AUTH_EXPOSE_VERIFICATION_CODE", "false").lower() == "true"

DB_CONNECT_RETRIES = max(1, int(os.getenv("DB_CONNECT_RETRIES", "10")))
DB_CONNECT_RETRY_DELAY_SECONDS = max(0.1, float(os.getenv("DB_CONNECT_RETRY_DELAY_SECONDS", "2")))

# Pre-computed dummy scrypt hash to equalize computation time during login attempts
# when a user does not exist in the database, preventing user enumeration via timing attacks.
DUMMY_PASSWORD_HASH = (
    "7510cc920455b9cfd4eb235d8fd83e63$"
    "7b6624c628d05b64b50bb52328ca0bf24eee95959d27b137e214e3427657a5402dc1de4c2756117509c26d7e1003c8fe1ab71519dbcf0b74a7c084954f407254"
)
