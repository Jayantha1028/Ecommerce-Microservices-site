"""SQLAlchemy ORM Models for Product & Inventory."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Product(Base):
    """Product catalog item with SKU, naming, pricing, and lifecycle status."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="accessories", nullable=False, index=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PUBLISHED", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # 1:1 relationship with inventory tracking
    inventory: Mapped["Inventory"] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # 1:N relationship with customer reviews
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(Review.created_at)",
    )


class Inventory(Base):
    """Stock level entity linked 1:1 with a Product."""

    __tablename__ = "inventory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    product: Mapped[Product] = relationship(back_populates="inventory")


class Reservation(Base):
    """Stock reservation record linked to a pending order to prevent over-selling."""

    __tablename__ = "inventory_reservations"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_inventory_reservation_order"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="RESERVED", nullable=False)  # 'RESERVED' or 'RELEASED'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    items: Mapped[list["ReservationItem"]] = relationship(
        back_populates="reservation",
        cascade="all, delete-orphan",
    )


class ReservationItem(Base):
    """Line item within an inventory reservation detailing the reserved quantity."""

    __tablename__ = "inventory_reservation_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reservation_id: Mapped[str] = mapped_column(
        ForeignKey("inventory_reservations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(String(36), nullable=False)
    sku: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    reservation: Mapped[Reservation] = relationship(back_populates="items")


class Review(Base):
    """Customer product review and star rating record."""

    __tablename__ = "product_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String(255), default="Verified Buyer", nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 5
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    product: Mapped[Product] = relationship(back_populates="reviews")
