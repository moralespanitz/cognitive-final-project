#!/bin/bash

# Script to deploy admin_logs migration to production EC2 server
# Usage: ./deploy_migration.sh [path_to_ssh_key]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Server configuration
SERVER_IP="98.92.214.232"
SSH_USER="ubuntu"
SSH_KEY="${1:-taxiwatch-prod-key.pem}"
PROJECT_PATH="/home/ubuntu/cognitive-final-project"

echo -e "${GREEN}=== TaxiWatch Migration Deployment ===${NC}"
echo ""
echo "Target server: $SERVER_IP"
echo "SSH key: $SSH_KEY"
echo ""

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found at $SSH_KEY${NC}"
    echo "Usage: ./deploy_migration.sh [path_to_ssh_key]"
    echo "Example: ./deploy_migration.sh ~/Downloads/taxiwatch-prod-key.pem"
    exit 1
fi

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SSH_USER@$SERVER_IP" "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to server${NC}"
    echo "Please check:"
    echo "  1. SSH key permissions (should be 400): chmod 400 $SSH_KEY"
    echo "  2. Server is running"
    echo "  3. Security group allows SSH from your IP"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}"
echo ""

# Copy migration file to server
echo -e "${YELLOW}Copying migration file to server...${NC}"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/alembic/versions/001_add_admin_logs.py \
    "$SSH_USER@$SERVER_IP:$PROJECT_PATH/backend/alembic/versions/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migration file copied${NC}"
else
    echo -e "${RED}✗ Failed to copy migration file${NC}"
    exit 1
fi
echo ""

# Copy updated models
echo -e "${YELLOW}Copying updated models to server...${NC}"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/app/models/admin_log.py \
    "$SSH_USER@$SERVER_IP:$PROJECT_PATH/backend/app/models/"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/app/models/__init__.py \
    "$SSH_USER@$SERVER_IP:$PROJECT_PATH/backend/app/models/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Models copied${NC}"
else
    echo -e "${RED}✗ Failed to copy models${NC}"
    exit 1
fi
echo ""

# Copy schemas
echo -e "${YELLOW}Copying schemas to server...${NC}"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/app/schemas/admin.py \
    "$SSH_USER@$SERVER_IP:$PROJECT_PATH/backend/app/schemas/"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/app/schemas/__init__.py \
    "$SSH_USER@$SERVER_IP:$PROJECT_PATH/backend/app/schemas/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Schemas copied${NC}"
else
    echo -e "${RED}✗ Failed to copy schemas${NC}"
    exit 1
fi
echo ""

# Copy admin endpoint
echo -e "${YELLOW}Copying admin endpoint to server...${NC}"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/app/api/v1/admin.py \
    "$SSH_USER@$SERVER_IP:$PROJECT_PATH/backend/app/api/v1/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Admin endpoint copied${NC}"
else
    echo -e "${RED}✗ Failed to copy admin endpoint${NC}"
    exit 1
fi
echo ""

# Copy middleware
echo -e "${YELLOW}Copying middleware to server...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$SERVER_IP" \
    "mkdir -p $PROJECT_PATH/backend/app/middleware"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/app/middleware/__init__.py \
    backend/app/middleware/audit.py \
    "$SSH_USER@$SERVER_IP:$PROJECT_PATH/backend/app/middleware/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Middleware copied${NC}"
else
    echo -e "${RED}✗ Failed to copy middleware${NC}"
    exit 1
fi
echo ""

# Copy updated main.py
echo -e "${YELLOW}Copying updated main.py to server...${NC}"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/app/main.py \
    "$SSH_USER@$SERVER_IP:$PROJECT_PATH/backend/app/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ main.py copied${NC}"
else
    echo -e "${RED}✗ Failed to copy main.py${NC}"
    exit 1
fi
echo ""

# Run migration on server
echo -e "${YELLOW}Running migration on server...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SSH_USER@$SERVER_IP" << 'ENDSSH'
    cd /home/ubuntu/cognitive-final-project

    echo "Current directory: $(pwd)"
    echo ""

    echo "Checking migration file..."
    if [ -f "backend/alembic/versions/001_add_admin_logs.py" ]; then
        echo "✓ Migration file exists"
    else
        echo "✗ Migration file not found"
        exit 1
    fi
    echo ""

    echo "Running Alembic migration..."
    docker-compose exec -T backend uv run alembic upgrade head

    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Migration completed successfully"
    else
        echo ""
        echo "✗ Migration failed"
        exit 1
    fi
    echo ""

    echo "Restarting backend container..."
    docker-compose restart backend

    echo ""
    echo "Waiting for backend to be ready..."
    sleep 5

    echo "Checking backend health..."
    curl -f http://localhost:8000/health
    echo ""
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=== Deployment Successful! ===${NC}"
    echo ""
    echo "New endpoints available:"
    echo "  • GET  http://$SERVER_IP:8000/api/v1/admin/logs"
    echo "  • GET  http://$SERVER_IP:8000/api/v1/admin/stats"
    echo "  • GET  http://$SERVER_IP:8000/api/v1/admin/stats/revenue"
    echo "  • GET  http://$SERVER_IP:8000/api/v1/admin/stats/quick"
    echo ""
    echo "Test the new endpoints:"
    echo "  curl -H 'Authorization: Bearer YOUR_ADMIN_TOKEN' http://$SERVER_IP:8000/api/v1/admin/stats/quick"
    echo ""
else
    echo ""
    echo -e "${RED}=== Deployment Failed ===${NC}"
    echo "Check the errors above and try again"
    exit 1
fi
