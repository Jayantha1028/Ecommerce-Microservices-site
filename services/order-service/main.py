"""Order Service Entrypoint & FastAPI Application."""
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

import database
from client import get_http_client
from config import PAYMENT_TIMEOUT, SERVICE_NAME
from database import Base, SessionLocal, engine, get_db, init_db
from models import Order, OrderItem
from routes import router
from schemas import CancelInput, OrderCreate, OrderLineInput, PaymentVerifyInput, order_payload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager initializing tables and client sessions."""
    init_db()
    client = get_http_client()
    yield
    if client and not client.is_closed:
        client.close()


app = FastAPI(
    title="E-Commerce Order Service",
    description="Order management and payment coordinator",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

# Aliases and re-exports for unit test backward compatibility
_order_payload = order_payload

__all__ = [
    "app",
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "Order",
    "OrderItem",
    "OrderLineInput",
    "OrderCreate",
    "PaymentVerifyInput",
    "CancelInput",
    "order_payload",
    "_order_payload",
    "get_http_client",
]
