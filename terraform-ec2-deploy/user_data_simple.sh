#!/bin/bash
set -e

exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "===== TaxiWatch EC2 Setup Started ====="
echo "Timestamp: $(date)"

# Update system
apt-get update -qq
apt-get upgrade -y -qq

# Install Docker
apt-get install -y -qq ca-certificates curl gnupg lsb-release
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Install Git
apt-get install -y -qq git

# Clone repository
cd /home/ubuntu
sudo -u ubuntu git clone ${github_repo} app
cd app
sudo -u ubuntu git checkout ${github_branch}

# Create .env for backend (using Docker PostgreSQL)
cat > /home/ubuntu/app/backend/.env <<'ENVEOF'
DATABASE_URL=${database_url}
SECRET_KEY=${secret_key}
ENVIRONMENT=production
DEBUG=False
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=["http://localhost:3000"]
AWS_REGION=us-west-2
OPENAI_API_KEY=sk-placeholder
EOF

# Create docker-compose override for production
cat > /home/ubuntu/app/docker-compose.prod.yml <<'COMPOSEEOF'
version: '3.8'

services:
  backend:
    restart: always
    environment:
      - DEBUG=False
      - ENVIRONMENT=production

  frontend:
    restart: always
    environment:
      - NODE_ENV=production

  gps_simulator:
    restart: always

  camera_simulator:
    restart: always

COMPOSEEOF

chown -R ubuntu:ubuntu /home/ubuntu/app

# Start services
echo "Starting Docker services..."
cd /home/ubuntu/app

# Pull images first
docker compose pull 2>/dev/null || true

# Start containers
sudo -u ubuntu docker compose up -d

# Wait for services
echo "Waiting for services to start..."
sleep 30

# Health checks
echo "Running health checks..."
curl -f http://localhost:8000/health 2>/dev/null || echo "Backend not ready yet"
curl -f http://localhost:3000 2>/dev/null || echo "Frontend not ready yet"

# Setup systemd service
cat > /etc/systemd/system/taxiwatch.service <<'SERVICEEOF'
[Unit]
Description=TaxiWatch Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/app
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable taxiwatch.service

echo "===== TaxiWatch EC2 Setup Completed ====="
echo "Timestamp: $(date)"
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Access your application:"
echo "  Frontend: http://$EC2_IP:3000"
echo "  Backend:  http://$EC2_IP:8000"
echo "  API Docs: http://$EC2_IP:8000/docs"
