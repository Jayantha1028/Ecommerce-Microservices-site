"""Cart Service Database Engine & Initialization."""
from __future__ import annotations

import sys
import time
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DATABASE_URL, DB_CONNECT_RETRIES, DB_CONNECT_RETRY_DELAY_SECONDS


class Base(DeclarativeBase):
    """Declarative base class for Cart Service models."""
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and ensures proper closure."""
    session_factory = SessionLocal
    for name in ("cart_main", "main"):
        mod = sys.modules.get(name)
        if mod and hasattr(mod, "SessionLocal") and getattr(mod, "SessionLocal") is not None:
            session_factory = getattr(mod, "SessionLocal")
            break
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables with connection retry logic."""
    if str(DATABASE_URL).startswith("sqlite") or str(getattr(engine, "url", "")).startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        return

    last_error: Exception | None = None
    for attempt in range(1, DB_CONNECT_RETRIES + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            return
        except Exception as exc:
            last_error = exc
            if attempt < DB_CONNECT_RETRIES:
                time.sleep(DB_CONNECT_RETRY_DELAY_SECONDS)

    raise RuntimeError(
        f"Cart Service could not connect to its configured database after "
        f"{DB_CONNECT_RETRIES} attempts. Check DATABASE_URL and database readiness."
    ) from last_error
