"""Product Service Entrypoint & FastAPI Application."""
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

import database
from config import SERVICE_NAME
from database import Base, SessionLocal, engine, get_db, init_db
from models import Inventory, Product, Reservation, ReservationItem
from routes import router
from schemas import product_payload, reservation_payload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager initializing tables upon startup."""
    init_db()
    yield


app = FastAPI(
    title=SERVICE_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

# Re-export symbols for backward compatibility with tests and external tools
__all__ = [
    "app",
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "Product",
    "Inventory",
    "Reservation",
    "ReservationItem",
    "product_payload",
    "reservation_payload",
]
