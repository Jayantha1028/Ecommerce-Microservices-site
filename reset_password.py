"""Emergency / Maintenance Password Reset Script.

Allows an operator to securely hash a new password using scrypt and update
a user account directly in PostgreSQL (via kubectl exec into the auth pod).
"""

import getpass
import hashlib
import os
import secrets
import subprocess
import sys

# Target email account to reset (command line argument or fallback)
if len(sys.argv) > 1 and sys.argv[1].strip():
    email = sys.argv[1].strip()
else:
    email = input("Enter email address to reset [default: testcustomer@example.com]: ").strip() or "testcustomer@example.com"

# Prompt operator for password with masked inputs
password = getpass.getpass(f"Enter new password for '{email}': ")
confirm = getpass.getpass("Confirm new password: ")

if password != confirm:
    sys.exit("Passwords do not match.")

if len(password) < 12:
    sys.exit("Use a password with at least 12 characters.")

# Compute scrypt password hash matching auth-service specifications
salt = secrets.token_bytes(16)
digest = hashlib.scrypt(
    password.encode(),
    salt=salt,
    n=2**14,
    r=8,
    p=1,
)
password_hash = salt.hex() + "$" + digest.hex()

# Remote Python script to execute inside the cluster container.
# Reads data safely via stdin and connects using the container's DATABASE_URL.
script = r'''
import os
import sys
import psycopg2

password_hash = sys.stdin.readline().strip()
email = sys.stdin.readline().strip().lower()

if not password_hash or not email:
    raise ValueError("Missing password hash or email input.")

db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("postgresql+psycopg2://"):
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql://", 1)

connection = psycopg2.connect(db_url)

try:
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE email = %s",
                (password_hash, email),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(
                    f"Expected 1 account to update for {email}, matched {cursor.rowcount}"
                )
    print(f"Password for {email} updated successfully.")
finally:
    connection.close()
'''

stdin_payload = f"{password_hash}\n{email}\n"

# Dispatch execution to the user-auth deployment in Kubernetes
result = subprocess.run(
    [
        "kubectl", "exec", "-i", "-n", "ecommerce",
        "deployment/user-auth-service", "--", "python", "-c", script,
    ],
    input=stdin_payload,
    text=True,
    capture_output=True,
)

print(result.stdout, end="")
if result.returncode != 0:
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)
