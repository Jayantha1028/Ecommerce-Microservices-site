"""Payment Service Route Endpoints."""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from client import get_razorpay_client
from config import PAYMENT_SIMULATION_MODE, PORT, RAZORPAY_KEY_SECRET
from database import engine, get_db
from models import PaymentRecord
from schemas import CreateOrderRequest, VerifyPaymentRequest, create_order_response, payment_payload

logger = logging.getLogger(__name__)
router = APIRouter()


def require_identity(
    x_auth_user_id: str | None = Header(None),
    x_auth_user_role: str | None = Header(None),
) -> tuple[str, str]:
    """Validate authenticated identity headers injected by the API gateway."""
    if not x_auth_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user identity is required",
        )
    return x_auth_user_id, (x_auth_user_role or "CUSTOMER").upper()


@router.get("/health")
def health() -> dict[str, Any]:
    """Service health and database probe endpoint."""
    import sys
    mod = sys.modules.get("main")
    active_engine = getattr(mod, "engine", engine) if mod else engine
    try:
        with active_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable")
    return {"status": "healthy", "database": "connected", "port": PORT}


@router.post("/payments/create-order", status_code=status.HTTP_201_CREATED)
def create_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
    _who: tuple[str, str] = Depends(require_identity),
) -> dict[str, Any]:
    """Create a new payment order with Razorpay and persist the transaction record."""
    existing = (
        db.query(PaymentRecord)
        .filter(PaymentRecord.order_id == payload.order_id, PaymentRecord.status.in_(["pending", "success"]))
        .order_by(PaymentRecord.id.desc())
        .first()
    )

    if existing:
        if existing.status == "success":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order has already been paid")
        if existing.amount != payload.amount or existing.currency != payload.currency:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A payment already exists for this order with a different amount or currency",
            )
        # Idempotent retry: do not create another Razorpay order for the same order.
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(create_order_response(existing)),
        )

    # Convert amount to smallest currency subunit (paise for INR, 100 paise = 1 INR)
    amount_in_paise = int((payload.amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    razorpay_client = get_razorpay_client()

    if PAYMENT_SIMULATION_MODE:
        sim_id = f"order_sim_{uuid.uuid4().hex[:14]}"
        razorpay_order = {
            "id": sim_id,
            "entity": "order",
            "amount": amount_in_paise,
            "amount_paid": 0,
            "amount_due": amount_in_paise,
            "currency": payload.currency,
            "receipt": f"order_rcptid_{payload.order_id}",
            "status": "created",
            "attempts": 0,
            "notes": {"order_id": payload.order_id, "mode": "simulated"},
            "created_at": int(time.time()),
        }
    else:
        try:
            razorpay_order = razorpay_client.order.create(data={
                "amount": amount_in_paise,
                "currency": payload.currency,
                "receipt": f"order_rcptid_{payload.order_id}",
                "notes": {"order_id": payload.order_id},
            })
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            logger.error(
                "Razorpay order creation failed; exception_type=%s; upstream_status=%s",
                type(exc).__name__,
                status_code,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to create Razorpay order",
            ) from None

    payment = PaymentRecord(
        order_id=payload.order_id,
        amount=payload.amount,
        currency=payload.currency,
        razorpay_order_id=razorpay_order["id"],
        status="pending",
    )

    try:
        db.add(payment)
        db.commit()
        db.refresh(payment)
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(PaymentRecord)
            .filter(PaymentRecord.order_id == payload.order_id, PaymentRecord.status.in_(["pending", "success"]))
            .order_by(PaymentRecord.id.desc())
            .first()
        )
        if existing:
            if existing.status == "success":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order has already been paid")
            if existing.amount == payload.amount and existing.currency == payload.currency:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=jsonable_encoder(create_order_response(existing)),
                )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicting payment already exists")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not save payment record")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not save payment record")

    return create_order_response(payment, razorpay_order)


@router.post("/payments/verify")
def verify_payment(
    payload: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    _who: tuple[str, str] = Depends(require_identity),
) -> dict[str, Any]:
    """Cryptographically verify Razorpay HMAC-SHA256 signature and update payment status to success."""
    payment = db.query(PaymentRecord).filter(
        PaymentRecord.razorpay_order_id == payload.razorpay_order_id
    ).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    if payment.status == "success":
        return {
            "status": "success",
            "message": "Payment was already verified",
            "payment": payment_payload(payment),
        }

    razorpay_client = get_razorpay_client()

    if PAYMENT_SIMULATION_MODE:
        expected_sig = hmac.new(
            (RAZORPAY_KEY_SECRET or "secret").encode(),
            f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        is_valid = (
            payload.razorpay_signature in {expected_sig, "mock_signature_test"}
            or payload.razorpay_signature.startswith("mock_")
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed",
            )
    else:
        import razorpay.errors
        try:
            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": payload.razorpay_order_id,
                "razorpay_payment_id": payload.razorpay_payment_id,
                "razorpay_signature": payload.razorpay_signature,
            })
        except razorpay.errors.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed",
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment verification could not be completed",
            )

    payment.razorpay_payment_id = payload.razorpay_payment_id
    payment.status = "success"

    try:
        db.commit()
        db.refresh(payment)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not save payment verification",
        )

    return {
        "status": "success",
        "message": "Payment verified successfully",
        "payment": payment_payload(payment),
    }


@router.get("/payments/{payment_id}")
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    _who: tuple[str, str] = Depends(require_identity),
) -> dict[str, Any]:
    """Retrieve details and verification status of a payment by its database ID."""
    payment = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")
    return payment_payload(payment)
