"""Order Service Route Endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from client import _call, _create_payment_for_order, _expect, _request_headers
from config import PAYMENT_SERVICE_URL, PAYMENT_TIMEOUT, PRODUCT_SERVICE_URL, PRODUCT_TIMEOUT, SERVICE_NAME
from database import get_db
from models import Order, OrderItem
from schemas import CancelInput, OrderCreate, PaymentVerifyInput, order_payload

router = APIRouter()


def identity(
    x_auth_user_id: Optional[str] = Header(None),
    x_auth_user_role: Optional[str] = Header(None),
) -> tuple[str, str]:
    """Extract authenticated identity headers injected by the API gateway."""
    if not x_auth_user_id:
        raise HTTPException(status_code=401, detail="Authenticated user identity is required")
    return x_auth_user_id, (x_auth_user_role or "CUSTOMER").upper()


def admin_identity(who: tuple[str, str] = Depends(identity)) -> tuple[str, str]:
    """Require administrator or order manager privileges for administrative actions."""
    if who[1] not in {"ADMIN", "ORDER_MANAGER"}:
        raise HTTPException(status_code=403, detail="Administrator or order-manager role required")
    return who


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Service health and database probe endpoint."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "DOWN", "service": SERVICE_NAME, "database": "DOWN"},
        ) from exc
    return {"status": "UP", "service": SERVICE_NAME, "database": "UP"}


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Create a new order, calculate totals, reserve stock, and initialize payment."""
    user_id, role = who
    currency = data.currency.strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise HTTPException(status_code=422, detail="currency must be a three-letter code")

    quantities: dict[str, int] = {}
    for line in data.items:
        quantities[line.product_id] = quantities.get(line.product_id, 0) + line.quantity

    products: list[dict] = []
    subtotal = Decimal("0.00")

    for product_id, quantity in quantities.items():
        response = _call(
            "GET",
            f"{PRODUCT_SERVICE_URL}/products/{product_id}",
            timeout=PRODUCT_TIMEOUT,
            headers=_request_headers(user_id, role),
        )
        product = _expect(response, {200}, "product-service")

        if product.get("status") != "PUBLISHED":
            raise HTTPException(status_code=409, detail=f"Product {product_id} is not available for purchase")

        try:
            price = Decimal(str(product["price"])).quantize(Decimal("0.01"))
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Product Service returned an invalid price") from exc

        if price <= 0:
            raise HTTPException(status_code=502, detail="Product Service returned an invalid price")

        line_total = (price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += line_total
        products.append({
            "product_id": product_id,
            "product_name": product["name"],
            "sku": product["sku"],
            "price": price,
            "quantity": quantity,
            "line_total": line_total,
        })

    subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tax = Decimal("0.00")
    grand_total = subtotal + tax

    order = Order(
        user_id=user_id,
        user_email=data.user_email,
        user_name=data.user_name,
        user_address=data.user_address,
        subtotal=subtotal,
        tax=tax,
        grand_total=grand_total,
        currency=currency,
        status="PAYMENT_PENDING",
    )

    for product in products:
        order.items.append(
            OrderItem(
                product_id=product["product_id"],
                product_name=product["product_name"],
                sku=product["sku"],
                unit_price=product["price"],
                quantity=product["quantity"],
                line_total=product["line_total"],
            )
        )

    db.add(order)
    try:
        db.commit()
        db.refresh(order)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Could not persist order") from exc

    # Reserve stock only after durable order ID exists; reservation is idempotent by order ID
    try:
        reservation_response = _call(
            "POST",
            f"{PRODUCT_SERVICE_URL}/inventory/reservations",
            timeout=PRODUCT_TIMEOUT,
            headers=_request_headers(user_id, role),
            json={
                "order_id": order.id,
                "items": [{"product_id": p["product_id"], "quantity": p["quantity"]} for p in products],
            },
        )
        _expect(reservation_response, {200, 201}, "product-service")
    except HTTPException as exc:
        order.status = "CANCELLED"
        db.commit()
        raise exc

    # Attempt payment order creation; on transient failure leave PAYMENT_PENDING for client retry
    try:
        payment = _create_payment_for_order(order, user_id, role)
        order.payment_id = str(payment["payment_id"])
        order.razorpay_order_id = payment["razorpay_order_id"]
        db.commit()
    except HTTPException:
        order.status = "PAYMENT_PENDING"
        db.commit()
        db.refresh(order)
        result = order_payload(order)
        result["payment_setup"] = "RETRY_REQUIRED"
        return result

    db.refresh(order)
    result = order_payload(order)
    result["payment_setup"] = "READY"
    result["razorpay_order"] = payment.get("razorpay_order")
    return result


@router.post("/orders/{order_id}/payment")
def retry_payment(
    order_id: str,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Retry payment initialization for an order in PAYMENT_PENDING state."""
    user_id, role = who
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id and role not in {"ADMIN", "ORDER_MANAGER"}:
        raise HTTPException(status_code=403, detail="You cannot access this order")

    if order.status == "PAID":
        raise HTTPException(status_code=409, detail="Order is already paid")

    if order.status != "PAYMENT_PENDING":
        raise HTTPException(status_code=409, detail=f"Cannot create payment for order in state {order.status}")

    payment = _create_payment_for_order(order, user_id, role)
    order.payment_id = str(payment["payment_id"])
    order.razorpay_order_id = payment["razorpay_order_id"]

    db.commit()
    db.refresh(order)

    result = order_payload(order)
    result["razorpay_order"] = payment.get("razorpay_order")
    return result


@router.post("/orders/{order_id}/payment/verify")
def verify_order_payment(
    order_id: str,
    data: PaymentVerifyInput,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Verify payment signature with Payment Service and transition order to PAID."""
    user_id, role = who
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id and role not in {"ADMIN", "ORDER_MANAGER"}:
        raise HTTPException(status_code=403, detail="You cannot access this order")

    if order.status == "PAID":
        return order_payload(order)

    if not order.razorpay_order_id or data.razorpay_order_id != order.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Payment order ID does not match this order")

    response = _call(
        "POST",
        f"{PAYMENT_SERVICE_URL}/payments/verify",
        timeout=PAYMENT_TIMEOUT,
        headers=_request_headers(user_id, role),
        json=data.model_dump(),
    )
    payment = _expect(response, {200}, "payment-service")

    if payment.get("status") != "success":
        raise HTTPException(status_code=409, detail="Payment Service has not confirmed success")

    order.status = "PAID"
    order.payment_id = str(payment.get("payment", {}).get("id", order.payment_id or "")) or order.payment_id

    db.commit()
    db.refresh(order)

    return order_payload(order)


@router.get("/orders")
def list_orders(
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """List orders for the authenticated customer, or all orders if admin/manager."""
    user_id, role = who
    query = select(Order).order_by(Order.created_at.desc())

    if role not in {"ADMIN", "ORDER_MANAGER"}:
        query = query.where(Order.user_id == user_id).where(Order.status != "CANCELLED")

    orders = db.scalars(query).all()
    return {"items": [order_payload(order) for order in orders], "count": len(orders)}


@router.get("/orders/{order_id}")
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Retrieve full details of an individual order by ID."""
    user_id, role = who
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id and role not in {"ADMIN", "ORDER_MANAGER"}:
        raise HTTPException(status_code=403, detail="You cannot access this order")

    return order_payload(order)


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: str,
    data: CancelInput,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Cancel a pending order and release its reserved inventory."""
    user_id, role = who
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id and role not in {"ADMIN", "ORDER_MANAGER"}:
        raise HTTPException(status_code=403, detail="You cannot access this order")

    # Enforce 6-hour lock before delivery completion
    now_utc = datetime.now(timezone.utc)
    created_at = order.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    estimated_delivery_at = created_at + timedelta(hours=24)
    seconds_to_completion = (estimated_delivery_at - now_utc).total_seconds()
    if seconds_to_completion <= 6 * 3600:
        raise HTTPException(
            status_code=400,
            detail="Cancellation locked: Orders cannot be cancelled within 6 hours of completion.",
        )

    if order.status == "PAID":
        raise HTTPException(status_code=409, detail="Paid orders cannot be cancelled through this endpoint")

    if order.status == "CANCELLED":
        return order_payload(order)

    if order.payment_id:
        response = _call(
            "GET",
            f"{PAYMENT_SERVICE_URL}/payments/{order.payment_id}",
            timeout=PAYMENT_TIMEOUT,
            headers=_request_headers(user_id, role),
        )
        payment = _expect(response, {200}, "payment-service")
        if payment.get("status") == "success":
            raise HTTPException(
                status_code=409,
                detail="Payment is already successful; cancellation requires a refund workflow",
            )

    release = _call(
        "POST",
        f"{PRODUCT_SERVICE_URL}/inventory/reservations/release",
        timeout=PRODUCT_TIMEOUT,
        headers=_request_headers(user_id, role),
        json={"order_id": order.id},
    )
    _expect(release, {200, 404}, "product-service")

    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)

    return order_payload(order)


@router.delete("/orders/{order_id}")
def delete_or_cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Delete or cancel an order before the completion timer runs out.

    Enforces the rule: Locks cancellation when less than 6 hours remain until completion.
    Releases all reserved stock back to active inventory before deletion.
    """
    user_id, role = who
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id and role not in {"ADMIN", "ORDER_MANAGER"}:
        raise HTTPException(status_code=403, detail="You cannot access this order")

    # Enforce 6-hour lock before completion
    now_utc = datetime.now(timezone.utc)
    created_at = order.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    estimated_delivery_at = created_at + timedelta(hours=24)
    seconds_to_completion = (estimated_delivery_at - now_utc).total_seconds()

    if seconds_to_completion <= 0:
        raise HTTPException(
            status_code=400,
            detail="Order completion timer has expired; order is already fulfilled.",
        )

    if seconds_to_completion <= 6 * 3600:
        raise HTTPException(
            status_code=400,
            detail="Cancellation locked: Orders cannot be cancelled or deleted within 6 hours of completion.",
        )

    # Release reservations back to inventory
    try:
        release_res = _call(
            "POST",
            f"{PRODUCT_SERVICE_URL}/inventory/reservations/release",
            timeout=PRODUCT_TIMEOUT,
            headers=_request_headers(user_id, role),
            json={"order_id": order.id},
        )
    except Exception:
        pass

    # Delete order and its line items (cascade delete)
    db.delete(order)
    db.commit()

    return {
        "status": "DELETED",
        "message": "Order successfully cancelled and deleted. Stock restored.",
        "id": order_id,
    }

