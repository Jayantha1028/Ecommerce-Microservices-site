# E-Commerce Microservices Platform

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jayantha-nayak/ECommerce-Microservices-Docker-Site)

An enterprise-grade, event-driven e-commerce platform built with **FastAPI**, **PostgreSQL 16**, **Redis 7.2**, **Docker**, **Kubernetes**, and **Razorpay**. All services are decoupled behind a unified API Gateway with JWT-based authentication, network-isolated databases, pessimistic row locking, and an encapsulated customer storefront.

---

## 🏗️ System Architecture Diagrams

### 1. High-Level Network & Services Topology

```mermaid
flowchart TD
    subgraph Clients["Client Layer"]
        Browser["👤 Customer Storefront (Browser :8000)"]
        AdminUser["🔒 Admin Control (Hidden Gate: Ctrl+Shift+A)"]
        TestRunner["🧪 Automated Test Runner (scripts/test_all.sh)"]
    end

    subgraph Perimeter["Perimeter Gateway (Port 8000)"]
        Gateway["🌐 API Gateway (FastAPI / Uvicorn :8000)"]
        AuthFilter["JWT Bearer Authenticator & Sanitizer"]
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

    subgraph CacheTier["In-Memory Cache"]
        RedisDB[("⚡ Redis 7.2 Cache")]
    end
    ProdSvc <-->|"Catalog Cache"| RedisDB

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
        RazorpayAPI["Razorpay Payment Gateway (Live / Sandbox)"]
    end
    PaySvc <-->|"HMAC-SHA256"| RazorpayAPI
```

#### ASCII Network View (Fallback / Raw Text)
```
                                 [ Client Traffic / Browser ]
                                              │
                                              ▼ (Port 8000)
                               ┌─────────────────────────────┐
                               │     Unified API Gateway     │
                               │  (FastAPI / Security Proxy) │
                               └──────────────┬──────────────┘
                                              │ Internal Bridge Subnets
          ┌──────────────────┬────────────────┼────────────────┬──────────────────┐
          ▼                  ▼                ▼                ▼                  ▼
 ┌─────────────────┐ ┌───────────────┐ ┌──────────┐ ┌──────────────┐ ┌─────────────────┐
 │User/Auth Service│ │Product Service│ │ Cart Svc │ │Order Service │ │ Payment Service │
 │   (Port 8001)   │ │  (Port 8002)  │ │ Port 8005│ │ (Port 8004)  │ │   (Port 8003)   │
 └────────┬────────┘ └───────┬───────┘ └────┬─────┘ └──────┬───────┘ └────────┬────────┘
          │ auth-net         │ prod-net     │cart-net      │ order-net        │ payment-net
          ▼                  ▼              ▼              ▼                  ▼
  ┌───────────────┐  ┌───────────────┐ ┌──────────┐ ┌──────────────┐  ┌───────────────┐
  │    auth-db    │  │  product-db   │ │ cart-db  │ │   order-db   │  │  payment-db   │
  │ (Postgres 16) │  │ (Postgres 16) │ │(Postgres)│ │(Postgres 16) │  │ (Postgres 16) │
  └───────────────┘  └───────────────┘ └──────────┘ └──────────────┘  └───────────────┘
```

---

### 2. Distributed Checkout Saga & Stock Locking

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
    GW->>Cart: Forward with X-Auth-User-Id
    Cart->>Order: POST /orders {items, currency}
    
    rect rgb(240, 248, 255)
        Note over Order,Prod: Pessimistic Row Lock & Snapshot Freezing
        Order->>Prod: GET /products/{id} (Freeze snapshot price)
        Order->>Order: Create Order (Status: PAYMENT_PENDING)
        Order->>Prod: POST /inventory/reservations (SELECT ... FOR UPDATE)
        Prod-->>Order: 201 Created (Stock Reserved)
    end

    Order->>Pay: POST /payments/create-order {order_id, amount}
    Pay-->>Order: 201 Created {payment_id, razorpay_order_id}
    Order-->>Cart: 201 Created (Order Ready)
    Cart->>Cart: Clear user items from cart-db
    Cart-->>GW: Order initialized
    GW-->>Customer: Display Payment Method Modal (UPI, Cards, NetBanking)

    rect rgb(240, 255, 240)
        Note over Customer,Pay: Cryptographic Payment Verification
        Customer->>GW: POST /orders/{id}/payment/verify {signature}
        GW->>Order: Forward verification
        Order->>Pay: POST /payments/verify (HMAC-SHA256)
        Pay-->>Order: 200 OK (Payment Verified)
        Order->>Order: Transition status to 'PAID'
        Order-->>Customer: Payment Confirmed (Ready for Dispatch)
    end
```

---

### 3. Order Lifecycle & 6-Hour Cancellation Rule

```mermaid
stateDiagram-v2
    [*] --> PAYMENT_PENDING: Customer Checks Out Cart

    state PAYMENT_PENDING {
        [*] --> ReservedStock: Stock locked via row-level lock
        ReservedStock --> PaymentFailure: Payment cancelled or timed out
        PaymentFailure --> ReservedStock: Customer retries payment
    }

    PAYMENT_PENDING --> PAID: Signature verified (HMAC-SHA256)
    PAYMENT_PENDING --> CANCELLED: Customer cancels order

    state PAID {
        [*] --> InTransit: 24h Delivery Countdown Window
        InTransit --> CancellationLocked: < 6 Hours Remaining (Option Locked)
        CancellationLocked --> COMPLETED: Delivery Completed
    }

    InTransit --> CANCELLED: Cancel Order (> 6 Hours Remaining)

    state CANCELLED {
        [*] --> ReleaseStock: Call /inventory/reservations/release
        ReleaseStock --> InventoryRestored: Stock returned to catalog
        InventoryRestored --> DisappearFromUI: Cancelled order disappears from orders list
    }

    COMPLETED --> [*]: Terminal State
    CANCELLED --> [*]: Terminal State
```

---

### 4. Database Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    USERS ||--o{ USER_PROFILES : "has profile"
    USERS ||--o{ VERIFICATION_CODES : "receives codes"
    PRODUCTS ||--|| INVENTORY : "tracks stock"
    INVENTORY ||--o{ INVENTORY_RESERVATIONS : "holds reservations"
    INVENTORY_RESERVATIONS ||--|{ INVENTORY_RESERVATION_ITEMS : "contains items"
    ORDERS ||--|{ ORDER_ITEMS : "contains items"
    ORDERS ||--o{ PAYMENTS : "associated payment"

    USERS {
        uuid id PK
        string name
        string email UK
        string password_hash
        string role
        boolean verified
        string status
        timestamp created_at
    }

    PRODUCTS {
        uuid id PK
        string sku UK
        string name
        numeric price
        string currency
        string status
        string image_url
        timestamp created_at
    }

    INVENTORY {
        uuid id PK
        uuid product_id FK
        integer quantity
        integer reserved_quantity
    }

    ORDERS {
        uuid id PK
        string user_id
        numeric grand_total
        string currency
        string status
        string payment_id
        timestamp created_at
    }

    PAYMENTS {
        uuid id PK
        string order_id UK
        string razorpay_order_id
        numeric amount
        string status
        string method
        timestamp created_at
    }
```

---

## 📂 Microservices Directory & Ports

| Service | Port | Database | Primary Function |
|---|---:|---|---|
| **API Gateway** | `8000` | None | Unified entry point, JWT validation, reverse proxy, customer storefront, hidden admin gate |
| **User & Auth Service** | `8001` | `auth_db` | Registration, email verification, `scrypt` password hashing, JWT issuance |
| **Product & Inventory** | `8002` | `product_db` | Catalog CRUD, product image upload, `SELECT ... FOR UPDATE` row locking |
| **Payment Service** | `8003` | `payment_db` | Razorpay orders, HMAC-SHA256 signature verification, offline simulation mode |
| **Order Service** | `8004` | `order_db` | Multi-item checkout saga, 24h timer, 6h lock rule, order cancellation |
| **Cart Service** | `8005` | `cart_db` | Persistent customer cart, quantity validation, checkout transition |

---

## 🚀 Quick Start

### 1. Run the Entire Stack via Docker
```bash
docker compose up -d --build
```
Inspect health:
```bash
docker compose ps
```
All 12 containers (`api-gateway`, 5 services, 5 databases, `redis`) will report `(healthy)`.

### 2. Access the Storefront
Open in browser:
- **Customer Store:** [http://localhost:8000](http://localhost:8000)
- **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Hidden Admin Gate:** Press `Ctrl + Shift + A` (or click logo 5x) $\to$ Password: `AdminPassword123!`

### 3. Run Automated Integration Tests (32/32 Passing)
```bash
bash scripts/test_all.sh
```

---

## 📑 Detailed Architecture Documentation
For deep-dive technical specs, review:
- [doc/ARCHITECTURE.md](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/doc/ARCHITECTURE.md): Comprehensive 7-diagram architecture guide.
- [doc/flowchart.md](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/doc/flowchart.md): Step-by-step workflow flowcharts.
- [scripts/export_csv_backup.py](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/scripts/export_csv_backup.py): Database backup snapshot script.
