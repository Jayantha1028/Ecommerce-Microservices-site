"""Payment Service Razorpay SDK Client."""
from __future__ import annotations

import sys
from typing import Any
import razorpay

from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

razorpay_client: Any = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def get_razorpay_client() -> Any:
    """Retrieve the Razorpay client, respecting test monkeypatches in main module."""
    for name in ("payment_main", "main"):
        mod = sys.modules.get(name)
        if mod and hasattr(mod, "razorpay_client"):
            return getattr(mod, "razorpay_client")
    return razorpay_client
