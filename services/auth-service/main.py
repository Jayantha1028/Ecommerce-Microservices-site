"""User & Authentication Microservice Entrypoint.

Handles identity, registration, email verification, password security,
JWT token issuance, login audit history, and user profile management.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure local directory is importable
SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import (
    DATABASE_URL,
    DB_CONNECT_RETRIES,
    DB_CONNECT_RETRY_DELAY_SECONDS,
    DUMMY_PASSWORD_HASH,
    EXPOSE_VERIFICATION_CODE,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
)
from database import Base, SessionLocal, engine, get_db, init_db
from models import LoginHistory, User, UserProfile, VerificationCode
from routes import router
from schemas import LoginIn, RegisterIn, TokenIn, UserProfileIn, VerifyEmailIn
from security import (
    check_password,
    decode_token,
    hash_password,
    hash_verification_code,
    issue_token,
    now,
    user_public,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """FastAPI lifespan context manager: verifies DB connectivity and creates schema tables on boot."""
    init_db()
    yield


app = FastAPI(
    title="User/Auth Service",
    description="Identity and Authentication Microservice",
    version="2.0.0",
    lifespan=lifespan,
)

# Include routes
app.include_router(router)
