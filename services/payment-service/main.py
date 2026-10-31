"""Payment Service Entrypoint & FastAPI Application."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI
import razorpay
import uvicorn

import database
from client import razorpay_client
from config import PORT, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, validate_configuration
from database import Base, SessionLocal, engine, get_db, initialize_database
from models import PaymentRecord
from routes import router
from schemas import (
    CreateOrderRequest,
    PaymentOut,
    VerifyPaymentRequest,
    create_order_response,
    payment_payload,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: validates configuration and initializes database schema."""
    global razorpay_client
    validate_configuration()
    initialize_database()
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    yield


app = FastAPI(
    title="FastAPI Payment Service",
    description="Payment Service with Razorpay integration and database persistence",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(router)

# Compatibility aliases and re-exports for unit tests
_payment_payload = payment_payload
_create_order_response = create_order_response

__all__ = [
    "app",
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "initialize_database",
    "PaymentRecord",
    "razorpay_client",
    "CreateOrderRequest",
    "VerifyPaymentRequest",
    "PaymentOut",
    "_payment_payload",
    "_create_order_response",
]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
