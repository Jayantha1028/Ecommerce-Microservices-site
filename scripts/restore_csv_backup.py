"""Restore Microservices PostgreSQL Databases from CSV Backups.

Restores all tables in data/backups/ into:
- product-db (products, inventory, inventory_reservations, inventory_reservation_items)
- auth-db (users, user_profiles, verification_codes)
- order-db (orders, order_items)
- payment-db (payments)
- cart-db (cart_items)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "data" / "backups"

RESTORE_ORDER = [
    {
        "service": "auth-db",
        "user": "auth_user",
        "db": "auth_db",
        "tables": ["users", "user_profiles", "verification_codes"],
    },
    {
        "service": "product-db",
        "user": "product_user",
        "db": "product_db",
        "tables": ["products", "inventory", "inventory_reservations", "inventory_reservation_items"],
    },
    {
        "service": "order-db",
        "user": "order_user",
        "db": "order_db",
        "tables": ["orders", "order_items"],
    },
    {
        "service": "payment-db",
        "user": "payment_user",
        "db": "payment_db",
        "tables": ["payments"],
    },
    {
        "service": "cart-db",
        "user": "cart_user",
        "db": "cart_db",
        "tables": ["cart_items"],
    },
]


def restore_backups():
    """Restore CSV records into running database containers."""
    if not BACKUP_DIR.exists():
        print(f"Error: Backup directory {BACKUP_DIR} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Restoring databases from CSV backups in: {BACKUP_DIR}\n")

    for entry in RESTORE_ORDER:
        service = entry["service"]
        user = entry["user"]
        db = entry["db"]

        print(f"[{service}] Restoring to {db}...")
        for table in entry["tables"]:
            csv_path = BACKUP_DIR / f"{table}.csv"
            if not csv_path.exists():
                print(f"  - Skipping {table} (no CSV found)")
                continue

            # Read CSV content
            with open(csv_path, "r", encoding="utf-8") as f:
                csv_data = f.read()

            query = f"COPY {table} FROM STDIN WITH CSV HEADER;"
            cmd = [
                "docker", "compose", "exec", "-T", service,
                "psql", "-U", user, "-d", db, "-c", query,
            ]

            try:
                res = subprocess.run(cmd, input=csv_data, capture_output=True, text=True, check=True)
                print(f"  ✓ Restored {table}.csv")
            except subprocess.CalledProcessError as exc:
                print(f"  ✗ Failed to restore {table}: {exc.stderr.strip()}", file=sys.stderr)

    print("\n" + "=" * 60)
    print("Database Restoration from CSV Finished!")
    print("=" * 60)


if __name__ == "__main__":
    restore_backups()
