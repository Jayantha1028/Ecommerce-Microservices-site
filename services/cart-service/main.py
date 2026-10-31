"""Cart Service Entrypoint & FastAPI Application."""
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

import database
from client import get_http_client
from config import ORDER_TIMEOUT, SERVICE_NAME
from database import Base, SessionLocal, engine, get_db, init_db
from models import CartItem
from routes import router
from schemas import CartItemAdd, CartItemUpdate, CheckoutRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager initializing tables and client sessions."""
    init_db()
    client = get_http_client()
    yield
    if client and not client.is_closed:
        client.close()


app = FastAPI(
    title="E-Commerce Cart Service",
    description="Shopping cart and checkout orchestrator",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

# Re-export symbols for backward compatibility with tests and entrypoints
__all__ = [
    "app",
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "CartItem",
    "CartItemAdd",
    "CartItemUpdate",
    "CheckoutRequest",
    "get_http_client",
]
