"""Cart Service Outbound HTTP Client & Inter-Service Communications."""
from __future__ import annotations

import sys
import time
from typing import Optional
import httpx
from fastapi import HTTPException

from config import ORDER_TIMEOUT, PRODUCT_SERVICE_URL, PRODUCT_TIMEOUT

http_client: httpx.Client | None = None


def get_http_client() -> httpx.Client:
    """Retrieve or lazily initialize the shared HTTP client for outbound service requests.
    
    Inspects cart_main or main to support test monkeypatching.
    """
    for name in ("cart_main", "main"):
        mod = sys.modules.get(name)
        if mod and hasattr(mod, "get_http_client"):
            candidate = getattr(mod, "get_http_client")
            if candidate is not get_http_client:
                return candidate()

    global http_client
    if http_client is None or http_client.is_closed:
        http_client = httpx.Client(timeout=ORDER_TIMEOUT)
    return http_client


def fetch_product(product_id: str, user_id: str, role: str) -> dict:
    """Fetch live product details and inventory availability with transient retry."""
    client = get_http_client()
    for attempt in range(2):
        try:
            response = client.get(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}",
                timeout=PRODUCT_TIMEOUT,
                headers={"X-Auth-User-Id": user_id, "X-Auth-User-Role": role},
            )
            if response.status_code in {502, 503} and attempt == 0:
                time.sleep(0.05)
                continue
            break
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            if attempt == 0:
                time.sleep(0.05)
                continue
            if isinstance(exc, httpx.TimeoutException):
                raise HTTPException(status_code=504, detail="Product Service timed out") from exc
            raise HTTPException(status_code=503, detail="Product Service is unavailable") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=503, detail="Product Service is unavailable") from exc

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Product Service could not retrieve product")

    return response.json()
