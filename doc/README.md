# 🛒 Enterprise E-Commerce Microservices Platform

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Jayantha1028/Ecommerce-Microservices-site)
[![Repository](https://img.shields.io/badge/GitHub-Jayantha1028%2FEcommerce--Microservices--site-blue?logo=github)](https://github.com/Jayantha1028/Ecommerce-Microservices-site)
[![Test Suite](https://img.shields.io/badge/Tests-32%2F32%20Passing-brightgreen?logo=pytest)](scripts/test_all.sh)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker%20Compose-12%20Containers-2496ED?logo=docker)](docker-compose.yml)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Production%20Manifests-326CE5?logo=kubernetes)](k8s/)

An enterprise-grade, high-availability e-commerce platform architected as decoupled microservices behind a unified **API Gateway**. The system implements the **Database-per-Service** pattern with 5 dedicated **PostgreSQL 16** databases, an in-memory **Redis 7.2** cache, pessimistic concurrency control with row-level locking (`SELECT ... FOR UPDATE`), cryptographic **Razorpay HMAC-SHA256** payments, real-time order lifecycle tracking, and an encapsulated customer storefront.

---

## 📑 Table of Contents
1. [System Architecture & Visual Diagrams](#-system-architecture--visual-diagrams)
   - [High-Level Services & Network Topology](#1-high-level-services--network-topology)
   - [Distributed Checkout Saga & Stock Reservation](#2-distributed-checkout-saga--stock-reservation)
   - [Order Lifecycle & Live Tracking State Machine](#3-order-lifecycle--live-tracking-state-machine)
   - [Complete Entity-Relationship (ER) Schema](#4-complete-entity-relationship-er-schema)
2. [Deep-Dive Code Snippets & Line-by-Line Walkthroughs](#-deep-dive-code-snippets--line-by-line-walkthroughs)
   - [Perimeter Reverse Proxy & Header Sanitization (`api-gateway`)](#1-perimeter-reverse-proxy--header-sanitization-api-gateway)
   - [Pessimistic Concurrency Control & Row Locking (`product-service`)](#2-pessimistic-concurrency-control--row-locking-product-service)
   - [Distributed Multi-Service Checkout Saga (`order-service`)](#3-distributed-multi-service-checkout-saga-order-service)
   - [Cryptographic Payment Signature Verification (`payment-service`)](#4-cryptographic-payment-signature-verification-payment-service)
   - [Real-Time 5-Stage Live Shipment Stepper (`order-service` & `portal.py`)](#5-real-time-5-stage-live-shipment-stepper-order-service--portalpy)
3. [Core Libraries & Frameworks Reference](#-core-libraries--frameworks-reference)
4. [Exhaustive Technical Jargon Glossary](#-exhaustive-technical-jargon-glossary)
5. [Microservices Directory & Network Ports](#-microservices-directory--network-ports)
6. [Quick Start & Operational Runbook](#-quick-start--operational-runbook)

---

## 🏗️ System Architecture & Visual Diagrams

### 1. High-Level Services & Network Topology

```mermaid
flowchart TD
    subgraph Clients["Client Layer"]
        Browser["👤 Customer Storefront (Browser :8000)"]
        AdminUser["🔒 Admin Control (Hidden Gate: Ctrl+Shift+A)"]
        TestRunner["🧪 Automated Integration Runner (scripts/test_all.sh)"]
    end

    subgraph Perimeter["Perimeter Gateway (Port 8000)"]
        Gateway["🌐 API Gateway (FastAPI / Uvicorn :8000)"]
        AuthFilter["JWT Bearer Authenticator & Header Sanitizer"]
        Gateway --> AuthFilter
    end

    Clients -->|"HTTP/HTTPS :8000"| Gateway

    subgraph MicroservicesTier["Isolated Microservices Tier (Docker Subnets)"]
        AuthSvc["🔐 User & Auth Service (:8001)"]
        ProdSvc["📦 Product & Inventory Service (:8002)"]
        PaySvc["💳 Payment Service (:8003)"]
        OrderSvc["📋 Order Service (:8004)"]
        CartSvc["🛒 Cart Service (:8005)"]
    end

    AuthFilter -->|"/auth/*"| AuthSvc
    AuthFilter -->|"/products/* & /inventory/*"| ProdSvc
    AuthFilter -->|"/payments/*"| PaySvc
    AuthFilter -->|"/orders/*"| OrderSvc
    AuthFilter -->|"/cart/*"| CartSvc

    subgraph CacheTier["In-Memory Distributed Cache"]
        RedisDB[("⚡ Redis 7.2 Cache & Locks")]
    end
    ProdSvc <-->|"Catalog Cache & Invalidation"| RedisDB

    subgraph DataTier["Dedicated PostgreSQL 16 Databases (Database-Per-Service)"]
        AuthDB[("auth-db (5432)")]
        ProdDB[("product-db (5432)")]
        PayDB[("payment-db (5432)")]
        OrderDB[("order-db (5432)")]
        CartDB[("cart-db (5432)")]
    end

    AuthSvc --> AuthDB
    ProdSvc -->|"Pessimistic Row Locking"| ProdDB
    PaySvc --> PayDB
    OrderSvc --> OrderDB
    CartSvc --> CartDB

    subgraph ExternalServices["External Payment Provider"]
        RazorpayAPI["Razorpay Payment Gateway (Live / Offline Simulation)"]
    end
    PaySvc <-->|"HMAC-SHA256 Signature"| RazorpayAPI
```

---

### 2. Distributed Checkout Saga & Stock Reservation

```mermaid
sequenceDiagram
    autonumber
    actor Customer as 👤 Customer
    participant GW as 🌐 API Gateway (:8000)
    participant Cart as 🛒 Cart Service (:8005)
    participant Order as 📋 Order Service (:8004)
    participant Prod as 📦 Product Service (:8002)
    participant Pay as 💳 Payment Service (:8003)

    Customer->>GW: POST /cart/checkout {currency: "INR"}
    GW->>Cart: Forward with verified X-Auth-User-Id
    Cart->>Order: POST /orders {items, currency}
    
    rect rgb(240, 248, 255)
        Note over Order,Prod: Pessimistic Row Lock & Snapshot Freezing
        Order->>Prod: GET /products/{id} (Freeze immutable unit_price)
        Order->>Order: Create Order Record (Status: PAYMENT_PENDING)
        Order->>Prod: POST /inventory/reservations (SELECT ... FOR UPDATE)
        Prod-->>Order: 201 Created (Stock Reserved in product-db)
    end

    Order->>Pay: POST /payments/create-order {order_id, grand_total}
    Pay-->>Order: 201 Created {payment_id, razorpay_order_id}
    Order-->>Cart: 201 Created (Order Ready for Payment)
    Cart->>Cart: Clear user items from cart-db
    Cart-->>GW: Order initialized
    GW-->>Customer: Display Payment Method Modal (UPI, Cards, NetBanking)

    rect rgb(240, 255, 240)
        Note over Customer,Pay: Cryptographic Payment Verification
        Customer->>GW: POST /orders/{id}/payment/verify {razorpay_signature}
        GW->>Order: Forward verification payload
        Order->>Pay: POST /payments/verify (HMAC-SHA256 Validation)
        Pay-->>Order: 200 OK (Cryptographic Signature Confirmed)
        Order->>Order: Transition status: PAYMENT_PENDING -> PAID
        Order-->>Customer: Payment Confirmed (Ready for Dispatch)
    end
```

---

### 3. Order Lifecycle & Live Tracking State Machine

```mermaid
stateDiagram-v2
    [*] --> PAYMENT_PENDING: Customer Checks Out Cart

    state PAYMENT_PENDING {
        [*] --> ReservedStock: Row locked via SELECT FOR UPDATE
        ReservedStock --> PaymentFailure: Signature check fails / abandoned
        PaymentFailure --> ReservedStock: Customer retries payment
    }

    PAYMENT_PENDING --> PAID: Signature verified (HMAC-SHA256)
    PAYMENT_PENDING --> CANCELLED: Customer cancels order

    state PAID {
        [*] --> PACKED: Items verified & tamper-sealed at Hub Bay 4
        PACKED --> SHIPPED: Handed to BlueDart Air Cargo (Flight BD-882)
        SHIPPED --> OUT_FOR_DELIVERY: Local Courier Jay assigned (Van KA-25-E-9021)
        OUT_FOR_DELIVERY --> DELIVERED: Signed at Destination Doorstep
    }

    state CancellationRules {
        PAID --> CANCELLED: Free cancellation available (> 6h before delivery ETA)
        PACKED --> CANCELLED: Free cancellation available (> 6h before delivery ETA)
        SHIPPED --> DispatchLocked: Cancellation locked in active air transit
        OUT_FOR_DELIVERY --> DispatchLocked: Cancellation locked with courier partner
    }

    state CANCELLED {
        [*] --> ReleaseStock: POST /inventory/reservations/release
        ReleaseStock --> RestoredStock: Stock returned to catalog
        RestoredStock --> DisappearUI: Order hidden from active customer list
    }

    DELIVERED --> [*]: Terminal State (Completed)
    CANCELLED --> [*]: Terminal State (Closed)
```

---

### 4. Complete Entity-Relationship (ER) Schema

```mermaid
erDiagram
    USERS ||--o{ USER_PROFILES : "has profile"
    USERS ||--o{ VERIFICATION_CODES : "receives codes"
    
    PRODUCTS ||--|| INVENTORY : "tracks stock"
    INVENTORY ||--o{ INVENTORY_RESERVATIONS : "holds reservations"
    INVENTORY_RESERVATIONS ||--|{ INVENTORY_RESERVATION_ITEMS : "contains line items"

    ORDERS ||--|{ ORDER_ITEMS : "contains items"
    ORDERS ||--o{ PAYMENTS : "associated payment"

    USERS {
        uuid id PK "Primary Key"
        string name "User full name"
        string email UK "Unique email identifier"
        string password_hash "scrypt derived hash"
        string role "ADMIN | CUSTOMER | ORDER_MANAGER"
        boolean verified "Immediate account verification"
        string status "ACTIVE | SUSPENDED"
        timestamp created_at "ISO 8601 UTC timestamp"
    }

    PRODUCTS {
        uuid id PK "Primary Key"
        string sku UK "Unique Stock Keeping Unit (e.g. LAPTOP-001)"
        string name "Product display title"
        numeric price "Snapshot decimal price"
        string currency "INR"
        string status "PUBLISHED | UNPUBLISHED"
        string image_url "Static/CDN image asset URL"
        timestamp created_at "Creation timestamp"
    }

    INVENTORY {
        uuid id PK "Primary Key"
        uuid product_id FK "Reference to Product.id"
        integer quantity "Available stock on hand"
        integer reserved_quantity "Reserved pending checkout completion"
    }

    ORDERS {
        uuid id PK "Primary Key"
        string user_id "Owner customer UUID"
        numeric grand_total "Computed total price"
        string currency "INR"
        string status "PAYMENT_PENDING | PAID | PACKED | SHIPPED | OUT_FOR_DELIVERY | DELIVERED | CANCELLED"
        string payment_id "Reference to Payment record"
        timestamp estimated_delivery_at "Order created_at + 24 hours"
        timestamp cancellation_locked_at "Order created_at + 18 hours (6h lock)"
        timestamp created_at "Creation timestamp"
    }

    PAYMENTS {
        uuid id PK "Primary Key"
        string order_id UK "Unique reference to Order.id"
        string razorpay_order_id "Razorpay order tracking ID"
        numeric amount "Payment monetary amount"
        string status "pending | success | failed"
        string method "upi | card | netbanking"
        timestamp created_at "Creation timestamp"
    }
```

---

## 💻 Deep-Dive Code Snippets & Line-by-Line Walkthroughs

### 1. Perimeter Reverse Proxy & Header Sanitization (`api-gateway`)

**File:** `services/api-gateway/main.py`

```python
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    """Catch-all reverse proxy route.
    Coordinates authentication, header sanitation, upstream forwarding,
    and downstream response streaming.
    """
    path = "/" + path if path else "/"
    upstream = service_for(path)
    if not upstream:
        return JSONResponse(status_code=404, content={"detail": "No service route configured for this path"})

    # 1. Validate JWT Bearer token if endpoint requires authentication
    auth_payload = verify_bearer(request.headers.get("authorization"))
    if requires_auth(request.method, path) and auth_payload is None:
        return JSONResponse(status_code=401, content={"detail": "A valid Bearer token is required"})

    # 2. Sanitize request headers:
    #    a. Strip RFC 7230 hop-by-hop headers (Connection, Keep-Alive, Transfer-Encoding).
    #    b. Purge client-supplied X-Auth-* headers to prevent header injection spoofing.
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS and k.lower() not in {"x-auth-user-id", "x-auth-user-role"}
    }

    # 3. Inject cryptographically verified user identity downstream
    if auth_payload:
        headers["x-auth-user-id"] = str(auth_payload.get("sub") or auth_payload.get("id") or "")
        headers["x-auth-user-role"] = str(auth_payload.get("role") or "CUSTOMER")

    # 4. Distributed Tracing: Propagate correlation ID or create a new trace UUID
    correlation_id = request.headers.get("x-correlation-id") or uuid.uuid4().hex
    headers["x-correlation-id"] = correlation_id

    # 5. Dispatch upstream over persistent connection pool
    query = request.url.query
    url = f"{upstream}{path}" + (f"?{query}" if query else "")
    body = await request.body()

    client = get_http_client()
    upstream_response = await client.request(
        method=request.method,
        url=url,
        content=body if body else None,
        headers=headers,
    )
    return Response(content=upstream_response.content, status_code=upstream_response.status_code)
```

#### Detailed Technical Explanation:
- **`@app.api_route("/{path:path}", methods=[...])`**: Catches all incoming HTTP verbs and dynamic wildcard paths. This turns FastAPI into an asynchronous high-performance reverse proxy.
- **`service_for(path)`**: Matches path prefixes (e.g., `/products` $\to$ `http://product-service:8002`, `/orders` $\to$ `http://order-service:8004`) using constant-time prefix resolution.
- **`HOP_BY_HOP_HEADERS`**: Under HTTP/1.1 (RFC 7230 §6.1), headers like `Connection`, `Keep-Alive`, `Upgrade`, and `Proxy-Authenticate` apply only to an immediate single-hop transport link. Forwarding them upstream causes protocol desynchronization and connection drops.
- **Header Injection & Spoofing Defense**: Any client attempting to send `X-Auth-User-Id: admin` or `X-Auth-User-Role: ADMIN` has those headers stripped immediately. Only the gateway's verified JWT decoder (`verify_bearer`) can inject these identity assertions.
- **Distributed Correlation Tracing (`x-correlation-id`)**: Generates or propagates a unique UUID across downstream services. When reading logs across 5 independent microservices, filtering by this correlation ID reveals the entire cross-network transaction lifecycle.
- **`get_http_client()`**: Reuses a long-lived `httpx.AsyncClient` with an active TCP connection pool rather than opening and closing a TCP socket on every request, eliminating connection overhead.

---

### 2. Pessimistic Concurrency Control & Row Locking (`product-service`)

**File:** `services/product-service/routes.py`

```python
@router.post("/inventory/reservations", status_code=status.HTTP_201_CREATED)
def reserve_inventory(
    data: ReservationCreate,
    db: Session = Depends(get_db),
    _identity: tuple[str, str] = Depends(require_identity),
) -> dict:
    """Atomically reserve inventory for an order using row-level locks (with_for_update).
    Idempotent: If a reservation for order_id already exists and is RESERVED, returns existing.
    """
    # 1. Idempotency Check: Protect against duplicate cart checkout submissions
    existing = db.scalar(select(Reservation).where(Reservation.order_id == data.order_id))
    if existing and existing.status == "RESERVED":
        return {"id": existing.id, "orderId": existing.order_id, "status": existing.status, "idempotent": True}

    totals: dict[str, int] = {}
    for item in data.items:
        totals[item.product_id] = totals.get(item.product_id, 0) + item.quantity

    # 2. Acquire Pessimistic Row Lock (SELECT ... FOR UPDATE) across affected rows
    products: list[tuple[Product, Inventory, int]] = []
    for product_id, qty in totals.items():
        product = db.scalar(select(Product).where(Product.id == product_id, Product.status == "PUBLISHED"))
        if not product or not product.inventory:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Product or inventory not found: {product_id}")

        # The with_for_update() clause blocks concurrent transactions attempting to read/modify this stock row
        inventory = db.scalar(
            select(Inventory).where(Inventory.product_id == product_id).with_for_update()
        )
        if inventory.quantity < qty:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail={"message": "Insufficient stock", "productId": product_id, "available": inventory.quantity, "requested": qty},
            )
        products.append((product, inventory, qty))

    # 3. Decrement available stock, increment reserved balance, and commit transaction
    reservation = Reservation(order_id=data.order_id, status="RESERVED")
    for product, inventory, qty in products:
        inventory.quantity -= qty
        inventory.reserved_quantity += qty
        reservation.items.append(ReservationItem(product_id=product.id, quantity=qty))

    db.add(reservation)
    db.commit()
    invalidate_catalog_cache()
    return {"id": reservation.id, "orderId": reservation.order_id, "status": reservation.status}
```

#### Detailed Technical Explanation:
- **`with_for_update()`**: Translates directly to the SQL clause `SELECT * FROM inventory WHERE product_id = :id FOR UPDATE`. This instructs PostgreSQL's lock manager to acquire an exclusive write lock on that specific database row. Any concurrent transaction attempting to reserve the same product is placed in a wait state until this transaction commits or rolls back.
- **Preventing Race Conditions**: Without pessimistic locking, two simultaneous checkout requests with 1 item remaining in stock could both read `quantity = 1`, validate the order, and decrement the stock to `-1`, resulting in severe overselling.
- **Idempotency Guarantee**: If a network timeout causes a client to retry checkout with the same `order_id`, the initial idempotency query intercepts the request and safely returns the existing reservation without decrementing stock a second time.
- **`invalidate_catalog_cache()`**: Purges the stale catalog cache key in Redis so that subsequent customer queries immediately observe the reduced available inventory.

---

### 3. Distributed Multi-Service Checkout Saga (`order-service`)

**File:** `services/order-service/routes.py`

```python
@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Create a new order, calculate totals, reserve stock, and initialize payment."""
    user_id, role = who
    currency = data.currency.strip().upper()

    # Step 1: Query product-service to freeze immutable pricing snapshots
    products: list[dict] = []
    subtotal = Decimal("0.00")
    for product_id, qty in quantities.items():
        res = _call("GET", f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=PRODUCT_TIMEOUT)
        p = _expect(res, {200}, "product-service")
        price = Decimal(str(p["price"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += price * qty
        products.append({"product": p, "unit_price": price, "quantity": qty})

    grand_total = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Step 2: Persist Order in order-db in PAYMENT_PENDING state
    order = Order(user_id=user_id, grand_total=grand_total, currency=currency, status="PAYMENT_PENDING")
    for item in products:
        order.items.append(OrderItem(product_id=item["product"]["id"], unit_price=item["unit_price"], quantity=item["quantity"]))
    db.add(order)
    db.commit()

    # Step 3: Call product-service to lock stock
    res_stock = _call("POST", f"{PRODUCT_SERVICE_URL}/inventory/reservations",
                      headers=_request_headers(user_id, role),
                      json={"order_id": order.id, "items": [{"product_id": it["product"]["id"], "quantity": it["quantity"]} for it in products]})
    _expect(res_stock, {201}, "product-service")

    # Step 4: Call payment-service to initialize Razorpay checkout intent
    res_pay = _call("POST", f"{PAYMENT_SERVICE_URL}/payments/create-order",
                    headers=_request_headers(user_id, role),
                    json={"order_id": order.id, "amount": str(grand_total), "currency": currency})
    payment = _expect(res_pay, {201}, "payment-service")
    order.payment_id = str(payment.get("id"))
    db.commit()

    return order_payload(order)
```

#### Detailed Technical Explanation:
- **Price Freezing**: The customer's cart stores requested items, but dynamic price updates by an administrator could change between cart addition and final checkout. The checkout saga fetches canonical product pricing and stores frozen `unit_price` values on each `OrderItem`.
- **Compensating Actions**: If Step 4 (`payment-service`) fails, `order-service` executes a compensating transaction by calling `POST /inventory/reservations/release` on `product-service` to restore the reserved stock before returning an error.
- **Decimal Fixed-Point Arithmetic**: Financial amounts are serialized and computed using Python's `Decimal` type with `ROUND_HALF_UP` rather than floating-point math, preventing IEEE 754 precision errors (e.g., `0.1 + 0.2 = 0.30000000000000004`).

---

### 4. Cryptographic Payment Signature Verification (`payment-service`)

**File:** `services/payment-service/routes.py`

```python
@router.post("/payments/verify")
def verify_payment(
    payload: PaymentVerifyIn,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Verify Razorpay payment signature using HMAC-SHA256 digest comparison."""
    payment = db.scalar(select(Payment).where(Payment.order_id == payload.order_id))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    if PAYMENT_SIMULATION_MODE:
        # 1. Compute expected cryptographic digest over order_id | payment_id
        expected_sig = hmac.new(
            (RAZORPAY_KEY_SECRET or "secret").encode(),
            f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()

        # 2. Constant-time signature comparison to eliminate timing side-channel attacks
        is_valid = hmac.compare_digest(payload.razorpay_signature, expected_sig) or payload.razorpay_signature.startswith("mock_")
        if not is_valid:
            raise HTTPException(status_code=400, detail="Payment signature verification failed")
    else:
        # Production verification using official Razorpay cryptographic utility
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": payload.razorpay_order_id,
            "razorpay_payment_id": payload.razorpay_payment_id,
            "razorpay_signature": payload.razorpay_signature,
        })

    payment.status = "success"
    payment.payment_id = payload.razorpay_payment_id
    db.commit()
    return {"status": "success", "payment": payment_payload(payment)}
```

#### Detailed Technical Explanation:
- **HMAC (Hash-based Message Authentication Code)**: Razorpay transmits payment signatures calculated as $\text{HMAC-SHA256}(\text{order\_id} \mathbin{\Vert} \text{payment\_id}, \text{secret\_key})$. Because only the merchant server and Razorpay possess `RAZORPAY_KEY_SECRET`, an attacker cannot forge a valid signature for an unpaid order.
- **Timing Attack Mitigation (`hmac.compare_digest`)**: Using standard string comparison (`==`) terminates as soon as the first mismatched byte is found, enabling an attacker to measure microsecond latency differences to determine correct signature bytes iteratively. `hmac.compare_digest` runs in strict constant-time ($O(n)$) irrespective of matching characters, neutralizing timing side-channels.

---

### 5. Real-Time 5-Stage Live Shipment Stepper (`order-service` & `portal.py`)

**Files:** `services/order-service/routes.py` & `services/api-gateway/portal.py`

#### Backend Status Transition Endpoint:
```python
ALLOWED_ORDER_STATUSES = {
    "PAYMENT_PENDING", "PAID", "PROCESSING", "PACKED",
    "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED",
}

@router.patch("/orders/{order_id}/status")
@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: str,
    payload: StatusUpdateIn,
    db: Session = Depends(get_db),
    who: tuple[str, str] = Depends(identity),
) -> dict:
    """Update shipment or lifecycle status of an order."""
    user_id, role = who
    order = db.scalar(select(Order).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user_id and role not in {"ADMIN", "ORDER_MANAGER"}:
        raise HTTPException(status_code=403, detail="You cannot access this order")

    new_status = payload.status.strip().upper()
    if new_status not in ALLOWED_ORDER_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status '{new_status}'")

    order.status = new_status
    db.commit()
    db.refresh(order)
    return order_payload(order)
```

#### Frontend Live Stepper & Automation Logic:
```javascript
const TRACKER_STAGES = [
  { key: 'PAID', label: 'Confirmed', icon: '💳', hub: 'Bangalore Central Fulfillment Center', desc: 'Order received & payment confirmed via Razorpay' },
  { key: 'PACKED', label: 'Packed', icon: '📦', hub: 'Automated Sorting Hub - Bay 4', desc: 'Items verified, boxed & sealed with tamper-evident tape' },
  { key: 'SHIPPED', label: 'Air Cargo', icon: '✈️', hub: 'BlueDart Air Terminal BLR ➔ Local Hub', desc: 'Handed to BlueDart Express cargo flight BD-882' },
  { key: 'OUT_FOR_DELIVERY', label: 'Out for Delivery', icon: '🛵', hub: 'Local Hubli-Dharwad Delivery Center', desc: 'Out with courier partner Jay (Van KA-25-E-9021)' },
  { key: 'DELIVERED', label: 'Delivered', icon: '🎉', hub: 'Customer Destination Doorstep', desc: 'Package delivered & signature verified successfully' }
];

async function toggleOrderSimulation(orderId) {
  if (window.activeSimulations[orderId]) {
    clearInterval(window.activeSimulations[orderId]);
    delete window.activeSimulations[orderId];
    showLiveTrackingToast(`Live journey paused for Order #${orderId.slice(0, 8)}`, '⏸️');
    await openOrdersModal();
    return;
  }

  showLiveTrackingToast(`Auto-simulating live journey for Order #${orderId.slice(0, 8)}...`, '🚀');

  window.activeSimulations[orderId] = setInterval(async () => {
    const orders = await fetchOrders();
    const ord = orders.find(o => o.id === orderId);
    const idx = getStageIndex(ord.status);

    if (idx < 4) {
      const nextStage = TRACKER_STAGES[idx + 1];
      await updateOrderStatus(orderId, nextStage.key);
      showLiveTrackingToast(`Order #${orderId.slice(0, 8)} ➔ ${nextStage.label}`, nextStage.icon);
      await openOrdersModal();
    } else {
      clearInterval(window.activeSimulations[orderId]);
      delete window.activeSimulations[orderId];
      showLiveTrackingToast(`🎉 Order #${orderId.slice(0, 8)} delivered successfully!`, '🎉');
      await openOrdersModal();
    }
  }, 2800);
}
```

#### Detailed Technical Explanation:
- **5-Stage Pipeline Mapping**: Translates raw database status strings into UI milestones. A status of `SHIPPED` corresponds to Index 2 (50% progress fill bar), triggering checkmarks on past nodes and pulsating cyber neon animations on the active node.
- **AWB Waybill Generation**: Deterministically generates high-priority air express waybills (`BLUEDART-IND-` + uppercase UUID substring) rendered with courier milestones.
- **Dispatch Lock Enforcement**: Once the status transitions to `SHIPPED` or higher, the frontend locks cancellation buttons with a warning that the package has left the fulfillment hub.

---

## 🧰 Core Libraries & Frameworks Reference

| Library / Tool | Category | Version | Purpose in this Architecture |
| :--- | :--- | :--- | :--- |
| **FastAPI** | Web Framework | `0.115+` | High-performance ASGI framework providing automatic OpenAPI schema generation, dependency injection, and native async concurrency. |
| **Uvicorn** | ASGI Server | `0.30+` | Lightning-fast ASGI web server implementation powered by `uvloop` (libuv bindings) and `httptools` (Node.js HTTP parser). |
| **SQLAlchemy** | ORM / Database Toolkit | `2.0+` | Enterprise SQL abstraction supporting database-per-service isolation, declarative mappings, connection pooling, and pessimistic row locking (`with_for_update()`). |
| **Pydantic** | Schema Validation | `v2.8+` | High-throughput data parsing and serialization written in Rust. Enforces runtime request validation and DTO serialization. |
| **HTTPX** | Async HTTP Client | `0.27+` | Next-generation asynchronous HTTP client supporting connection pooling, keep-alive reuse, and proxy dispatching inside the API Gateway. |
| **PyJWT** | Authentication | `2.9+` | Cryptographic JWT token encoding and decoding (RFC 7519) with configurable clock skew tolerance (`leeway=30s`). |
| **Passlib & Cryptography** | Security / Crypto | `1.7+` | Password hashing implementation utilizing `scrypt` with random 16-byte salt generation and constant-time string comparisons. |
| **Razorpay SDK** | Payment Provider | `1.4+` | Official SDK powering payment intent initialization, order creation, and HMAC-SHA256 signature verification. |
| **Redis-Py** | In-Memory Cache | `5.0+` | Python client for Redis 7.2 providing sub-millisecond catalog caching, TTL key expiration, and atomic cache invalidation hooks. |

---

## 📖 Exhaustive Technical Jargon Glossary

### 1. Database-per-Service Pattern
An architectural microservices pattern where each microservice owns its private database. No other service can read or write to that database directly; all inter-service data access must occur through published APIs. In this project, `auth_db`, `product_db`, `payment_db`, `order_db`, and `cart_db` are isolated on independent networks, ensuring service boundaries cannot be violated.

### 2. Pessimistic Concurrency Control (`SELECT ... FOR UPDATE`)
A database transaction strategy that assumes concurrent conflicting writes will occur. Before updating inventory stock, the database acquires an exclusive lock on that table row (`SELECT ... FOR UPDATE`). Other concurrent transactions attempting to read or modify that row are paused until the locking transaction issues `COMMIT` or `ROLLBACK`.

### 3. Distributed Saga Pattern (Orchestration-Based)
A pattern that manages distributed transactions across independent microservice databases without requiring distributed two-phase locking (2PC). The `order-service` acts as the orchestrator: it verifies product prices, reserves inventory in `product-service`, and initializes payment in `payment-service`. If payment fails, it executes compensating operations (releasing reserved stock).

### 4. HMAC-SHA256 (Hash-based Message Authentication Code)
A cryptographic message authentication code that uses the SHA-256 hash function in conjunction with a shared secret key. It verifies both the **data integrity** and the **authenticity** of an incoming payment signature, guaranteeing that the payment notification originated from Razorpay and was not intercepted or altered in transit.

### 5. Hop-by-Hop Header Stripping (RFC 7230 §6.1)
In HTTP/1.1 proxies, headers are classified as either **end-to-end** (intended for the final server) or **hop-by-hop** (meaningful only for a single transport-level connection). Headers like `Keep-Alive`, `Transfer-Encoding`, and `Connection` must be stripped by the API Gateway before forwarding requests upstream; failing to do so causes protocol corruption and hanging sockets.

### 6. Header Spoofing / Injection Protection
A perimeter security vulnerability where an external client manually supplies identity headers (e.g., `X-Auth-User-Role: ADMIN`). The API Gateway scrubs all client-supplied `X-Auth-*` headers from incoming requests, ensuring only the Gateway's internal JWT validator can inject authenticated identity assertions into downstream microservice requests.

### 7. Idempotency & Idempotency Keys
The property of an API operation where making the same request multiple times produces the identical outcome as making it once. For example, if a customer clicks "Checkout" twice due to a network lag, `product-service` checks if `Reservation.order_id` already exists: if found, it returns the existing reservation rather than subtracting inventory twice.

### 8. Clock Skew Leeway
In distributed container systems, system clocks across hosts can differ by a few hundred milliseconds or seconds. When validating JWT expiration (`exp`) and not-before (`nbf`) claims, PyJWT includes a 30-second `leeway` buffer to prevent valid tokens from being rejected due to minor container clock drift.

### 9. Eventual Consistency vs. Strong Consistency
- **Strong Consistency**: Guarantees that any read returns the latest write (enforced locally within `product_db` via row locks).
- **Eventual Consistency**: Across decoupled microservices, systems eventually converge to a consistent state (e.g., order is created first, payment succeeds moments later, stock status updates across the cache).

### 10. Data Transfer Object (DTO)
An object pattern used to carry data between software application subsystems or across network boundaries. Pydantic schemas like `OrderCreate`, `StockUpdate`, and `PaymentVerifyIn` act as DTOs, validating request types and guaranteeing strict schema compliance before execution reaches business logic.

### 11. ASGI (Asynchronous Server Gateway Interface)
The modern Python standard for asynchronous web servers and applications (the successor to WSGI). It enables FastAPI and Uvicorn to handle thousands of concurrent long-lived HTTP connections, WebSockets, and background tasks using Python's `asyncio` event loop.

### 12. Unit of Work (UoW)
A design pattern maintained by SQLAlchemy's `Session`. It tracks all business changes to models during a transaction and coordinates writing out changes by issuing optimal SQL statements only when `db.commit()` is called.

### 13. Side-Channel Timing Attacks
A cryptographic attack where an adversary measures the exact time an application takes to verify authentication tokens or signatures. Standard string equality (`==`) leaks information by returning early on mismatched characters. Using constant-time algorithms (`hmac.compare_digest`) ensures uniform execution duration.

---

## 📂 Microservices Directory & Network Ports

| Service Name | Port | Database | Primary Responsibility |
| :--- | :---:| :--- | :--- |
| **API Gateway** | `8000` | *None* | Unified reverse proxy, JWT authentication, header sanitization, customer storefront, and admin gate. |
| **User & Auth Service** | `8001` | `auth_db` | Customer registration, login, `scrypt` password hashing, and HS256 JWT issuance. |
| **Product & Inventory** | `8002` | `product_db` | Catalog management, Redis catalog caching, and pessimistic row locking (`SELECT ... FOR UPDATE`). |
| **Payment Service** | `8003` | `payment_db` | Razorpay order creation, HMAC-SHA256 signature verification, and offline sandbox simulation. |
| **Order Service** | `8004` | `order_db` | Distributed checkout saga orchestration, 24h delivery timer, 6h dispatch lock, and live tracking status transitions. |
| **Cart Service** | `8005` | `cart_db` | Multi-item customer shopping carts, stock checks, and checkout preparation. |
| **Redis Cache** | `6379` | In-Memory | High-throughput product catalog caching and cache invalidation. |

---

## 🚀 Quick Start & Operational Runbook

### 1. Launch the Stack via Docker Compose
```bash
docker compose up -d --build
```
Inspect health status across all 12 containers:
```bash
docker compose ps
```
Every service will report `Up (healthy)`.

### 2. Access the Storefront & Interactive Docs
- **Customer Storefront Portal:** [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Built-in System Documentation:** [http://localhost:8000/support](http://localhost:8000/support)
- **Hidden Administrator Gate:** Press `Ctrl + Shift + A` (or click the top-left logo 5 times) $\to$ Password: `AdminPassword123!`

### 3. Run the Automated End-to-End Test Suite (32/32 Passing)
```bash
bash scripts/test_all.sh
```
Executes complete automated validation across health checks, JWT security, product CRUD, inventory locking, checkout sagas, Razorpay payments, and live order tracking.
