"""Cart Service SQLAlchemy ORM Models."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class CartItem(Base):
    """Cart item line representing a product quantity in a specific user's shopping cart."""

    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class CartCoupon(Base):
    """Active promo discount coupon applied to a user's shopping cart."""

    __tablename__ = "cart_coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'PERCENT' or 'FLAT'
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    min_order_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
