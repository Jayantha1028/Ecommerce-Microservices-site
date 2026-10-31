#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "      Configuring GitHub Codespace for E-Commerce Microservices       "
echo "======================================================================"

cd /workspaces/ECommerce-Microservices-Docker-Site 2>/dev/null || cd "$(pwd)"

# Ensure bash scripts have execution permissions
chmod +x run.sh stop.sh scripts/*.sh 2>/dev/null || true

# Check / initialize environment variables
if [ ! -f ".env" ]; then
  echo "✔ Creating initial .env from .env.example..."
  cp .env.example .env
  
  RANDOM_JWT=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${RANDOM_JWT}|" .env
  
  for db in AUTH PRODUCT ORDER PAYMENT CART; do
    PASS=$(openssl rand -hex 12 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(12))")
    sed -i "s|^${db}_DB_PASSWORD=.*|${db}_DB_PASSWORD=${PASS}|" .env
  done
  echo "✔ Generated secure random credentials in .env"
fi

# Spin up all 11 microservices and PostgreSQL containers
echo "🚀 Starting all microservices and databases..."
bash run.sh

# Run the 32-test automated verification suite
echo "🧪 Running automated health checks and verification suite..."
bash scripts/test_all.sh || true

echo ""
echo "======================================================================"
echo "    🎉 GitHub Codespaces Environment is Ready for Testing!            "
echo "======================================================================"
echo "  • Storefront / API Gateway: Port 8000 (Forwarded & Open in Browser)"
echo "  • Swagger UI API Docs:      http://localhost:8000/docs"
echo "  • Run Test Suite:           bash scripts/test_all.sh"
echo "  • Stop Stack:               bash stop.sh"
echo "======================================================================"
