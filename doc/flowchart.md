# E-Commerce Microservices Architecture & Flowcharts

This document provides visual flowcharts and state diagrams for all core business workflows, architectural boundaries, and transaction lifecycles across the e-commerce microservices platform.

---

## 📑 Table of Contents

1. [Master End-to-End Business Flowchart](#1-master-end-to-end-business-flowchart)
2. [High-Level System & Network Architecture](#2-high-level-system--network-architecture)
3. [User Registration & Authentication Flow](#3-user-registration--authentication-flow)
4. [Product Catalog & Inventory Reservation Flow](#4-product-catalog--inventory-reservation-flow)
5. [Shopping Cart & Checkout Saga Flow](#5-shopping-cart--checkout-saga-flow)
6. [Payment Processing & Cryptographic Verification Flow](#6-payment-processing--cryptographic-verification-flow)
7. [Order Lifecycle State Diagram](#7-order-lifecycle-state-diagram)

---

## 1. Master End-to-End Business Flowchart

This master flowchart visualizes the complete end-to-end customer journey from storefront discovery to order fulfillment:

```mermaid
flowchart TD
    subgraph Phase1["1. Storefront Discovery & Authentication"]
        A["Customer visits Web Storefront (Port 8000)"] --> B["GET /products (Browse Published Catalog)"]
        B --> C{"Has Existing Account?"}
        C -- "No" --> D["POST /auth/register (Create Account)"]
        D --> E["POST /auth/verify-email (Submit 6-Digit Code)"]
        E --> F["POST /auth/login (Submit Email & Password)"]
        C -- "Yes" --> F
        F --> G["Receive Bearer JWT Access Token"]
    end

    subgraph Phase2["2. Shopping Cart Management"]
        G --> H["POST /cart/items (Select Item & Quantity)"]
        H --> I["Cart Service calls Product Service: Verify Stock"]
        I --> J["GET /cart (Review Cart & Live Subtotals)"]
        J --> K["POST /cart/checkout (Submit Checkout Request)"]
    end

    subgraph Phase3["3. Order Orchestration & Stock Locking"]
        K --> L["Cart Service dispatches POST /orders"]
        L --> M["Order Service calls Product Service: Freeze Unit Prices"]
        M --> N["Persist Order in order-db (Status: PAYMENT_PENDING)"]
        N --> O["POST /inventory/reservations (Order ID key)"]
        O --> P["Product Service acquires Row Lock: SELECT ... FOR UPDATE"]
        P --> Q["Stock decremented atomically & Reservation persisted"]
    end

    subgraph Phase4["4. Payment & Order Confirmation"]
        Q --> R["Order Service calls Payment Service: POST /payments/create-order"]
        R --> S["Create Razorpay Order (Offline Simulation / Live)"]
        S --> T["Cart cleared in cart-db"]
        T --> U["Return Order Details & razorpay_order_id to Customer"]
        U --> V["Customer completes payment & submits signature"]
        V --> W["POST /orders/{id}/payment/verify"]
        W --> X["Payment Service validates HMAC-SHA256 Signature"]
        X --> Y["PaymentRecord status transitions to 'success'"]
        Y --> Z["Order status transitions to 'PAID'"]
        Z --> Done["Order Confirmed: Receipt issued to Customer"]
    end
```

---

## 2. High-Level System & Network Architecture

The architecture isolates all downstream microservices and databases on private Docker bridge subnets. The **API Gateway** acts as the single public entry point on port `8000`.

```mermaid
flowchart TD
    Client["Client / Web Browser / Mobile"] -->|"HTTP Requests (Port 8000)"| GW["API Gateway (:8000)"]

    subgraph Internal_Network["Isolated Docker Bridge Subnets"]
        GW -->|"/auth/*"| Auth["User & Auth Service (:8001)"]
        GW -->|"/products/* & /inventory/*"| Prod["Product & Inventory Service (:8002)"]
        GW -->|"/cart/*"| Cart["Cart Service (:8005)"]
        GW -->|"/orders/*"| Order["Order Service (:8004)"]
        GW -->|"/payments/*"| Pay["Payment Service (:8003)"]

        Cart -.->|"Verify Live Stock"| Prod
        Cart -.->|"Submit Order"| Order
        Order -.->|"Freeze Price & Reserve Stock"| Prod
        Order -.->|"Initialize Razorpay Order"| Pay

        Auth -->|"Internal auth-net"| AuthDB[("auth-db (PostgreSQL 16)")]
        Prod -->|"Internal prod-net"| ProdDB[("product-db (PostgreSQL 16)")]
        Cart -->|"Internal cart-net"| CartDB[("cart-db (PostgreSQL 16)")]
        Order -->|"Internal order-net"| OrderDB[("order-db (PostgreSQL 16)")]
        Pay -->|"Internal payment-net"| PayDB[("payment-db (PostgreSQL 16)")]
    end
```

---

## 3. User Registration & Authentication Flow

Covers account creation, one-time email verification codes, password hashing via `scrypt` with random 16-byte salts, and JWT token issuance.

```mermaid
flowchart TD
    Start["Client sends POST /auth/register"] --> CheckEmail{"Email exists in auth-db?"}
    
    CheckEmail -- Yes --> Err409["Return 409 Conflict: Email already registered"]
    CheckEmail -- No --> CreateAccount["Create unverified user account"]
    
    CreateAccount --> GenCode["Generate 6-digit verification code"]
    GenCode --> SaveCode["Store hashed code with 10-minute expiry"]
    SaveCode --> Resp201["Return 201 Created: Verification code sent"]
    
    Resp201 --> VerifyStep["Client sends POST /auth/verify-email with 6-digit code"]
    VerifyStep --> CheckCode{"Code valid and not expired?"}
    
    CheckCode -- No --> Err400["Return 400 Bad Request: Invalid or expired code"]
    CheckCode -- Yes --> ActivateUser["Mark user is_active = True"]
    ActivateUser --> Confirmed["Account activated"]
    
    Confirmed --> LoginStep["Client sends POST /auth/login with email and password"]
    LoginStep --> FindUser{"User exists in database?"}
    
    FindUser -- No --> DummyHash["Run dummy scrypt hash to prevent timing attacks"]
    DummyHash --> Err401["Return 401 Unauthorized: Invalid credentials"]
    
    FindUser -- Yes --> VerifyHash{"Verify scrypt hash with stored salt"}
    VerifyHash -- Mismatch --> Err401
    VerifyHash -- Match --> CheckActive{"Is account active?"}
    
    CheckActive -- No --> ErrInactive["Return 403 Forbidden: Email verification required"]
    CheckActive -- Yes --> IssueJWT["Issue HS256 JWT Token with user_id and role"]
    IssueJWT --> ReturnToken["Return Bearer Token (Expires in 24 hours)"]
```

---

## 4. Product Catalog & Inventory Reservation Flow

Illustrates how product catalog creation works, along with atomic inventory stock reservations utilizing PostgreSQL `SELECT ... FOR UPDATE` pessimistic row locking.

```mermaid
flowchart TD
    Req["Request received at Product Service"] --> CheckType{"Request Type"}

    CheckType -- "Admin: Create/Update Catalog" --> VerifyAdmin{"Role == ADMIN or PRODUCT_MANAGER?"}
    VerifyAdmin -- No --> Ret403["Return 403 Forbidden"]
    VerifyAdmin -- Yes --> PersistCatalog["Persist Product and initialize Inventory row"]
    PersistCatalog --> Ret201["Return 201 Created"]

    CheckType -- "Customer: Browse Catalog" --> FilterPublished["Query products WHERE status == 'PUBLISHED'"]
    FilterPublished --> RetList["Return catalog list"]

    CheckType -- "Order Service: Reserve Stock" --> CheckIdempotent{"Reservation exists for order_id?"}
    CheckIdempotent -- Yes --> ReturnExisting["Return existing reservation idempotently"]
    CheckIdempotent -- No --> LockRow["Acquire row-level lock: SELECT ... FOR UPDATE"]

    LockRow --> CheckStock{"Available Stock >= Requested Quantity?"}
    CheckStock -- No --> RollbackStock["Rollback transaction and return 409 Insufficient Stock"]
    CheckStock -- Yes --> DeductStock["Deduct quantity from inventory row"]
    DeductStock --> CreateReservation["Insert Reservation and ReservationItem rows"]
    CreateReservation --> CommitRes["Commit transaction and return 201 Reserved"]
```

---

## 5. Shopping Cart & Checkout Saga Flow

Demonstrates the distributed checkout orchestration across the Cart Service, Product Service, and Order Service.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer (Client)
    participant GW as API Gateway (:8000)
    participant Cart as Cart Service (:8005)
    participant Order as Order Service (:8004)
    participant Prod as Product Service (:8002)
    participant Pay as Payment Service (:8003)

    Note over Customer,GW: Step 1: Add Item to Cart
    Customer->>GW: POST /cart/items {product_id, quantity} (Bearer JWT)
    GW->>Cart: Forward with X-Auth-User-Id & X-Auth-User-Role
    Cart->>Prod: GET /products/{product_id}
    Prod-->>Cart: 200 OK {price, stock, status: "PUBLISHED"}
    Cart->>Cart: Upsert CartItem in cart_db
    Cart-->>Customer: 201 Created

    Note over Customer,GW: Step 2: Checkout Cart
    Customer->>GW: POST /cart/checkout {currency: "INR"}
    GW->>Cart: Forward checkout request
    Cart->>Cart: Query all user items from cart_db
    Cart->>Order: POST /orders {items, currency}

    Note over Order,Prod: Step 3: Order Creation & Stock Lock
    Order->>Prod: GET /products/{id} for all items (Freeze snapshot prices)
    Order->>Order: Persist Order (status: "PAYMENT_PENDING")
    Order->>Prod: POST /inventory/reservations (Pessimistic row lock)
    Prod-->>Order: 201 Created {reservation_id, status: "RESERVED"}

    Note over Order,Pay: Step 4: Payment Initialization
    Order->>Pay: POST /payments/create-order {order_id, amount, currency}
    Pay-->>Order: 201 Created {payment_id, razorpay_order_id}
    Order->>Order: Update order with payment identifiers
    Order-->>Cart: 201 Created {order_id, razorpay_order}

    Note over Cart,Customer: Step 5: Clear Cart
    Cart->>Cart: DELETE FROM cart_items WHERE user_id = :id
    Cart-->>Customer: 201 Created {order, message: "Checkout complete"}
```

---

## 6. Payment Processing & Cryptographic Verification Flow

Shows how Razorpay payment orders are created, idempotently handled, and verified using HMAC-SHA256 signatures or offline sandbox simulation mode.

```mermaid
flowchart TD
    Start["Client sends POST /payments/create-order"] --> CheckExisting{"Active payment exists for order_id?"}

    CheckExisting -- "Status == success" --> ErrPaid["Return 409 Conflict: Order already paid"]
    CheckExisting -- "Status == pending (identical amount)" --> ReturnExisting["Return existing payment record idempotently"]
    CheckExisting -- "Status == pending (different amount)" --> ErrConflict["Return 409 Conflict: Conflicting amount"]
    CheckExisting -- "No existing record" --> CheckMode{"PAYMENT_SIMULATION_MODE enabled?"}

    CheckMode -- "Yes (Zero Cost / Offline)" --> SimOrder["Generate simulated order: order_sim_..."]
    CheckMode -- "No (Live Razorpay)" --> RzpSDK["Call razorpay_client.order.create()"]

    SimOrder --> SavePayment["Insert PaymentRecord with status = 'pending'"]
    RzpSDK --> SavePayment
    SavePayment --> RetPayment["Return payment_id and razorpay_order_id"]

    RetPayment --> ClientVerify["Client completes checkout and sends POST /orders/{id}/payment/verify"]
    ClientVerify --> ForwardPay["Order Service calls POST /payments/verify with signature"]

    ForwardPay --> CheckSimSig{"Simulation Mode?"}
    CheckSimSig -- Yes --> VerifySim["Verify simulated signature or mock_signature_test"]
    CheckSimSig -- No --> VerifyHMAC["Call razorpay.utility.verify_payment_signature()"]

    VerifySim -- Failed --> SigFail["Return 400 Bad Request: Signature mismatch"]
    VerifyHMAC -- Failed --> SigFail

    VerifySim -- Valid --> MarkSuccess["Update PaymentRecord status = 'success'"]
    VerifyHMAC -- Valid --> MarkSuccess

    MarkSuccess --> UpdateOrder["Order Service transitions Order status = 'PAID'"]
    UpdateOrder --> Done["Return 200 OK: Payment verified and order confirmed"]
```

---

## 7. Order Lifecycle State Diagram

The formal state machine governing an order from creation through payment confirmation or cancellation with compensating inventory release.

```mermaid
stateDiagram-v2
    [*] --> PAYMENT_PENDING: Customer initiates checkout via Cart Service

    state PAYMENT_PENDING {
        [*] --> AwaitingPayment: Stock reserved via Product Service
        AwaitingPayment --> PaymentFailed: User payment fails or cancels on gateway
        PaymentFailed --> AwaitingPayment: Client calls POST /orders/{id}/payment (Retry)
    }

    PAYMENT_PENDING --> PAID: Signature verified via POST /orders/{id}/payment/verify
    PAYMENT_PENDING --> CANCELLED: Order cancelled via POST /orders/{id}/cancel

    state CANCELLED {
        [*] --> ReleaseInventory: Call /inventory/reservations/release
        ReleaseInventory --> OrderVoided: Inventory restored to available stock
    }

    PAID --> [*]: Order fulfilled (Terminal state)
    CANCELLED --> [*]: Order closed (Terminal state)
```
