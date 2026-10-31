"""FastAPI Route Handlers for Product Catalog & Inventory."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from config import SERVICE_NAME
from database import get_db
from models import Inventory, Product, Reservation, ReservationItem
from cache import get_cached_catalog, set_cached_catalog, invalidate_catalog_cache
from schemas import (
    ProductCreate,
    ProductUpdate,
    ReleaseRequest,
    ReservationCreate,
    StockUpdate,
    product_payload,
)
from security import require_admin, require_identity

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Service health and database probe endpoint."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "UP", "service": SERVICE_NAME, "database": "UP"}
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={"status": "DOWN", "service": SERVICE_NAME, "database": "DOWN"},
        )


@router.get("/products")
def list_products(
    search: Optional[str] = Query(default=None, max_length=255),
    status_filter: Optional[str] = Query(default=None, alias="status", pattern=r"^(DRAFT|PUBLISHED|UNPUBLISHED)$"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """List products with pagination, search, status filtering, and Redis caching."""
    cache_key = f"catalog:p:{search or ''}:{status_filter or ''}:{skip}:{limit}"
    cached = get_cached_catalog(cache_key)
    if cached is not None:
        return cached

    query = select(Product).where(Product.status == "PUBLISHED")
    if status_filter:
        query = select(Product).where(Product.status == status_filter)
    if search:
        query = query.where((Product.name.ilike(f"%{search}%")) | (Product.sku.ilike(f"%{search}%")))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    products = db.scalars(query.order_by(Product.created_at.desc()).offset(skip).limit(limit)).unique().all()

    result = {
        "data": [product_payload(p, include_description=False) for p in products],
        "pagination": {"skip": skip, "limit": limit, "total": total},
    }
    set_cached_catalog(cache_key, result)
    return result


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _identity: tuple[str, str] = Depends(require_admin),
) -> dict:
    """Create a new product and initialize its corresponding inventory record."""
    if db.scalar(select(Product.id).where(Product.sku == data.sku)):
        raise HTTPException(status_code=409, detail="A product with this SKU already exists")

    product = Product(
        sku=data.sku,
        name=data.name,
        description=data.description,
        price=data.price,
        image_url=data.image_url,
        status=data.status,
    )
    product.inventory = Inventory(sku=data.sku, quantity=data.initial_stock)
    db.add(product)

    try:
        db.commit()
        db.refresh(product)
        invalidate_catalog_cache()
        return product_payload(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A product with this SKU already exists")


@router.get("/products/{product_id}")
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    x_auth_user_role: Optional[str] = Header(None),
) -> dict:
    """Retrieve full product details. Non-admins cannot view draft/unpublished products."""
    product = db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    role = (x_auth_user_role or "CUSTOMER").upper()
    if product.status != "PUBLISHED" and role not in {"ADMIN", "PRODUCT_MANAGER"}:
        raise HTTPException(status_code=404, detail="Product not found")

    return product_payload(product)


@router.api_route("/products/{product_id}", methods=["PUT", "PATCH"])
def update_product(
    product_id: str,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _identity: tuple[str, str] = Depends(require_admin),
) -> dict:
    """Partially update an existing product."""
    product = db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    try:
        db.commit()
        db.refresh(product)
        invalidate_catalog_cache()
        return product_payload(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product update conflicts with existing data")


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    _identity: tuple[str, str] = Depends(require_admin),
) -> Response:
    """Soft-delete a product by marking it UNPUBLISHED to preserve historical order references."""
    product = db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.status = "UNPUBLISHED"
    db.commit()
    invalidate_catalog_cache()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/inventory/{product_id}")
def get_inventory(product_id: str, db: Session = Depends(get_db)) -> dict:
    """Look up inventory stock levels by product ID or inventory ID."""
    inventory = db.scalar(
        select(Inventory).where((Inventory.product_id == product_id) | (Inventory.id == product_id))
    )
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")

    return {
        "id": inventory.id,
        "productId": inventory.product_id,
        "sku": inventory.sku,
        "quantity": inventory.quantity,
        "stockStatus": "In Stock" if inventory.quantity > 0 else "Out of Stock",
        "updatedAt": inventory.updated_at.isoformat(),
    }


@router.put("/inventory/{product_id}")
def update_inventory(
    product_id: str,
    data: StockUpdate,
    db: Session = Depends(get_db),
    _identity: tuple[str, str] = Depends(require_admin),
) -> dict:
    """Update inventory quantity with row-level locking."""
    inventory = db.scalar(
        select(Inventory)
        .where((Inventory.product_id == product_id) | (Inventory.id == product_id))
        .with_for_update()
    )
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")

    inventory.quantity = data.quantity
    db.commit()
    db.refresh(inventory)
    invalidate_catalog_cache()

    return {
        "id": inventory.id,
        "productId": inventory.product_id,
        "sku": inventory.sku,
        "quantity": inventory.quantity,
        "stockStatus": "In Stock" if inventory.quantity > 0 else "Out of Stock",
    }


@router.post("/inventory/reservations", status_code=status.HTTP_201_CREATED)
def reserve_inventory(
    data: ReservationCreate,
    db: Session = Depends(get_db),
    _identity: tuple[str, str] = Depends(require_identity),
) -> dict:
    """Atomically reserve inventory for an order using row-level locks (with_for_update).

    Idempotent: If a reservation for order_id already exists and is RESERVED, returns existing reservation.
    """
    existing = db.scalar(select(Reservation).where(Reservation.order_id == data.order_id))
    if existing:
        if existing.status == "RESERVED":
            return {
                "id": existing.id,
                "orderId": existing.order_id,
                "status": existing.status,
                "items": [{"productId": i.product_id, "sku": i.sku, "quantity": i.quantity} for i in existing.items],
                "idempotent": True,
            }
        raise HTTPException(status_code=409, detail=f"Order inventory reservation is already {existing.status.lower()}")

    totals: dict[str, int] = {}
    for item in data.items:
        totals[item.product_id] = totals.get(item.product_id, 0) + item.quantity

    products: list[tuple[Product, Inventory, int]] = []
    for product_id, qty in totals.items():
        product = db.scalar(select(Product).where(Product.id == product_id, Product.status == "PUBLISHED"))
        if not product or not product.inventory:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Published product or inventory not found: {product_id}")

        inventory = db.scalar(select(Inventory).where(Inventory.product_id == product_id).with_for_update())
        if inventory.quantity < qty:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail={"message": "Insufficient stock", "productId": product_id, "available": inventory.quantity, "requested": qty},
            )
        products.append((product, inventory, qty))

    reservation = Reservation(order_id=data.order_id, status="RESERVED")
    for product, inventory, qty in products:
        inventory.quantity -= qty
        reservation.items.append(ReservationItem(product_id=product.id, sku=product.sku, quantity=qty))

    db.add(reservation)
    try:
        db.commit()
        db.refresh(reservation)
        invalidate_catalog_cache()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A reservation already exists for this order")

    return {
        "id": reservation.id,
        "orderId": reservation.order_id,
        "status": reservation.status,
        "items": [{"productId": i.product_id, "sku": i.sku, "quantity": i.quantity} for i in reservation.items],
        "idempotent": False,
    }


@router.post("/inventory/reservations/release")
def release_inventory(
    data: ReleaseRequest,
    db: Session = Depends(get_db),
    _identity: tuple[str, str] = Depends(require_identity),
) -> dict:
    """Release reserved stock back to the active inventory upon order cancellation."""
    reservation = db.scalar(
        select(Reservation).where(Reservation.order_id == data.order_id).with_for_update()
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.status == "RELEASED":
        return {"orderId": reservation.order_id, "status": "RELEASED", "idempotent": True}

    for item in reservation.items:
        inventory = db.scalar(select(Inventory).where(Inventory.product_id == item.product_id).with_for_update())
        if inventory:
            inventory.quantity += item.quantity

    reservation.status = "RELEASED"
    db.commit()
    invalidate_catalog_cache()

    return {"orderId": reservation.order_id, "status": reservation.status, "idempotent": False}


@router.get("/inventory/reservations/{order_id}")
def get_reservation(
    order_id: str,
    db: Session = Depends(get_db),
    _identity: tuple[str, str] = Depends(require_identity),
) -> dict:
    """Retrieve details of an existing inventory reservation by order ID."""
    reservation = db.scalar(select(Reservation).where(Reservation.order_id == order_id))
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    return {
        "id": reservation.id,
        "orderId": reservation.order_id,
        "status": reservation.status,
        "items": [{"productId": i.product_id, "sku": i.sku, "quantity": i.quantity} for i in reservation.items],
    }
