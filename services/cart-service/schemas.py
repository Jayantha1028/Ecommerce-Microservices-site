"""Cart Service Pydantic DTO Schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    """Payload for adding an item to the user's cart."""
    product_id: str = Field(min_length=1, max_length=36)
    quantity: int = Field(default=1, gt=0, le=10000)


class CartItemUpdate(BaseModel):
    """Payload for updating the quantity of an existing cart item."""
    quantity: int = Field(gt=0, le=10000)


class CheckoutRequest(BaseModel):
    """Payload for checking out the current shopping cart."""
    currency: str = Field(default="INR", min_length=3, max_length=3)
