"""Payment Service Pydantic DTO Schemas & Payload Helpers."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from models import PaymentRecord


class CreateOrderRequest(BaseModel):
    """Request payload to initiate a new Razorpay payment order."""
    order_id: str = Field(min_length=1, max_length=128)
    amount: Decimal = Field(gt=Decimal("0"), max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("order_id")
    @classmethod
    def strip_order_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("order_id must not be blank")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a three-letter currency code")
        return value


class VerifyPaymentRequest(BaseModel):
    """Request payload with Razorpay client callback signatures for verification."""
    razorpay_order_id: str = Field(min_length=1, max_length=128)
    razorpay_payment_id: str = Field(min_length=1, max_length=128)
    razorpay_signature: str = Field(min_length=1, max_length=512)


class PaymentOut(BaseModel):
    """Public representation of a payment transaction record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: str
    amount: Decimal
    currency: str
    razorpay_order_id: str
    razorpay_payment_id: str | None
    status: str
    created_at: datetime


def payment_payload(payment: PaymentRecord) -> dict[str, Any]:
    """Serialize a PaymentRecord model into a dictionary."""
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
        "status": payment.status,
        "created_at": payment.created_at,
    }


def create_order_response(
    payment: PaymentRecord,
    razorpay_order: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format standard response returned after payment order creation."""
    response: dict[str, Any] = {
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "razorpay_order_id": payment.razorpay_order_id,
        "status": payment.status,
    }
    if razorpay_order is not None:
        response["razorpay_order"] = razorpay_order
    return response
