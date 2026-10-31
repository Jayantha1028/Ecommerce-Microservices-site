"""Order Service HTTP Client & Inter-Service Communications."""
from __future__ import annotations

import sys
import time
from typing import Optional
import httpx
from fastapi import HTTPException

from config import PAYMENT_SERVICE_URL, PAYMENT_TIMEOUT
from models import Order

http_client: httpx.Client | None = None


def get_http_client() -> httpx.Client:
    """Retrieve or initialize the shared HTTP client for outbound service requests.
    
    Supports monkeypatching in unit tests via main module inspection.
    """
    for name in ("order_main", "main"):
        mod = sys.modules.get(name)
        if mod and hasattr(mod, "get_http_client"):
            candidate = getattr(mod, "get_http_client")
            if candidate is not get_http_client:
                return candidate()

    global http_client
    if http_client is None or http_client.is_closed:
        http_client = httpx.Client(timeout=PAYMENT_TIMEOUT)
    return http_client


def _request_headers(user_id: str, role: str) -> dict[str, str]:
    """Construct downstream authentication headers for internal inter-service HTTP calls."""
    return {"X-Auth-User-Id": user_id, "X-Auth-User-Role": role}


def _call(method: str, url: str, *, timeout: float, headers: dict[str, str], max_retries: int = 2, **kwargs) -> httpx.Response:
    """Execute an outbound HTTP request with retry, backoff, standard timeout and error handling."""
    client = get_http_client()
    for attempt in range(max_retries + 1):
        try:
            response = client.request(method, url, timeout=timeout, headers=headers, **kwargs)
            if response.status_code in {502, 503} and attempt < max_retries and method.upper() in {"GET", "HEAD"}:
                time.sleep(0.05 * (2 ** attempt))
                continue
            return response
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            if attempt < max_retries:
                time.sleep(0.05 * (2 ** attempt))
                continue
            if isinstance(exc, httpx.TimeoutException):
                raise HTTPException(status_code=504, detail="A dependent service timed out") from exc
            raise HTTPException(status_code=502, detail="A dependent service is unavailable") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="A dependent service is unavailable") from exc
    raise HTTPException(status_code=502, detail="A dependent service is unavailable")


def _expect(response: httpx.Response, expected: set[int], service: str) -> dict:
    """Validate that an outbound HTTP response matches expected status codes and return JSON."""
    if response.status_code not in expected:
        try:
            detail = response.json().get("detail", "request failed")
        except Exception:
            detail = "request failed"
        mapped = response.status_code if response.status_code in {400, 404, 409, 422} else 502
        raise HTTPException(status_code=mapped, detail={"service": service, "message": detail})

    if not response.content:
        return {}

    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"{service} returned an invalid response") from exc


def _create_payment_for_order(order: Order, user_id: str, role: str) -> dict:
    """Initialize a payment with the Payment Service for a pending order."""
    if order.payment_id and order.razorpay_order_id:
        return {
            "payment_id": order.payment_id,
            "razorpay_order_id": order.razorpay_order_id,
            "status": "pending",
        }

    response = _call(
        "POST",
        f"{PAYMENT_SERVICE_URL}/payments/create-order",
        timeout=PAYMENT_TIMEOUT,
        headers=_request_headers(user_id, role),
        json={"order_id": order.id, "amount": str(order.grand_total), "currency": order.currency},
    )
    payment = _expect(response, {200, 201}, "payment-service")

    if not payment.get("payment_id") or not payment.get("razorpay_order_id"):
        raise HTTPException(status_code=502, detail="Payment Service returned incomplete payment details")

    return payment
