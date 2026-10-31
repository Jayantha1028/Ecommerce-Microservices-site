# E-Commerce Platform — Technical & Development Guide (`DEVELOPMENT.md`)

A comprehensive developer reference explaining the system architecture, technology stack, library ecosystems, design patterns, and annotated code snippets across all microservices.

---

## 📑 Table of Contents
1. [Core Technology Stack & System Topology](#1-core-technology-stack--system-topology)
2. [Microservices Breakdown & Responsibilities](#2-microservices-breakdown--responsibilities)
3. [Library & Framework Ecosystem](#3-library--framework-ecosystem)
4. [Key Architectural Patterns & Code Snippets](#4-key-architectural-patterns--code-snippets)
   - [4.1 API Gateway Reverse Proxy & Header Sanitization](#41-api-gateway-reverse-proxy--header-sanitization)
   - [4.2 Constant-Time Scrypt Hashing & Timing-Attack Defense](#42-constant-time-scrypt-hashing--timing-attack-defense)
   - [4.3 Pessimistic Concurrency & Row-Level Locking (`SELECT FOR UPDATE`)](#43-pessimistic-concurrency--row-level-locking-select-for-update)
   - [4.4 Distributed Checkout Saga & Stock Reservation](#44-distributed-checkout-saga--stock-reservation)
   - [4.5 Cryptographic Payment Verification (HMAC-SHA256)](#45-cryptographic-payment-verification-hmac-sha256)
   - [4.6 Order Lifecycle & 6-Hour Cancellation Lock Rule](#46-order-lifecycle--6-hour-cancellation-lock-rule)
   - [4.7 Encapsulated Storefront & Hidden Admin Gate](#47-encapsulated-storefront--hidden-admin-gate)
5. [Database Architecture & Connection Management](#5-database-architecture--connection-management)
6. [Local Development, Docker & Testing Guide](#6-local-development-docker--testing-guide)

---

## 1. Core Technology Stack & System Topology

The platform is designed around the **Database-per-Service** pattern, decoupling domain boundaries so no service accesses another's database directly.

| Layer | Technologies Used | Key Characteristics |
|---|---|---|
| **API Gateway** | FastAPI, Uvicorn, HTTPX, PyJWT | Single entry point (port `8000`), reverse proxying, JWT verification, and security header injection. |
| **Microservices** | FastAPI (Python 3.11+ / 3.12+), Starlette, Pydantic v2 | 5 isolated services: Auth (`:8001`), Product (`:8002`), Payment (`:8003`), Order (`:8004`), Cart (`:8005`). |
| **Persistence** | PostgreSQL 16 (x5 instances) | Dedicated databases: `auth_db`, `product_db`, `payment_db`, `order_db`, `cart_db`. |
| **Cache & In-Memory**| Redis 7.2 | High-throughput product catalog caching and read-through caching. |
| **Payments** | Razorpay SDK, HMAC-SHA256 | Live and offline sandbox simulation modes. |
| **Containerization** | Docker Compose v2, Kubernetes 1.28+ | Multi-stage Dockerfiles, isolated internal bridge subnets, PVC storage. |

```
                              [ Browser / Client ]
                                       │
                                       ▼ (Port 8000)
                        ┌──────────────────────────────┐
                        │     API Gateway Service      │
                        │ (FastAPI Reverse Proxy & JWT)│
                        └──────────────┬───────────────┘
                                       │
         ┌──────────────────┬──────────┴────────┬──────────────────┬─────────────────┐
         ▼                  ▼                   ▼                  ▼                 ▼
 ┌───────────────┐  ┌───────────────┐   ┌───────────────┐  ┌───────────────┐ ┌───────────────┐
 │   User/Auth   │  │    Product    │   │     Cart      │  │     Order     │ │    Payment    │
 │ Service :8001 │  │ Service :8002 │   │ Service :8005 │  │ Service :8004 │ │ Service :8003 │
 └───────┬───────┘  └───────┬───────┘   └───────┬───────┘  └───────┬───────┘ └───────┬───────┘
         │                  │                   │                  │                 │
         ▼                  ▼                   ▼                  ▼                 ▼
  [( auth-db )]      [( product-db )]    [( cart-db )]      [( order-db )]    [( payment-db )]
```

---

## 2. Microservices Breakdown & Responsibilities

### 1. `api-gateway` (Port `8000`)
- **Public Surface:** Reverse proxies `/auth/*`, `/users/*`, `/products/*`, `/inventory/*`, `/cart/*`, `/orders/*`, `/payments/*`.
- **Storefront Host:** Serves the responsive, modern single-page storefront application (`GET /`).
- **Security Perimeter:** Strips hop-by-hop headers, verifies incoming Bearer JWT tokens, and injects trusted downstream headers (`X-Auth-User-Id`, `X-Auth-User-Role`, `X-Correlation-Id`).

### 2. `user-auth-service` (Port `8001`)
- **Domain:** User registration, one-time 6-digit email verification codes, login with constant-time password verification, JWT token issuance, and user profile management (`GET /auth/profile`, `PUT /auth/profile`).
- **Database:** `auth_db` (`users`, `user_profiles`, `verification_codes`, `login_history`).

### 3. `product-service` (Port `8002`)
- **Domain:** Published catalog discovery, product CRUD with image URL support, category filtering, inventory management, and atomic stock reservation using PostgreSQL row-level locks.
- **Database:** `product_db` (`products`, `inventory`, `inventory_reservations`, `inventory_reservation_items`).

### 4. `payment-service` (Port `8003`)
- **Domain:** Razorpay order generation, cryptographic HMAC-SHA256 signature verification, idempotent payment creation, and sandbox simulation mode (`PAYMENT_SIMULATION_MODE=true`).
- **Database:** `payment_db` (`payments`).

### 5. `order-service` (Port `8004`)
- **Domain:** Multi-item checkout coordination, price freezing, inventory reservation calls, payment status synchronization, 24-hour delivery countdown timer, and 6-hour cancellation lock enforcement.
- **Database:** `order_db` (`orders`, `order_items`).

### 6. `cart-service` (Port `8005`)
- **Domain:** Persistent customer carts, live product validation, quantity adjustment, and checkout dispatch to the Order Service.
- **Database:** `cart_db` (`cart_items`).

---

## 3. Library & Framework Ecosystem

Each service specifies minimal, pinned dependencies inside its `requirements.txt`:

| Library | Version | Purpose in Codebase |
|---|---|---|
| `fastapi` | `^0.115.0` | High-performance asynchronous web framework providing routing, OpenAPI documentation, and dependency injection. |
| `uvicorn` | `^0.31.0` | Production ASGI web server running microservice processes. |
| `sqlalchemy` | `^2.0.35` | Modern Declarative 2.0 ORM with type annotations (`Mapped`, `mapped_column`) and connection pooling. |
| `pydantic` | `^2.9.0` | Data validation, payload deserialization, and schema enforcement using `EmailStr` and `StringConstraints`. |
| `psycopg2-binary` | `^2.9.9` | C-optimized PostgreSQL database adapter. |
| `pyjwt` | `^2.9.0` | JSON Web Token encoding and decoding with HS256 algorithm and clock skew leeway. |
| `httpx` | `^0.27.2` | Next-generation asynchronous HTTP client with connection pooling for inter-service RPC calls. |
| `redis` | `^5.1.0` | High-throughput in-memory caching and distributed lock primitives. |
| `razorpay` | `^1.4.1` | Official payment gateway client for order creation and HMAC signature verification. |
| `pytest` | `^8.3.0` | Automated test runner for integration and unit test suites. |

---

## 4. Key Architectural Patterns & Code Snippets

### 4.1 API Gateway Reverse Proxy & Header Sanitization
**Location:** [`services/api-gateway/main.py`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/services/api-gateway/main.py)

The Gateway inspects every incoming HTTP request, strips dangerous hop-by-hop headers and client-spoofed headers, decodes the JWT, and forwards authenticated claims securely:

```python
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    path = "/" + path if path else "/"
    upstream = service_for(path)
    if not upstream:
        return JSONResponse(status_code=404, content={"detail": "No service route configured"})

    # 1. Cryptographically verify JWT bearer token
    auth_payload = verify_bearer(request.headers.get("authorization"))
    if requires_auth(request.method, path) and auth_payload is None:
        return JSONResponse(status_code=401, content={"detail": "A valid Bearer token is required"})

    # 2. Sanitize headers to prevent header injection attacks
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS and k.lower() not in {"x-auth-user-id", "x-auth-user-role"}
    }

    # 3. Inject verified identity claims from trusted Gateway
    if auth_payload:
        headers["x-auth-user-id"] = str(auth_payload.get("sub") or auth_payload.get("id") or "")
        headers["x-auth-user-role"] = str(auth_payload.get("role") or "CUSTOMER")

    # 4. Propagate distributed tracing correlation ID
    headers["x-correlation-id"] = request.headers.get("x-correlation-id") or uuid.uuid4().hex

    # 5. Forward request with pooled HTTP client
    req = http_client.build_request(
        method=request.method,
        url=f"{upstream}{path}",
        headers=headers,
        content=await request.body(),
        params=request.query_params,
        timeout=TIMEOUT_SECONDS,
    )
    resp = await http_client.send(req, stream=True)
    return StreamingResponse(resp.aiter_bytes(), status_code=resp.status_code, headers=dict(resp.headers))
```

---

### 4.2 Constant-Time Scrypt Hashing & Timing-Attack Defense
**Location:** [`services/auth-service/security.py`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/services/auth-service/security.py)

To prevent username enumeration via response-timing discrepancies, the Auth Service executes a full `scrypt` hashing derivation against a pre-calculated dummy hash even if the account does not exist:

```python
# Fixed dummy hash with identical scrypt cost parameters (N=16384, r=8, p=1)
DUMMY_PASSWORD_HASH = (
    "scrypt$16384$8$1$676f6f676c6564756d6d7973616c74$5f70a09e0a0d4c1b97ad8949811b3e8c"
)

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Constant-time verification of scrypt-hashed passwords."""
    try:
        scheme, n, r, p, salt_hex, hash_hex = hashed_password.split("$")
        computed = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            maxmem=64 * 1024 * 1024,
        )
        return hmac.compare_digest(computed.hex(), hash_hex)
    except Exception:
        return False

# In login route:
user = db.scalar(select(User).where(User.email == data.email.lower()))
if not user:
    # Timing attack mitigation: Execute dummy hash so response time matches real user check
    check_password(data.password, DUMMY_PASSWORD_HASH)
    raise HTTPException(status_code=401, detail="Invalid email or password")
```

---

### 4.3 Pessimistic Concurrency & Row-Level Locking (`SELECT FOR UPDATE`)
**Location:** [`services/product-service/routes.py`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/services/product-service/routes.py)

During inventory reservations, concurrent checkouts for the same product are serialized at the database row level to prevent overselling:

```python
@router.post("/inventory/reservations", status_code=201)
def reserve_inventory(data: ReservationInput, db: Session = Depends(get_db)):
    # 1. Idempotency check: Return existing reservation if order was already reserved
    existing = db.scalar(select(InventoryReservation).where(InventoryReservation.order_id == data.order_id))
    if existing:
        return reservation_payload(existing)

    # 2. Acquire exclusive pessimistic row locks on inventory rows
    for item in data.items:
        inv = db.scalar(
            select(Inventory)
            .where(Inventory.product_id == item.product_id)
            .with_for_update()  # <-- Emits SELECT ... FOR UPDATE in PostgreSQL
        )
        if not inv:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Inventory for product {item.product_id} not found")

        available = inv.quantity - inv.reserved_quantity
        if available < item.quantity:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient inventory. Requested: {item.quantity}, Available: {available}",
            )

        # 3. Atomically increment reserved stock count
        inv.reserved_quantity += item.quantity

    # 4. Persist reservation record and commit transaction
    reservation = InventoryReservation(order_id=data.order_id, status="ACTIVE")
    db.add(reservation)
    db.commit()
    return reservation_payload(reservation)
```

---

### 4.4 Distributed Checkout Saga & Stock Reservation
**Location:** [`services/order-service/routes.py`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/services/order-service/routes.py)

The Order Service acts as the coordinator (Saga orchestrator) for multi-item checkouts:

```python
# Step 1: Snapshot unit prices from Product Service to freeze prices against changes
snapshot_res = _call("GET", f"{PRODUCT_SERVICE_URL}/products/{item.product_id}")
frozen_price = snapshot_res["price"]

# Step 2: Persist Order in order_db with status PAYMENT_PENDING
order = Order(user_id=user_id, status="PAYMENT_PENDING", grand_total=total)
db.add(order)
db.commit()

# Step 3: Call Product Service to reserve stock atomically
reservation_res = _call(
    "POST",
    f"{PRODUCT_SERVICE_URL}/inventory/reservations",
    json={"order_id": order.id, "items": reservation_items},
)

# Step 4: Call Payment Service to initialize Razorpay order
payment_res = _call(
    "POST",
    f"{PAYMENT_SERVICE_URL}/payments/create-order",
    json={"order_id": order.id, "amount": float(order.grand_total)},
)
order.payment_id = payment_res["id"]
db.commit()
```

---

### 4.5 Cryptographic Payment Verification (HMAC-SHA256)
**Location:** [`services/payment-service/routes.py`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/services/payment-service/routes.py)

Verifies Razorpay payment signatures using HMAC-SHA256 digests over the `razorpay_order_id|razorpay_payment_id` message payload:

```python
def verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(
        key=RAZORPAY_KEY_SECRET.encode("utf-8"),
        msg=message,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

### 4.6 Order Lifecycle & 6-Hour Cancellation Lock Rule
**Location:** [`services/order-service/routes.py`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/services/order-service/routes.py)

Orders carry an estimated 24-hour completion window. Customers can cancel anytime until **6 hours before completion**, after which final packaging locks cancellation:

```python
COMPLETION_WINDOW_HOURS = 24
LOCK_BEFORE_COMPLETION_HOURS = 6

@router.delete("/orders/{order_id}")
def delete_or_cancel_order(order_id: str, db: Session = Depends(get_db), who: tuple = Depends(identity)):
    user_id, role = who
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Calculate remaining time until delivery completion
    now_utc = datetime.now(timezone.utc)
    estimated_delivery_at = order.created_at + timedelta(hours=COMPLETION_WINDOW_HOURS)
    seconds_to_completion = (estimated_delivery_at - now_utc).total_seconds()

    if seconds_to_completion <= 0:
        raise HTTPException(status_code=400, detail="Order is already completed.")

    # 6-Hour Lock Rule Enforcement
    if seconds_to_completion <= LOCK_BEFORE_COMPLETION_HOURS * 3600:
        raise HTTPException(
            status_code=400,
            detail="Cancellation locked: Orders cannot be cancelled within 6 hours of completion.",
        )

    # Release reserved inventory back to catalog
    _call("POST", f"{PRODUCT_SERVICE_URL}/inventory/reservations/release", json={"order_id": order.id})

    # Delete order record
    db.delete(order)
    db.commit()
    return {"status": "DELETED", "message": "Order cancelled and deleted. Stock restored."}
```

---

### 4.7 Encapsulated Storefront & Hidden Admin Gate
**Location:** [`services/api-gateway/portal.py`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/services/api-gateway/portal.py)

To keep customer views clean and secure:
1. **Customer Encapsulation:** Storefront hides internal DB IDs, administrative toggles, and internal microservice health metrics.
2. **Hidden Admin Gate:** Unlocked exclusively through:
   - Secret key combination: `Ctrl + Shift + A`
   - 5 consecutive clicks on the brand logo
   - Secret URL parameter: `?admin_gate=1`
   - Followed by admin password authentication (`AdminPassword123!`).

```javascript
// Secret Keybinding Listener
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
    e.preventDefault();
    openAdminAuthModal();
  }
});
```

---

## 5. Database Architecture & Connection Management

Every microservice manages an independent PostgreSQL database session using scoped SQLAlchemy sessions and connection pooling:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # Number of permanent connections maintained in pool
    max_overflow=20,     # Maximum additional burst connections under load
    pool_timeout=30,     # Connection checkout timeout in seconds
    pool_pre_ping=True,  # Proactively test connection vitality before checkout
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Table Directory Across 5 Databases

1. **`auth_db`**: `users`, `user_profiles`, `verification_codes`, `login_history`.
2. **`product_db`**: `products`, `inventory`, `inventory_reservations`, `inventory_reservation_items`.
3. **`payment_db`**: `payments`.
4. **`order_db`**: `orders`, `order_items`.
5. **`cart_db`**: `cart_items`.

---

## 6. Local Development, Docker & Testing Guide

### 1. Build and Run Entire Platform
```bash
docker compose up -d --build
```

### 2. Verify Container Health
```bash
docker compose ps
```
All 12 containers will display `Up (healthy)`.

### 3. Run Automated 32/32 Test Suite
```bash
# macOS / Linux / WSL
bash scripts/test_all.sh

# Windows PowerShell
.\scripts\test_all.ps1
```

### 4. Database CSV Export / Restore
```bash
# Export all 11 tables to CSV snapshots in data/backups/
python3 scripts/export_csv_backup.py

# Restore all tables from CSV snapshots
python3 scripts/restore_csv_backup.py
```

### 5. Access Interactive APIs & Storefront
- **Storefront:** [http://localhost:8000](http://localhost:8000)
- **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Admin Password:** `AdminPassword123!`
- **Demo Customer:** `customer@example.com` / `CustomerPassword123!`
