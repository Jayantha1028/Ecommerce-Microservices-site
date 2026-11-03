# E-Commerce Microservices System Architecture & Diagrams

Comprehensive architectural documentation for the E-Commerce Platform, capturing system topology, domain boundaries, data models, distributed transaction orchestration, security architecture, and deployment specifications.

---

## 📑 Table of Contents
1. [High-Level System & Network Topology](#1-high-level-system--network-topology)
2. [Microservices Domain & Inter-Service Communication](#2-microservices-domain--inter-service-communication)
3. [Complete Database Entity-Relationship (ER) Diagram](#3-complete-database-entity-relationship-er-diagram)
4. [Distributed Checkout Saga & Inventory Locking](#4-distributed-checkout-saga--inventory-locking)
5. [Order Lifecycle & 6-Hour Cancellation Lock State Machine](#5-order-lifecycle--6-hour-cancellation-lock-state-machine)
6. [Security & Authentication Architecture](#6-security--authentication-architecture)
7. [Kubernetes Cluster Deployment Architecture](#7-kubernetes-cluster-deployment-architecture)
8. [Crossplane Continuous Drift Detection & Keep-Alive Architecture](#8-crossplane-continuous-drift-detection--keep-alive-architecture)

---

## 1. High-Level System & Network Topology

The platform enforces database-per-service isolation across 5 dedicated PostgreSQL 16 databases and an ephemeral Redis instance. The **API Gateway** acts as the single secure public reverse proxy and perimeter gateway.

```mermaid
flowchart TD
    subgraph Clients["Client Layer"]
        Browser["Customer Browser (Storefront & Portal)"]
        AdminUser["Administrator (Hidden Admin Mode)"]
        CurlClient["Automated Test Suite / CI/CD Runner"]
    end

    subgraph Perimeter["Perimeter Gateway (Port 8000)"]
        Gateway["API Gateway (FastAPI / Uvicorn :8000)"]
        GatewayRouter["Reverse Proxy & Routing Engine"]
        GatewaySecurity["JWT Validator & Header Propagator"]
        Gateway --> GatewayRouter
        Gateway --> GatewaySecurity
    end

    Clients -->|"HTTP/HTTPS :8000"| Gateway

    subgraph InternalServices["Isolated Microservices Tier"]
        AuthSvc["User & Auth Service (:8001)"]
        ProdSvc["Product & Inventory Service (:8002)"]
        PaySvc["Payment Service (:8003)"]
        OrderSvc["Order Service (:8004)"]
        CartSvc["Cart Service (:8005)"]
    end

    GatewayRouter -->|"/auth/*"| AuthSvc
    GatewayRouter -->|"/products/* & /inventory/*"| ProdSvc
    GatewayRouter -->|"/payments/*"| PaySvc
    GatewayRouter -->|"/orders/*"| OrderSvc
    GatewayRouter -->|"/cart/*"| CartSvc

    subgraph CacheTier["Caching & Locks"]
        RedisDB[("Redis 7.2 (Catalog Cache & Locks)")]
    end

    ProdSvc <-->|"Product Cache & Read-Through"| RedisDB

    subgraph DataTier["PostgreSQL 16 Databases (Database-Per-Service)"]
        AuthDB[("auth-db (auth_db)")]
        ProdDB[("product-db (product_db)")]
        PayDB[("payment-db (payment_db)")]
        OrderDB[("order-db (order_db)")]
        CartDB[("cart-db (cart_db)")]
    end

    AuthSvc -->|"SQLAlchemy 2.0"| AuthDB
    ProdSvc -->|"SQLAlchemy 2.0 (Row Locks)"| ProdDB
    PaySvc -->|"SQLAlchemy 2.0"| PayDB
    OrderSvc -->|"SQLAlchemy 2.0"| OrderDB
    CartSvc -->|"SQLAlchemy 2.0"| CartDB

    subgraph ExternalGateway["External Payment Provider"]
        RazorpayAPI["Razorpay Payment Gateway (Live / Offline Simulation)"]
    end

    PaySvc <-->|"REST API / Webhooks / HMAC"| RazorpayAPI
```

---

## 2. Microservices Domain & Inter-Service Communication

Services communicate over an internal network using REST APIs with propagated security headers (`X-Auth-User-Id`, `X-Auth-User-Role`).

```mermaid
flowchart LR
    Cart["Cart Service (:8005)"]
    Order["Order Service (:8004)"]
    Prod["Product Service (:8002)"]
    Pay["Payment Service (:8003)"]
    Auth["Auth Service (:8001)"]

    Cart -->|"GET /products/{id} (Check Stock & Price)"| Prod
    Cart -->|"POST /orders (Submit Frozen Cart)"| Order
    Order -->|"GET /products/{id} (Verify Snapshots)"| Prod
    Order -->|"POST /inventory/reservations (Pessimistic Lock)"| Prod
    Order -->|"POST /inventory/reservations/release (On Cancel)"| Prod
    Order -->|"POST /payments/create-order"| Pay
    Order -->|"POST /payments/verify (Validate Signature)"| Pay
    Prod -->|"Authorize Token"| Auth
    Order -->|"Authorize Token"| Auth
    Cart -->|"Authorize Token"| Auth
    Pay -->|"Authorize Token"| Auth
```

---

## 3. Complete Database Entity-Relationship (ER) Diagram

The system comprises 11 tables distributed across 5 databases with referential integrity maintained within each service boundary.

```mermaid
erDiagram
    USERS ||--o{ USER_PROFILES : "has profile"
    USERS ||--o{ VERIFICATION_CODES : "receives codes"
    
    PRODUCTS ||--|| INVENTORY : "tracks stock"
    INVENTORY ||--o{ INVENTORY_RESERVATIONS : "holds reservations"
    INVENTORY_RESERVATIONS ||--|{ INVENTORY_RESERVATION_ITEMS : "contains"

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
        timestamp updated_at
    }

    USER_PROFILES {
        uuid id PK
        uuid user_id FK
        string name
        string email
        string phone
        string street_address
        string city
        string state
        string postal_code
        string country
    }

    VERIFICATION_CODES {
        uuid id PK
        uuid user_id FK
        string code_hash
        boolean used
        timestamp expires_at
        timestamp created_at
    }

    PRODUCTS {
        uuid id PK
        string sku UK
        string name
        string description
        numeric price
        string currency
        string status
        string image_url
        timestamp created_at
        timestamp updated_at
    }

    INVENTORY {
        uuid id PK
        uuid product_id FK
        integer quantity
        integer reserved_quantity
        timestamp updated_at
    }

    INVENTORY_RESERVATIONS {
        uuid id PK
        string order_id UK
        string status
        timestamp expires_at
        timestamp created_at
    }

    INVENTORY_RESERVATION_ITEMS {
        uuid id PK
        uuid reservation_id FK
        uuid product_id
        integer quantity
    }

    CART_ITEMS {
        uuid id PK
        string user_id
        uuid product_id
        integer quantity
        timestamp created_at
        timestamp updated_at
    }

    ORDERS {
        uuid id PK
        string user_id
        numeric subtotal
        numeric tax_total
        numeric shipping_total
        numeric grand_total
        string currency
        string status
        string payment_id
        timestamp created_at
        timestamp updated_at
    }

    ORDER_ITEMS {
        uuid id PK
        uuid order_id FK
        uuid product_id
        string product_name
        string sku
        numeric unit_price
        integer quantity
        numeric line_total
    }

    PAYMENTS {
        uuid id PK
        string order_id UK
        string razorpay_order_id
        string razorpay_payment_id
        numeric amount
        string currency
        string status
        string method
        timestamp created_at
        timestamp updated_at
    }
```

---

## 4. Distributed Checkout Saga & Inventory Locking

Sequence diagram of the distributed transaction during checkout, showing PostgreSQL `SELECT ... FOR UPDATE` row locking to prevent race conditions and overselling.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer (Browser)
    participant GW as API Gateway (:8000)
    participant Cart as Cart Service (:8005)
    participant Order as Order Service (:8004)
    participant Prod as Product Service (:8002)
    participant Pay as Payment Service (:8003)
    participant ProdDB as product-db (PostgreSQL)

    Note over Customer,GW: Step 1: Initiate Checkout
    Customer->>GW: POST /cart/checkout {currency: "INR"}
    GW->>Cart: Forward with X-Auth-User-Id

    Note over Cart,Order: Step 2: Order Orchestration
    Cart->>Order: POST /orders {items, currency}
    Order->>Prod: GET /products/{id} (Freeze snapshot unit prices)
    Order->>Order: Create Order record (status: PAYMENT_PENDING)

    Note over Order,ProdDB: Step 3: Atomic Stock Reservation
    Order->>Prod: POST /inventory/reservations {order_id, items}
    Prod->>ProdDB: BEGIN Transaction
    Prod->>ProdDB: SELECT quantity, reserved_quantity FROM inventory WHERE product_id = :id FOR UPDATE
    Note over ProdDB: Pessimistic Row Lock acquired (Prevents race conditions)
    alt Available Stock >= Requested Quantity
        Prod->>ProdDB: UPDATE inventory SET reserved_quantity = reserved_quantity + :qty
        Prod->>ProdDB: INSERT INTO inventory_reservations & items
        Prod->>ProdDB: COMMIT Transaction
        Prod-->>Order: 201 Created (Reserved)
    else Insufficient Stock
        Prod->>ProdDB: ROLLBACK Transaction
        Prod-->>Order: 409 Conflict (Out of stock)
        Order-->>Cart: 409 Conflict
        Cart-->>Customer: 409 Conflict (Stock unavailable)
    end

    Note over Order,Pay: Step 4: Payment Initialization
    Order->>Pay: POST /payments/create-order {order_id, amount, currency}
    Pay-->>Order: 201 Created {payment_id, razorpay_order_id}
    Order->>Order: Update order with payment ID
    Order-->>Cart: 201 Created (Order Ready)

    Note over Cart,Customer: Step 5: Clean Cart & Return
    Cart->>Cart: Clear user's cart in cart-db
    Cart-->>GW: 201 Created {order_id, razorpay_order_id}
    GW-->>Customer: 200 OK (Render Payment Modal)
```

---

## 5. Order Lifecycle & 6-Hour Cancellation Lock State Machine

State machine governing order statuses, completion countdowns, the 6-hour cancellation lock, and automatic inventory release.

```mermaid
stateDiagram-v2
    [*] --> PAYMENT_PENDING: Customer Checks Out

    state PAYMENT_PENDING {
        [*] --> ReservedStock: Row locked in product-db
        ReservedStock --> PaymentFailure: Signature check fails or window expires
        PaymentFailure --> ReservedStock: Customer retries payment
    }

    PAYMENT_PENDING --> PAID: Payment Verified (HMAC-SHA256 Match)
    PAYMENT_PENDING --> CANCELLED: Customer Cancels / Abandons

    state PAID {
        [*] --> InTransit: 24h Completion Window Starts
        InTransit --> CancellationLocked: < 6 Hours Remaining (Option Locked)
        CancellationLocked --> COMPLETED: 0 Hours Remaining (Package Delivered)
    }

    InTransit --> CANCELLED: Customer Cancels (> 6 Hours Remaining)

    state CANCELLED {
        [*] --> ReleaseStock: Call /inventory/reservations/release
        ReleaseStock --> InventoryRestored: Stock returned to available pool
        InventoryRestored --> ExcludedFromList: Order disappears from Customer View
    }

    COMPLETED --> [*]: Terminal State (Delivered)
    CANCELLED --> [*]: Terminal State (Closed)
```

---

## 6. Security & Authentication Architecture

Details the multi-tiered defense strategy: JWT bearer authentication, scrypt password hashing, the hidden administrative gate, and cryptographic payment verification.

```mermaid
flowchart TD
    subgraph AuthPipeline["1. Customer Authentication"]
        Reg["POST /auth/register"] --> ScryptHash["Hash password with scrypt (16-byte random salt)"]
        ScryptHash --> StoreUser["Store User (status: PENDING, verified: false)"]
        StoreUser --> CodeGen["Generate 6-digit numeric verification code"]
        CodeGen --> VerifyEmail["POST /auth/verify-email (Code validated via HMAC compare)"]
        VerifyEmail --> UserActive["User marked ACTIVE & VERIFIED"]
        UserActive --> Login["POST /auth/login"]
        Login --> IssueJWT["Issue HS256 JWT Token (Claims: sub, role, email)"]
    end

    subgraph AdminGate["2. Encapsulated Hidden Admin Gate"]
        Trigger["Secret Hotkey: Ctrl+Shift+A / 5x Logo Click / ?admin_gate=1"] --> Prompt["Restricted Access Authentication Modal"]
        Prompt --> AdminAuth["POST /auth/login (Requires ADMIN Role)"]
        AdminAuth --> CheckRole{"Role == 'ADMIN'?"}
        CheckRole -- No --> Deny["HTTP 403 Forbidden (Audit Logged)"]
        CheckRole -- Yes --> Unlock["Unlock Dark Theme Catalog Inventory Control"]
    end

    subgraph PaymentSecurity["3. Cryptographic Payment Verification"]
        SubmitSig["Customer submits payment details & signature"] --> PostVerify["POST /orders/{id}/payment/verify"]
        PostVerify --> SignatureCheck{"Verification Mode"}
        SignatureCheck -- Live --> HMACVal["HMAC-SHA256(order_id + '|' + payment_id, secret)"]
        SignatureCheck -- Sandbox --> SimVal["Simulated Sandbox Signature Match"]
        HMACVal --> Success["Payment Confirmed -> Order Marked PAID"]
        SimVal --> Success
    end
```

---

## 7. Kubernetes Cluster Deployment Architecture

Production topology deployed on a Kubernetes cluster with isolated namespaces, Services, Ingress, and persistent volume storage.

```mermaid
flowchart TD
    Ingress["Kubernetes Ingress Controller (Nginx / Traefik)"] -->|"Port 80/443"| GatewaySvc["Service: api-gateway (ClusterIP :8000)"]

    subgraph Cluster["Kubernetes Cluster (Namespace: ecommerce)"]
        GatewaySvc --> GatewayPods["Deployment: api-gateway (Replicas: 2)"]

        subgraph ServicesDeployment["Microservice Deployments"]
            GatewayPods -->|"HTTP :8001"| AuthSvc["Service: user-auth-service"]
            GatewayPods -->|"HTTP :8002"| ProdSvc["Service: product-service"]
            GatewayPods -->|"HTTP :8003"| PaySvc["Service: payment-service"]
            GatewayPods -->|"HTTP :8004"| OrderSvc["Service: order-service"]
            GatewayPods -->|"HTTP :8005"| CartSvc["Service: cart-service"]

            AuthSvc --> AuthPods["Pods: user-auth-service (Replicas: 2)"]
            ProdSvc --> ProdPods["Pods: product-service (Replicas: 2)"]
            PaySvc --> PayPods["Pods: payment-service (Replicas: 2)"]
            OrderSvc --> OrderPods["Pods: order-service (Replicas: 2)"]
            CartSvc --> CartPods["Pods: cart-service (Replicas: 2)"]
        end

        subgraph StatefulTier["StatefulSets & Persistent Volumes"]
            ProdPods <--> RedisSvc["Service: redis-service (Port 6379)"]

            AuthPods --> AuthDBSvc["Service: auth-db (Port 5432)"]
            ProdPods --> ProdDBSvc["Service: product-db (Port 5432)"]
            PayPods --> PayDBSvc["Service: payment-db (Port 5432)"]
            OrderPods --> OrderDBSvc["Service: order-db (Port 5432)"]
            CartPods --> CartDBSvc["Service: cart-db (Port 5432)"]

            AuthDBSvc --> AuthPVC["PVC: auth-db-pvc (5Gi)"]
            ProdDBSvc --> ProdPVC["PVC: product-db-pvc (5Gi)"]
            PayDBSvc --> PayPVC["PVC: payment-db-pvc (5Gi)"]
            OrderDBSvc --> OrderPVC["PVC: order-db-pvc (5Gi)"]
            CartDBSvc --> CartPVC["PVC: cart-db-pvc (5Gi)"]
        end
    end
```

---

## 8. Crossplane Continuous Drift Detection & Keep-Alive Architecture

The infrastructure uses **Crossplane** Custom Resources (`XRD`, `Composition`, `Claim`) to define and enforce continuous drift detection and container self-healing across the 12-container fleet.

```mermaid
flowchart TD
    subgraph ControlPlane["Crossplane Control Plane Layer (k8s/crossplane/)"]
        Provider["Provider: provider-docker (v0.44+) / provider-kubernetes"]
        XRD["CompositeResourceDefinition: ContainerFleet\nxcontainerfleets.platform.ecommerce.io"]
        Comp["Composition: container-fleet-docker.platform.ecommerce.io"]
        Claim["Claim: ecommerce-fleet (claim-ecommerce-fleet.yaml)"]
        
        Provider --> Comp
        XRD --> Comp
        Claim --> XRD
    end

    subgraph RuntimeSupervisor["Runtime Drift & Keep-Alive Supervisor (API Gateway)"]
        AuditLoop["Continuous Drift Audit Loop (Interval: 15s)"]
        ActiveProbes["Active Multi-Vector Health Probes"]
        DriftComparator{"Observed vs Desired Spec"}
        Healer["Automated Self-Healing Engine"]

        AuditLoop --> ActiveProbes
        ActiveProbes --> DriftComparator
    end

    Claim -.->|"Desired State Contract"| DriftComparator

    subgraph ContainerFleet["12-Container Application Fleet"]
        AppTier["App Microservices (:8000-:8005)"]
        DBTier["PostgreSQL Databases (:5432)"]
        CacheTier["Redis Cache (:6379)"]
    end

    ActiveProbes --> AppTier
    ActiveProbes --> DBTier
    ActiveProbes --> CacheTier

    DriftComparator -->|"Matched (0 Drifts)"| Synced["Status: SYNCHRONIZED\nKeep-Alive Guard Active"]
    DriftComparator -->|"Mismatch (Process exit, unreachability)"| Drifted["Status: DRIFT_DETECTED"]

    Drifted --> Healer
    Healer -->|"docker start / docker restart"| ContainerFleet
    Healer -->|"Re-probe Fleet"| AuditLoop
```

### Declarative Crossplane Resources
1. **`k8s/crossplane/providers.yaml`**: Installs Crossplane providers for Docker and Kubernetes to manage container instances directly via Kubernetes declarative semantics.
2. **`k8s/crossplane/xrd-container-fleet.yaml`**: Defines the `CompositeResourceDefinition` `ContainerFleet` with schema validation for desired containers, keep-alive guard policy, probe intervals, and drift status reports.
3. **`k8s/crossplane/composition-container-fleet.yaml`**: Composes the 12 containers into a unified composite resource with declarative environment variables, port mappings, volume mounts, and network links.
4. **`k8s/crossplane/claim-ecommerce-fleet.yaml`**: The operational claim requesting continuous monitoring (`driftDetectionInterval: 15s`, `keepAliveUntilClose: true`, `autoHealOnDrift: true`).
5. **Runtime Drift Supervisor**: Implemented in [`services/api-gateway/crossplane_drift_controller.py`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/services/api-gateway/crossplane_drift_controller.py) to actively evaluate the desired Crossplane fleet specification, expose live endpoints (`/health/crossplane-drift`, `/health/crossplane-drift/reconcile`), and power the Admin Console's Crossplane drift audit card.
