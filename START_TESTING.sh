#!/bin/bash

# TaxiWatch End-to-End Testing Startup Script
# This script sets up and starts all services for testing

set -e

echo "=================================="
echo "TaxiWatch E2E Testing Setup"
echo "=================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "\n${BLUE}[1/5] Checking Prerequisites...${NC}"
# Check Docker
if ! command -v docker &> /dev/null; then
  echo "❌ Docker is not installed"
  exit 1
fi
echo "✓ Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
  echo "❌ Docker Compose is not installed"
  exit 1
fi
echo "✓ Docker Compose found"

echo -e "\n${BLUE}[2/5] Starting Services...${NC}"
cd "$PROJECT_DIR"

# Start Docker containers
echo "Starting backend, database, and redis..."
docker-compose up -d
sleep 5

# Check if services are running
if docker-compose ps | grep -q "taxiwatch_backend"; then
  echo "✓ Backend started"
else
  echo "❌ Backend failed to start"
  docker-compose logs backend
  exit 1
fi

echo -e "\n${BLUE}[3/5] Seeding Test Data...${NC}"
echo "Populating database with test vehicles, users, devices, and FAQs..."
if docker-compose exec backend python -m app.scripts.seed_data 2>&1 | tail -5; then
  echo "✓ Test data seeded"
else
  echo "⚠️  Database may already have data (that's okay)"
fi

echo -e "\n${BLUE}[4/5] Starting Frontend...${NC}"
echo "Starting Next.js development server..."
echo "Frontend will be available at http://localhost:3000"
echo "Press Ctrl+C in this terminal to stop"
cd "$PROJECT_DIR/ui"
pnpm dev &
FRONTEND_PID=$!
sleep 5

echo -e "\n${BLUE}[5/5] Starting GPS Simulator...${NC}"
echo "Starting GPS location simulator for vehicles..."
cd "$PROJECT_DIR"
python3 hardware/gps_simulator.py &
SIMULATOR_PID=$!
sleep 2

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Available URLs:${NC}"
echo "  Frontend:    http://localhost:3000"
echo "  Backend:     http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Health:      http://localhost:8000/health"

echo -e "\n${YELLOW}Test Credentials:${NC}"
echo "  Username:    admin"
echo "  Password:    Admin123!"

echo -e "\n${YELLOW}What to Test:${NC}"
echo "  1. Login at http://localhost:3000"
echo "  2. Check Dashboard for live GPS updates"
echo "  3. Go to /map for full-screen fleet map"
echo "  4. Visit /vehicles to see vehicle list"
echo "  5. Test /admin/devices for device management"
echo "  6. Test /admin/faqs for FAQ management"
echo "  7. Try /chat for AI assistant"
echo "  8. Run ./scripts/e2e-test.sh in another terminal"

echo -e "\n${YELLOW}Documentation:${NC}"
echo "  Full testing guide:    E2E_TESTING_GUIDE.md"
echo "  Testing summary:       TESTING_SUMMARY.md"
echo "  Environment template:  .env.testing"
echo "  Automated tests:       ./scripts/e2e-test.sh"

echo -e "\n${BLUE}To stop all services:${NC}"
echo "  Press Ctrl+C in this terminal"
echo "  Then run: docker-compose down"

echo -e "\n${GREEN}System ready for testing! 🚀${NC}\n"

# Keep the script running
wait $FRONTEND_PID $SIMULATOR_PID 2>/dev/null || true

# Cleanup on exit
trap 'echo "Stopping services..."; kill $FRONTEND_PID $SIMULATOR_PID 2>/dev/null; docker-compose down' EXIT

wait
