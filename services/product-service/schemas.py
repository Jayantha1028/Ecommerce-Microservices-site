"""Pydantic Schemas & DTOs for Product Service."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing_extensions import Annotated

from models import Product, Reservation


class ProductCreate(BaseModel):
    """Payload to create a new product and its initial inventory."""
    sku: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    description: Optional[Annotated[str, StringConstraints(max_length=2000)]] = None
    price: Annotated[Decimal, Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)]
    initial_stock: int = Field(default=0, ge=0)
    image_url: Optional[str] = None
    status: Annotated[str, StringConstraints(pattern=r"^(DRAFT|PUBLISHED|UNPUBLISHED)$")] = "PUBLISHED"


class ProductUpdate(BaseModel):
    """Payload to partially update product catalog metadata."""
    name: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]] = None
    description: Optional[Annotated[str, StringConstraints(max_length=2000)]] = None
    price: Optional[Annotated[Decimal, Field(gt=Decimal("0.00"), max_digits=12, decimal_places=2)]] = None
    image_url: Optional[str] = None
    status: Optional[Annotated[str, StringConstraints(pattern=r"^(DRAFT|PUBLISHED|UNPUBLISHED)$")]] = None


class StockUpdate(BaseModel):
    """Payload to directly overwrite inventory stock level."""
    quantity: int = Field(ge=0)


class ReservationItemCreate(BaseModel):
    """Specification of product and quantity to be reserved."""
    product_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=36)]
    quantity: int = Field(gt=0)


class ReservationCreate(BaseModel):
    """Payload to create an inventory reservation for an order."""
    order_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    items: list[ReservationItemCreate] = Field(min_length=1)


class ReleaseRequest(BaseModel):
    """Payload to release an existing reservation."""
    order_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


def product_payload(product: Product, include_description: bool = True) -> dict:
    """Serialize a Product ORM instance and its associated inventory into a dictionary."""
    stock = product.inventory.quantity if product.inventory else 0
    payload = {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "price": str(product.price),
        "status": product.status,
        "inventoryId": product.inventory.id if product.inventory else None,
        "stock": stock,
        "stockStatus": "In Stock" if stock > 0 else "Out of Stock",
        "description": product.description or "",
        "imageUrl": getattr(product, "image_url", None) or "",
        "createdAt": product.created_at.isoformat(),
        "updatedAt": product.updated_at.isoformat(),
    }
    return payload


def reservation_payload(reservation: Reservation) -> dict:
    """Serialize a Reservation ORM instance and its items into a dictionary."""
    return {
        "id": reservation.id,
        "orderId": reservation.order_id,
        "status": reservation.status,
        "items": [
            {"productId": i.product_id, "sku": i.sku, "quantity": i.quantity}
            for i in reservation.items
        ],
    }
