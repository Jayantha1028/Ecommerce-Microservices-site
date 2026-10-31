"""Payment Service Configuration & Environment Settings."""
from __future__ import annotations

import os
from dotenv import load_dotenv

try:
    load_dotenv()
except (PermissionError, OSError):
    pass

PORT = int(os.getenv("PORT", "8003"))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://payment_user:payment_pass@payment-db:5432/payment_db",
)
DB_CONNECT_RETRIES = max(1, int(os.getenv("DB_CONNECT_RETRIES", "10")))
DB_CONNECT_RETRY_DELAY_SECONDS = max(0.1, float(os.getenv("DB_CONNECT_RETRY_DELAY_SECONDS", "2")))

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# Zero-cost offline sandbox / mock mode for developer environments without live Razorpay accounts
PAYMENT_SIMULATION_MODE = (
    os.getenv("PAYMENT_SIMULATION_MODE", "false").lower() == "true"
    or "mock" in RAZORPAY_KEY_ID.lower()
    or "replace" in RAZORPAY_KEY_ID.lower()
    or RAZORPAY_KEY_ID == ""
)


def validate_configuration() -> None:
    """Verify that required payment gateway API keys are present."""
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured")
