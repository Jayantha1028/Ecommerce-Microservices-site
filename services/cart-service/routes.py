"""Cart Service Route Endpoints."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from client import fetch_product, get_http_client
from config import ORDER_SERVICE_URL, ORDER_TIMEOUT, SERVICE_NAME
from database import get_db
from models import CartItem
from schemas import CartItemAdd, CartItemUpdate, CheckoutRequest

router = APIRouter()


def identity(
    x_auth_user_id: Optional[str] = Header(None),
    x_auth_user_role: Optional[str] = Header(None),
) -> tuple[str, str]:
    """Extract authenticated identity headers injected by the API gateway."""
    if not x_auth_user_id:
        raise HTTPException(status_code=401, detail="Authenticated user identity is required")
    return x_auth_user_id, (x_auth_user_role or "CUSTOMER").upper()


def find_item(db: Session, user_id: str, product_id: str) -> Optional[CartItem]:
    """Look up an existing cart item for a given user and product ID."""
    return db.scalar(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    )


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Service health and database probe endpoint."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "UP", "service": SERVICE_NAME, "database": "UP"}
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "DOWN", "service": SERVICE_NAME, "database": "DOWN"},
        ) from exc


@router.post("/cart/items", status_code=201)
def add_to_cart(
    item: CartItemAdd,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Add a product quantity to the user's shopping cart after validating stock."""
    user_id, role = who

    # Verify that the product is active and published
    product = fetch_product(item.product_id, user_id, role)
    if product.get("status") != "PUBLISHED":
        raise HTTPException(status_code=409, detail="Product is not available for purchase")

    # Calculate cumulative quantity if product already exists in cart
    existing = find_item(db, user_id, item.product_id)
    new_quantity = item.quantity + (existing.quantity if existing else 0)

    # Validate stock limits
    if int(product.get("stock", 0)) < new_quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough stock. Available: {product.get('stock', 0)}, requested: {new_quantity}",
        )

    if existing:
        existing.quantity = new_quantity
    else:
        db.add(CartItem(user_id=user_id, product_id=item.product_id, quantity=item.quantity))

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cart item conflicted with another update; retry the request",
        ) from exc

    return {
        "message": f"{product['name']} added to cart",
        "product_id": item.product_id,
        "quantity_in_cart": new_quantity,
    }


@router.get("/cart")
def view_cart(
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """View the calling user's cart with live prices, product names, and subtotal."""
    user_id, role = who
    rows = db.scalars(select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id)).all()

    items = []
    total = Decimal("0.00")

    for row in rows:
        try:
            product = fetch_product(row.product_id, user_id, role)
        except HTTPException as exc:
            if exc.status_code in {503, 504, 502}:
                raise
            items.append({
                "product_id": row.product_id,
                "quantity": row.quantity,
                "available": False,
                "note": "Product no longer exists",
            })
            continue

        price = Decimal(str(product["price"]))
        subtotal = (price * row.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += subtotal

        items.append({
            "product_id": row.product_id,
            "name": product["name"],
            "sku": product.get("sku"),
            "price": str(price),
            "quantity": row.quantity,
            "subtotal": str(subtotal),
            "in_stock": int(product.get("stock", 0)) >= row.quantity,
            "available": True,
        })

    return {
        "items": items,
        "total": str(total.quantize(Decimal("0.01"))),
        "count": len(items),
    }


@router.put("/cart/items/{product_id}")
def update_item(
    product_id: str,
    updated: CartItemUpdate,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Update the quantity of a specific product line in the user's cart."""
    user_id, role = who
    row = find_item(db, user_id, product_id)
    if not row:
        raise HTTPException(status_code=404, detail="Item not in cart")

    # Verify inventory availability for updated quantity
    product = fetch_product(product_id, user_id, role)
    if int(product.get("stock", 0)) < updated.quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough stock. Available: {product.get('stock', 0)}, requested: {updated.quantity}",
        )

    row.quantity = updated.quantity
    db.commit()

    return {
        "message": "Cart quantity updated",
        "product_id": product_id,
        "quantity": updated.quantity,
    }


@router.delete("/cart/items/{product_id}", status_code=200)
def remove_item(
    product_id: str,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Delete a single product line item from the user's cart."""
    user_id, _role = who
    row = find_item(db, user_id, product_id)
    if not row:
        raise HTTPException(status_code=404, detail="Item not in cart")

    db.delete(row)
    db.commit()

    return {"message": "Item removed from cart"}


@router.delete("/cart", status_code=200)
def clear_cart(
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Remove all items from the current user's shopping cart."""
    user_id, _role = who
    db.query(CartItem).filter(CartItem.user_id == user_id).delete(synchronize_session=False)
    db.commit()

    return {"message": "Cart cleared"}


@router.post("/cart/checkout", status_code=201)
def checkout(
    details: CheckoutRequest,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Submit the contents of the cart to create an Order and clear the cart upon success."""
    user_id, role = who
    rows = db.scalars(select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id)).all()

    if not rows:
        raise HTTPException(status_code=400, detail="Cart is empty")

    payload = {
        "items": [{"product_id": row.product_id, "quantity": row.quantity} for row in rows],
        "currency": details.currency.upper(),
    }

    client = get_http_client()
    try:
        response = client.post(
            f"{ORDER_SERVICE_URL}/orders",
            json=payload,
            timeout=ORDER_TIMEOUT,
            headers={"X-Auth-User-Id": user_id, "X-Auth-User-Role": role},
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Order Service timed out; check order history before retrying",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Order Service is unavailable") from exc

    if response.status_code not in {200, 201}:
        try:
            detail = response.json().get("detail", "Order creation failed")
        except Exception:
            detail = "Order creation failed"
        raise HTTPException(
            status_code=response.status_code if response.status_code in {400, 404, 409, 422} else 502,
            detail=detail,
        )

    order = response.json()

    # Clear cart only after Order Service confirms durable order creation
    db.query(CartItem).filter(CartItem.user_id == user_id).delete(synchronize_session=False)
    db.commit()

    return {
        "status": "success",
        "order": order,
        "message": "Checkout submitted; continue payment using the returned order details",
    }
