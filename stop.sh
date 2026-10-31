#!/usr/bin/env bash
# ==============================================================================
# Graceful Shutdown Script for E-Commerce Microservices
# ==============================================================================
set -euo pipefail

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}              STOPPING E-COMMERCE MICROSERVICES PLATFORM              ${NC}"
echo -e "${CYAN}======================================================================${NC}"

if [ "${1:-}" = "-v" ] || [ "${1:-}" = "--volumes" ]; then
  echo -e "${YELLOW}Stopping containers and removing all database volumes (clean wipe)...${NC}"
  docker compose down -v
  echo -e "${GREEN}✔ All containers stopped and data volumes wiped.${NC}"
else
  echo -e "Stopping containers (persisting database volumes)..."
  docker compose down
  echo -e "${GREEN}✔ All containers stopped cleanly. Database data is preserved.${NC}"
  echo -e "To restart: ${YELLOW}./run.sh${NC}"
  echo -e "To wipe data: ${YELLOW}./stop.sh -v${NC}"
fi
