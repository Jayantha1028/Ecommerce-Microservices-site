# 🛡️ Platform Privacy & Security Policy

Last Updated: November 1, 2026
Applicable Platform: **Enterprise E-Commerce Microservices Platform**
Owner / Security Lead: **Jay (jayanthanayak1028@gmail.com)**
GitHub: **[https://github.com/Jayantha1028/Ecommerce-Microservices-site](https://github.com/Jayantha1028/Ecommerce-Microservices-site)**

---

## 1. Executive Summary & Privacy Principles

This E-Commerce Microservices Platform was engineered from the ground up with a **Security-by-Design** and **Privacy-by-Default** philosophy. We adhere to the core principles of data minimization, perimeter reverse-proxy containment, cryptographic identity verification, zero-retention financial boundaries, and complete database-per-service isolation.

### Core Privacy Guarantees:
- 🔒 **Zero Plaintext Credentials:** Passwords are never stored in plaintext; all credentials undergo irreversible cryptographic key derivation using `scrypt` with 16-byte random salts.
- 💳 **Zero Financial Exposure (Zero PCI-DSS Footprint):** Credit card numbers, debit card numbers, CVVs, expiry dates, and UPI PINs are **never handled, transmitted, or stored** on our backend databases. All monetary transactions are processed directly via **Razorpay Payments** and verified cryptographically via **HMAC-SHA256**.
- 🧱 **Database-per-Service Network Isolation:** Every microservice possesses its own private database (`auth_db`, `product_db`, `order_db`, `cart_db`, `payment_db`). No shared databases exist, and none of our database containers are exposed to the public internet.
- 🛡️ **Anti-Header Spoofing & Hop-by-Hop Scrubbing:** The API Gateway purges all client-supplied identity claims (`X-Auth-*`) and RFC 7230 transport headers, ensuring malicious actors cannot elevate privileges or inject spoofed headers.

---

## 2. Information We Collect & Why

We collect strictly the minimum information necessary to execute e-commerce orders, authenticate sessions, and track physical delivery journeys.

| Category | Specific Data Points | Purpose | Storage Boundary | Retention Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Identity & Account** | Name, Email address, Encrypted Password Hash (`scrypt`) | Account registration, authentication, and session management | `auth_db` | Maintained until customer requests account deletion |
| **Delivery Information** | Recipient Name, Street Address, City, State, Postal Code, Country | Calculating delivery timelines, courier route allocation, and doorstep delivery | `order_db` & `user_profiles` | Attached to historical orders for dispute resolution |
| **Session Claims** | Ephemeral JWT Bearer Tokens (Subject UUID, Role, Issue Time) | Stateless API request authorization across microservices | Client-side `localStorage` | Automatically expires after token TTL |
| **Order History** | Order UUID, Product SKUs, Quantities, Frozen Snapshot Prices, Grand Total | Order fulfillment, live shipment tracking, and cancellation window calculation | `order_db` | Retained for consumer audit and purchase history |
| **Tracking Milestones** | Carrier Waybill AWB (`BLUEDART-IND-...`), Hub Checkpoints, Delivery Status | Real-time shipment stepper simulation and package routing updates | `order_db` | Preserved with completed orders |

---

## 3. Information We NEVER Collect or Store

To eliminate consumer risk and maintain compliance with global standards (GDPR, CCPA, and RBI/PCI-DSS):

1. **Cardholder Data (CHD) & Sensitive Authentication Data (SAD):**
   - We do not receive, store, or log 16-digit card numbers, cardholder names, CVV codes, or card expiration dates.
   - Payments are executed via client-side hosted fields / SDKs communicating directly with **Razorpay**.
   - Our `payment-service` only records non-sensitive operational identifiers: `payment_id`, `razorpay_order_id`, monetary amount, and success status.
2. **UPI PINs or Net Banking Credentials:**
   - UPI PINs and banking passwords are typed strictly within NPCI-certified or bank-certified secure frames. Our servers never intercept these packets.
3. **Telemetry & Ad Trackers:**
   - We do not embed third-party advertising cookies, ad tracking beacons, or cross-site tracking pixels.
   - Your shopping cart, bookmarks, and search filters remain completely private to your active session.

---

## 4. Deep-Dive Security Architecture & Technical Controls

### A. Password Cryptography (`scrypt`)
When you register or update your password in `user-auth-service`:
1. A cryptographically secure 16-byte random salt is generated from `/dev/urandom`.
2. The password and salt are hashed using `scrypt` (CPU and memory-hard key derivation function).
3. The derived hash is stored in `auth_db.users`. Even if a raw database backup were intercepted, rainbow-table lookups and GPU-accelerated brute-force attacks are computationally infeasible.

### B. Stateless JWT Session Tokens & Leeway Clocks
- Session authorization uses standard **RFC 7519 JSON Web Tokens (JWT)** signed via **HMAC-SHA256 (HS256)** using a 32+ character high-entropy `JWT_SECRET`.
- Downstream services accept validated identity claims (`sub`, `role`) injected strictly by the perimeter API Gateway.
- Includes a **30-second clock skew leeway** buffer to tolerate distributed server timestamp drifts across Docker/Kubernetes container nodes.

### C. Perimeter Gateway Anti-Spoofing & RFC 7230 Scrubbing
The `api-gateway` operates as the single perimeter guard:
- **Purging Injected Headers:** Any request arriving from the outside world with `X-Auth-User-Id` or `X-Auth-User-Role` is instantly stripped. Only the gateway's verified cryptographic token decoder can inject these identity claims into downstream microservices.
- **Hop-by-Hop Header Stripping:** Under RFC 7230 §6.1, transport headers (`Connection`, `Keep-Alive`, `Upgrade`, `Proxy-Authenticate`) are filtered out to prevent protocol desynchronization and socket hanging.

### D. Cryptographic Payment Verification (HMAC-SHA256)
When a checkout transaction completes:
1. Razorpay passes a signature: $\text{HMAC-SHA256}(\text{order\_id} \mathbin{\Vert} \text{payment\_id}, \text{secret})$.
2. `payment-service` recalculates this cryptographic digest independently using `RAZORPAY_KEY_SECRET`.
3. To eliminate **microsecond side-channel timing attacks**, signatures are compared using `hmac.compare_digest` (strict constant-time $O(n)$ verification). An attacker cannot guess valid payment signatures by measuring execution latency.

### E. Pessimistic Row-Level Database Locking
To protect against race conditions and concurrent double-spending attacks:
- When an order reserves inventory, `product-service` issues `SELECT ... FOR UPDATE` via SQLAlchemy.
- PostgreSQL locks the specific inventory row. Other concurrent requests must wait until the transaction commits, guaranteeing that two customers cannot simultaneously purchase the last unit in stock.

---

## 5. User Privacy Rights & Controls

As a consumer on our platform, you possess full sovereignty over your personal data:

1. **Right to Access & Inspection:**
   - View your profile data, registration email, delivery address, and contact details anytime by clicking **Account** in the storefront.
   - Inspect all historical purchases and transaction receipts via the **Order History** modal.
2. **Right to Rectification (Edit Profile):**
   - Click **Account** $\to$ **Edit Profile** to immediately modify your name, delivery address, city, postal code, and country. Changes propagate across future orders instantly.
3. **Right to Order Cancellation & Stock Return:**
   - Customers have the right to cancel any placed order within the active cancellation window (up until 6 hours before estimated arrival).
   - Upon cancellation, reserved inventory is automatically returned to the public catalog, and orders are safely retired.
4. **Dispatched Transit Lock:**
   - Once a package enters live air cargo transit (`SHIPPED` or `OUT_FOR_DELIVERY`), cancellation is locked to ensure physical delivery safety and courier accountability.
5. **Right to Data Erasure (Account Deletion):**
   - Users may request complete account erasure by contacting our Privacy and Security Officer. All personal records in `auth_db` and associated profiles will be purged.

---

## 6. Developer & Administrative Access Controls

The platform implements strict role-based access control (RBAC):
- **Customer Role:** Can read published products, manage personal cart items, execute personal orders, and view personal history. Cannot modify catalog prices, adjust inventory stock, or view other customers' orders.
- **Administrator Role:** Restricted behind the **Developer Admin Gate**. Access requires multi-tier authentication with the designated administrator credentials (`admin@example.com`).
- **Audit Trails:** All catalog additions, stock adjustments, and product deletions are logged with timestamps and operator identity.

---

## 7. Contact Data Protection Officer

For privacy inquiries, audit questions, or data erasure requests:

- **Security & Data Protection Lead:** Jay
- **Email:** `jayanthanayak1028@gmail.com`
- **GitHub Repository:** [`https://github.com/Jayantha1028/Ecommerce-Microservices-site`](https://github.com/Jayantha1028/Ecommerce-Microservices-site)
- **Deployment Documentation:** [`doc/README.md`](file:///Users/jayanthanayak/Ecommerce_Microservices_Kubernetes/doc/README.md)
