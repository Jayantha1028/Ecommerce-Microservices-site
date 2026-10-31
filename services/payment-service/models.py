"""Payment Service SQLAlchemy ORM Models & Indexes."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class PaymentRecord(Base):
    """Represents a financial transaction record linked to an e-commerce order."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    razorpay_order_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


# Partial index allowing only one active (pending or success) payment record per order
Index(
    "uq_payments_active_order",
    PaymentRecord.order_id,
    unique=True,
    postgresql_where=text("status IN ('pending', 'success')"),
    sqlite_where=text("status IN ('pending', 'success')"),
)
