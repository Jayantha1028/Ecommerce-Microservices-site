#!/usr/bin/env bash
# ==============================================================================
# One-Click Application Runner for E-Commerce Microservices
# Starts all 11 containers, checks health, and bootstraps initial data.
# ==============================================================================
set -euo pipefail

# ANSI Color Codes
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}             E-COMMERCE MICROSERVICES APPLICATION RUNNER             ${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo "Working Directory: ${ROOT_DIR}"
echo ""

# ------------------------------------------------------------------------------
# 1. Check Docker Daemon
# ------------------------------------------------------------------------------
echo -e "🔍 Checking Docker environment..."
if ! command -v docker >/dev/null 2>&1; then
  echo -e "${RED}Error: 'docker' CLI is not installed or not in PATH.${NC}" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo -e "${RED}Error: Docker daemon is not running.${NC}" >&2
  echo -e "Please start Docker Desktop and re-run this script." >&2
  exit 1
fi
echo -e "${GREEN}✔ Docker engine is active.${NC}"

# ------------------------------------------------------------------------------
# 2. Check / Setup .env File
# ------------------------------------------------------------------------------
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}Notice: .env file not found. Generating from .env.example...${NC}"
  cp .env.example .env

  # Generate random 32+ char JWT Secret
  RANDOM_JWT=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
  sed -i.bak "s|^JWT_SECRET=.*|JWT_SECRET=${RANDOM_JWT}|" .env && rm -f .env.bak

  # Generate alphanumeric passwords for each database
  for db in AUTH PRODUCT ORDER PAYMENT CART; do
    PASS=$(openssl rand -hex 12 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(12))")
    sed -i.bak "s|^${db}_DB_PASSWORD=.*|${db}_DB_PASSWORD=${PASS}|" .env && rm -f .env.bak
  done

  echo -e "${GREEN}✔ Generated fresh .env with secure JWT secret and database credentials.${NC}"
  echo -e "${YELLOW}  Note: If testing real Razorpay orders, set RAZORPAY_KEY_ID & RAZORPAY_KEY_SECRET in .env${NC}"
else
  echo -e "${GREEN}✔ Found existing .env configuration.${NC}"
fi

# ------------------------------------------------------------------------------
# 3. Build & Start Docker Compose Stack
# ------------------------------------------------------------------------------
echo ""
echo -e "🚀 Starting all 11 microservices and PostgreSQL databases..."
docker compose up -d --build

# ------------------------------------------------------------------------------
# 4. Wait for API Gateway & Services to become Healthy
# ------------------------------------------------------------------------------
GATEWAY_URL="http://127.0.0.1:${GATEWAY_PORT:-8000}"
echo ""
echo -n "⏳ Waiting for API Gateway to become healthy at ${GATEWAY_URL}/health "

MAX_RETRIES=40
COUNT=0
HEALTHY=false

while [ "${COUNT}" -lt "${MAX_RETRIES}" ]; do
  if curl -s -f "${GATEWAY_URL}/health" >/dev/null 2>&1; then
    HEALTHY=true
    break
  fi
  COUNT=$((COUNT + 1))
  echo -n "."
  sleep 2
done

if [ "${HEALTHY}" = true ]; then
  echo -e " ${GREEN}READY!${NC}"
else
  echo -e " ${RED}TIMED OUT!${NC}"
  echo -e "${RED}Error: API Gateway failed to become healthy within $((MAX_RETRIES * 2)) seconds.${NC}" >&2
  echo ""
  echo "Container status:"
  docker compose ps
  echo ""
  echo "Check container logs with: docker compose logs api-gateway"
  exit 1
fi

# ------------------------------------------------------------------------------
# 5. Bootstrap Baseline Administrator & Catalog
# ------------------------------------------------------------------------------
echo ""
echo -e "🌱 Bootstrapping administrator account and baseline catalog..."
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

if [ -n "${PYTHON_BIN}" ]; then
  "${PYTHON_BIN}" scripts/bootstrap.py || echo -e "${YELLOW}Notice: Bootstrapper completed with non-fatal status.${NC}"
else
  echo -e "${YELLOW}Notice: Python not detected on host. Skipping local bootstrap script.${NC}"
fi

# ------------------------------------------------------------------------------
# 6. Display Status and Access Information
# ------------------------------------------------------------------------------
echo ""
echo -e "${CYAN}----------------------------------------------------------------------${NC}"
echo -e "${CYAN}                     CONTAINER STATUS OVERVIEW                        ${NC}"
echo -e "${CYAN}----------------------------------------------------------------------${NC}"
docker compose ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}       🎉 APPLICATION IS RUNNING AND READY TO RECEIVE TRAFFIC!        ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "🌐 Access Points:"
echo -e "   • API Gateway URL:   ${CYAN}${GATEWAY_URL}${NC}"
echo -e "   • Health Endpoint:   ${CYAN}${GATEWAY_URL}/health${NC}"
echo -e "   • Swagger UI Docs:   ${CYAN}${GATEWAY_URL}/docs${NC}"
echo -e "   • Product Catalog:   ${CYAN}${GATEWAY_URL}/products${NC}"
echo ""
echo -e "🧪 Helpful Commands:"
echo -e "   • Run Test Suite:    ${YELLOW}bash scripts/test_all.sh${NC}"
echo -e "   • View Live Logs:    ${YELLOW}docker compose logs -f [service-name]${NC}"
echo -e "   • Stop Application:  ${YELLOW}docker compose down${NC}"
echo -e "   • Clean Reset (Wipe):${YELLOW}docker compose down -v${NC}"
echo ""
