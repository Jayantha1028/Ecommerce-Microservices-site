"""Export all Microservices PostgreSQL Databases to Persistent CSV Backups.

Exports:
- products, inventory, reservations (from product-db)
- users, user_profiles (from auth-db)
- orders, order_items (from order-db)
- payments (from payment-db)
- cart_items (from cart-db)

All CSV files are written to data/backups/ on the local filesystem.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "data" / "backups"

TABLES_TO_EXPORT = [
    {
        "service": "product-db",
        "user": "product_user",
        "db": "product_db",
        "tables": ["products", "inventory", "inventory_reservations", "inventory_reservation_items"],
    },
    {
        "service": "auth-db",
        "user": "auth_user",
        "db": "auth_db",
        "tables": ["users", "user_profiles", "verification_codes"],
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


def export_backups():
    """Execute PostgreSQL COPY commands inside containers and write CSV files."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Exporting database records to CSV in: {BACKUP_DIR}\n")

    total_files = 0
    total_rows = 0

    for entry in TABLES_TO_EXPORT:
        service = entry["service"]
        user = entry["user"]
        db = entry["db"]

        print(f"[{service}] Connecting to {db}...")
        for table in entry["tables"]:
            csv_path = BACKUP_DIR / f"{table}.csv"
            query = f"COPY {table} TO STDOUT WITH CSV HEADER;"
            cmd = [
                "docker", "compose", "exec", "-T", service,
                "psql", "-U", user, "-d", db, "-c", query,
            ]

            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                lines = [line for line in res.stdout.splitlines() if line.strip()]
                row_count = max(0, len(lines) - 1)  # Subtract header

                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(res.stdout)

                total_files += 1
                total_rows += row_count
                print(f"  ✓ Exported {table}.csv ({row_count} rows)")
            except subprocess.CalledProcessError as exc:
                print(f"  ✗ Failed to export {table}: {exc.stderr.strip()}", file=sys.stderr)

    print("\n" + "=" * 60)
    print(f"CSV Backup Complete! {total_files} tables exported, {total_rows} total rows saved.")
    print(f"Backup Location: {BACKUP_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    export_backups()
