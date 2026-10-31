"""Platform Bootstrapper Script.

Ensures that the environment has:
1. An active, email-verified administrator account (`admin@example.com`).
2. An initial catalog product (`LAPTOP-001`) with positive inventory stock.

Can be run standalone or as part of automated test harnesses (`test_all.sh` / `test_all.ps1`).
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

# ==============================================================================
# Configuration & Defaults
# ==============================================================================

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8000").rstrip("/")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "AdminPassword123!")
CUSTOMER_EMAIL = os.getenv("CUSTOMER_EMAIL", "customer@example.com")
CUSTOMER_PASSWORD = os.getenv("CUSTOMER_PASSWORD", "CustomerPassword123!")


# ==============================================================================
# HTTP Client Utility Helpers
# ==============================================================================

def post_json(path: str, data: dict, token: str | None = None) -> tuple[int, dict]:
    """Send an HTTP POST request with a JSON payload and return (status_code, body)."""
    return _send_json("POST", path, data=data, token=token)


def put_json(path: str, data: dict, token: str | None = None) -> tuple[int, dict]:
    """Send an HTTP PUT request with a JSON payload and return (status_code, body)."""
    return _send_json("PUT", path, data=data, token=token)


def _send_json(method: str, path: str, data: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    """Send an HTTP request with an optional JSON payload and return (status_code, body)."""
    url = f"{GATEWAY_URL}{path}"
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Content-Type": "application/json"} if data is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as exc:
        content = exc.read().decode("utf-8")
        try:
            body = json.loads(content) if content else {}
        except Exception:
            body = {"detail": content}
        return exc.code, body


def get_json(path: str, token: str | None = None) -> tuple[int, dict]:
    """Send an HTTP GET request and return (status_code, body)."""
    url = f"{GATEWAY_URL}{path}"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as exc:
        content = exc.read().decode("utf-8")
        try:
            body = json.loads(content) if content else {}
        except Exception:
            body = {"detail": content}
        return exc.code, body


# ==============================================================================
# Bootstrap Execution Logic
# ==============================================================================

def bootstrap() -> bool:
    """Execute the bootstrap sequence to prepare administrative users and seed products."""
    print(f"Bootstrapping administrator ({ADMIN_EMAIL}) and LAPTOP-001 if needed...")

    # Step 1: Register administrator if not exists
    status, body = post_json("/auth/register", {
        "name": "Administrator",
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    })

    if status == 201:
        code = body.get("verificationCode")
        print(f"Registered admin, verification code: {code}")
        if code:
            v_status, _ = post_json("/auth/verify-email", {
                "email": ADMIN_EMAIL,
                "code": code,
            })
            print(f"Verified admin email: status {v_status}")
    elif status == 409 or (status == 400 and "already" in str(body).lower()):
        print("Admin account already registered.")
    else:
        print(f"Registration response: HTTP {status} {body}")

    # Step 2: Ensure role is elevated to ADMIN and account is active in auth-db
    try:
        cmd = [
            "docker", "compose", "exec", "-T", "auth-db",
            "psql", "-U", "auth_user", "-d", "auth_db",
            "-c", f"UPDATE users SET role='ADMIN', verified=true, status='ACTIVE' WHERE email='{ADMIN_EMAIL}';",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        print(f"Promoted admin in database: {res.stdout.strip()}")
    except Exception as e:
        print(f"Notice: Could not run docker compose psql directly: {e}")

    # Step 2b: Register standard test customer if not exists
    c_status, c_body = post_json("/auth/register", {
        "name": "Test Customer",
        "email": CUSTOMER_EMAIL,
        "password": CUSTOMER_PASSWORD,
    })
    if c_status == 201:
        c_code = c_body.get("verificationCode")
        print(f"Registered test customer, verification code: {c_code}")
        if c_code:
            v_status, _ = post_json("/auth/verify-email", {
                "email": CUSTOMER_EMAIL,
                "code": c_code,
            })
            print(f"Verified customer email: status {v_status}")
    elif c_status == 409 or (c_status == 400 and "already" in str(c_body).lower()):
        print("Customer account already registered.")

    # Ensure test customer is active and verified in database
    try:
        cmd_cust = [
            "docker", "compose", "exec", "-T", "auth-db",
            "psql", "-U", "auth_user", "-d", "auth_db",
            "-c", f"UPDATE users SET role='CUSTOMER', verified=true, status='ACTIVE' WHERE email='{CUSTOMER_EMAIL}';",
        ]
        res_cust = subprocess.run(cmd_cust, capture_output=True, text=True, timeout=15)
        print(f"Verified test customer in database: {res_cust.stdout.strip()}")
    except Exception as e:
        print(f"Notice: Could not update customer via psql: {e}")

    # Step 3: Log in as admin to obtain JWT access token
    status, login_body = post_json("/auth/login", {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    })

    if status != 200 or not login_body.get("token"):
        print(f"Failed to log in as administrator: HTTP {status} {login_body}")
        return False

    admin_token = login_body["token"]
    print("Obtained administrator token successfully.")

    # Step 4: Ensure baseline products (around 8 products) exist with adequate stock
    INITIAL_CATALOG = [
        {
            "sku": "LAPTOP-001",
            "name": "Pro Developer Laptop 16-inch",
            "description": "High-performance workstation with 32GB RAM & 1TB NVMe SSD",
            "price": "199999.00",
            "initial_stock": 15,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "PHONE-002",
            "name": "Ultra 5G Flagship Smartphone",
            "description": "120Hz AMOLED edge display, 256GB storage, triple optical camera",
            "price": "89999.00",
            "initial_stock": 25,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "AUDIO-003",
            "name": "Studio ANC Wireless Headphones",
            "description": "Active noise cancelling with 40-hour battery and spatial audio",
            "price": "24999.00",
            "initial_stock": 40,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "DISP-004",
            "name": "4K UHD 27-inch Curved Gaming Monitor",
            "description": "144Hz refresh rate, 1ms HDR400 IPS panel with ultra-thin bezels",
            "price": "44999.00",
            "initial_stock": 20,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "KEYB-005",
            "name": "Mechanical RGB Gaming Keyboard",
            "description": "Hot-swappable tactile switches, aircraft aluminum plate, per-key RGB",
            "price": "12999.00",
            "initial_stock": 35,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "MOUS-006",
            "name": "Ergonomic Wireless Precision Mouse",
            "description": "16,000 DPI optical tracking, hyper-fast scroll wheel, multi-device",
            "price": "7499.00",
            "initial_stock": 50,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "TABL-007",
            "name": "Ultra-Slim 11-inch Tablet 128GB",
            "description": "High-resolution OLED screen with active stylus support & all-day battery",
            "price": "54999.00",
            "initial_stock": 18,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "WATCH-008",
            "name": "Smart Fitness & Health Tracker",
            "description": "Continuous heart rate, GPS tracking, sleep coaching, 50m water resistant",
            "price": "24999.00",
            "initial_stock": 30,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "LAPTOP-009",
            "name": "Apple MacBook Air 13-inch M3",
            "description": "Ultra-thin aluminum chassis, 16GB unified memory, 512GB SSD, up to 18 hours battery life",
            "price": "114900.00",
            "initial_stock": 25,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "AUDIO-010",
            "name": "Sony WH-1000XM5 Wireless Headphones",
            "description": "Industry-leading active noise cancellation with 8 mics, 30-hour battery, and spatial audio",
            "price": "29990.00",
            "initial_stock": 30,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "DISP-011",
            "name": "Dell UltraSharp 32-inch 4K UHD Hub Monitor",
            "description": "IPS Black technology, 98% DCI-P3 color gamut, integrated 90W USB-C hub with RJ45 connectivity",
            "price": "79999.00",
            "initial_stock": 15,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "GAME-012",
            "name": "Sony PlayStation 5 Slim 1TB Console",
            "description": "Ultra-high speed 1TB SSD, ray tracing, Tempest 3D audio, and DualSense haptic feedback",
            "price": "44990.00",
            "initial_stock": 20,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "MOUS-013",
            "name": "Logitech MX Master 3S Wireless Mouse",
            "description": "Quiet click switches, 8,000 DPI track-on-glass sensor, and MagSpeed electromagnetic wheel",
            "price": "9495.00",
            "initial_stock": 45,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "KEYB-014",
            "name": "Keychron Q1 Pro Custom Mechanical Keyboard",
            "description": "Full aluminum CNC body, hot-swappable switches, double-gasket mount, and wireless Bluetooth",
            "price": "18499.00",
            "initial_stock": 30,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "TABL-015",
            "name": "Apple iPad Air 11-inch M2 Liquid Retina",
            "description": "Apple M2 silicon, 11-inch Liquid Retina display, landscape 12MP Center Stage front camera",
            "price": "59900.00",
            "initial_stock": 22,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "PHONE-016",
            "name": "Samsung Galaxy S24 Ultra 5G AI Phone",
            "description": "Titanium construction, 200MP quad telephoto camera system, built-in S Pen, and Galaxy AI",
            "price": "129999.00",
            "initial_stock": 20,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "DRON-017",
            "name": "DJI Mini 4 Pro 4K HDR Drone with RC 2",
            "description": "Sub-249g ultra-lightweight drone, omnidirectional obstacle sensing, 4K/60fps HDR, 34m flight time",
            "price": "84999.00",
            "initial_stock": 14,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "SPKR-018",
            "name": "Bose SoundLink Revolve+ II 360 Speaker",
            "description": "True 360-degree immersive acoustic coverage, water and dust resistant (IP55), 17h battery",
            "price": "29400.00",
            "initial_stock": 28,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "CHRG-019",
            "name": "Anker Prime 250W High-Speed Power Bank",
            "description": "27,650mAh capacity, 250W multi-device fast output, smart app display, charges laptops rapidly",
            "price": "16999.00",
            "initial_stock": 50,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=600&auto=format&fit=crop&q=80",
        },
        {
            "sku": "STRE-020",
            "name": "Elgato Stream Deck MK.2 Studio Console",
            "description": "15 customizable tactile LCD keys to trigger macros, audio routing, scenes, and app workflows",
            "price": "14499.00",
            "initial_stock": 35,
            "status": "PUBLISHED",
            "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&auto=format&fit=crop&q=80",
        },
    ]

    status, catalog = get_json("/products")
    existing_items = catalog.get("data", []) if isinstance(catalog, dict) else []
    existing_by_sku = {p.get("sku"): p for p in existing_items}

    for item in INITIAL_CATALOG:
        sku = item["sku"]
        if sku not in existing_by_sku:
            status, prod_body = post_json("/products", item, token=admin_token)
            if status == 201:
                print(f"Created catalog product {sku} ({item['name']}).")
            else:
                print(f"Notice creating {sku}: HTTP {status} {prod_body}")
        else:
            p = existing_by_sku[sku]
            pid = p.get("id")
            # Update price and metadata if market level price or image differs
            needs_update = (str(p.get("price")) != str(item["price"])) or (item.get("image_url") and not p.get("image_url"))
            if needs_update:
                put_json(
                    f"/products/{pid}",
                    {
                        "name": item["name"],
                        "description": item["description"],
                        "price": float(item["price"]),
                        "status": item["status"],
                        "image_url": item.get("image_url", p.get("image_url")),
                    },
                    token=admin_token,
                )
                print(f"Updated product details & image for {sku} (price: ₹{item['price']}).")

            if sku == "LAPTOP-001" and p.get("stock") != 10:
                put_json(f"/inventory/{pid}", {"quantity": 10}, token=admin_token)
                print(f"Reset stock for {sku} to 10 for test baseline.")
            elif p.get("stock", 0) < 5:
                put_json(f"/inventory/{pid}", {"quantity": item["initial_stock"]}, token=admin_token)
                print(f"Replenished stock for {sku} to {item['initial_stock']}.")

    print(f"Bootstrap completed successfully. {len(INITIAL_CATALOG)} products ready.")
    return True


if __name__ == "__main__":
    bootstrap()
