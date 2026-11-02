"""Product Service Database Engine & Initialization."""
from __future__ import annotations

import sys
import time
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DATABASE_URL, DB_CONNECT_RETRIES, DB_CONNECT_RETRY_DELAY_SECONDS


class Base(DeclarativeBase):
    """Declarative base class for Product Service models."""
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency yielding a SQLAlchemy session and guaranteeing closure."""
    session_factory = SessionLocal
    for name in ("product_main", "main"):
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
    """Initialize database tables with connection retry logic and schema migrations."""
    def _run_migrations(conn):
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(64) DEFAULT 'accessories'"))
        # Auto-classify existing products by SKU prefix
        conn.execute(text("UPDATE products SET category = 'laptops' WHERE sku LIKE 'LAPTOP%' AND (category IS NULL OR category = 'accessories')"))
        conn.execute(text("UPDATE products SET category = 'phones' WHERE sku LIKE 'PHONE%' AND (category IS NULL OR category = 'accessories')"))
        conn.execute(text("UPDATE products SET category = 'audio' WHERE (sku LIKE 'AUDIO%' OR sku LIKE 'SPKR%') AND (category IS NULL OR category = 'accessories')"))
        conn.execute(text("UPDATE products SET category = 'displays' WHERE sku LIKE 'DISP%' AND (category IS NULL OR category = 'accessories')"))
        conn.execute(text("UPDATE products SET category = 'peripherals' WHERE (sku LIKE 'KEYB%' OR sku LIKE 'MOUS%') AND (category IS NULL OR category = 'accessories')"))
        conn.execute(text("UPDATE products SET category = 'gaming' WHERE (sku LIKE 'GAME%' OR sku LIKE 'DRON%') AND (category IS NULL OR category = 'accessories')"))
        conn.execute(text("UPDATE products SET category = 'accessories' WHERE (sku LIKE 'TABL%' OR sku LIKE 'WATCH%' OR sku LIKE 'CHRG%' OR sku LIKE 'STRE%') AND category IS NULL"))
        conn.commit()

    if str(DATABASE_URL).startswith("sqlite") or str(getattr(engine, "url", "")).startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            _run_migrations(conn)
        return

    last_error: Exception | None = None
    for attempt in range(1, DB_CONNECT_RETRIES + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            with engine.connect() as conn:
                _run_migrations(conn)
            return
        except Exception as exc:
            last_error = exc
            if attempt < DB_CONNECT_RETRIES:
                time.sleep(DB_CONNECT_RETRY_DELAY_SECONDS)

    raise RuntimeError(
        f"Product Service could not connect to its configured database after "
        f"{DB_CONNECT_RETRIES} attempts. Check DATABASE_URL and database readiness."
    ) from last_error
