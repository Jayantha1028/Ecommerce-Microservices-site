"""Order Service Pydantic DTO Schemas & Serialization Helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

from models import Order

COMPLETION_WINDOW_HOURS = 24
LOCK_BEFORE_COMPLETION_HOURS = 6


class OrderLineInput(BaseModel):
    """Specification of an individual product and quantity to be ordered."""
    product_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=36)]
    quantity: int = Field(gt=0, le=10000)


class OrderCreate(BaseModel):
    """Payload submitted to create a new order."""
    items: list[OrderLineInput] = Field(min_length=1, max_length=100)
    user_email: Optional[str] = Field(default=None, max_length=320)
    user_name: Optional[str] = Field(default=None, max_length=255)
    user_address: Optional[str] = Field(default=None, max_length=2000)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    discount: Optional[str] = Field(default="0.00")
    coupon_code: Optional[str] = Field(default=None, max_length=32)


class PaymentVerifyInput(BaseModel):
    """Payload containing cryptographic Razorpay payment verification signatures."""
    razorpay_order_id: str = Field(min_length=1, max_length=128)
    razorpay_payment_id: str = Field(min_length=1, max_length=128)
    razorpay_signature: str = Field(min_length=1, max_length=512)


class CancelInput(BaseModel):
    """Payload containing optional reason for order cancellation."""
    reason: Optional[str] = Field(default=None, max_length=500)


class StatusUpdateIn(BaseModel):
    """Payload for updating order tracking / shipment status."""
    status: str = Field(min_length=3, max_length=30)


def order_payload(order: Order, include_payment: bool = True) -> dict:
    """Serialize an Order and its line items into a standard response dictionary."""
    now_utc = datetime.now(timezone.utc)
    created_at = order.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    estimated_delivery_at = created_at + timedelta(hours=COMPLETION_WINDOW_HOURS)
    cancellation_locked_at = estimated_delivery_at - timedelta(hours=LOCK_BEFORE_COMPLETION_HOURS)

    seconds_to_completion = max(0, int((estimated_delivery_at - now_utc).total_seconds()))
    seconds_to_lock = int((cancellation_locked_at - now_utc).total_seconds())

    # Can cancel if order is not already cancelled/completed AND more than 6h remain before completion
    can_cancel = (
        order.status not in {"CANCELLED", "COMPLETED", "DELIVERED"}
        and seconds_to_lock > 0
    )

    result = {
        "id": order.id,
        "user_id": order.user_id,
        "user_email": order.user_email,
        "user_name": order.user_name,
        "user_address": order.user_address,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "sku": item.sku,
                "unit_price": str(item.unit_price),
                "quantity": item.quantity,
                "line_total": str(item.line_total),
            }
            for item in order.items
        ],
        "subtotal": str(order.subtotal),
        "discount": str(getattr(order, "discount", Decimal("0.00")) or "0.00"),
        "coupon_code": getattr(order, "coupon_code", None),
        "tax": str(order.tax),
        "grand_total": str(order.grand_total),
        "currency": order.currency,
        "status": order.status,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "estimated_delivery_at": estimated_delivery_at.isoformat(),
        "cancellation_locked_at": cancellation_locked_at.isoformat(),
        "can_cancel": can_cancel,
        "seconds_to_lock": max(0, seconds_to_lock),
        "seconds_to_completion": seconds_to_completion,
    }
    if include_payment:
        result["payment"] = {
            "payment_id": order.payment_id,
            "razorpay_order_id": order.razorpay_order_id,
        }
    return result
