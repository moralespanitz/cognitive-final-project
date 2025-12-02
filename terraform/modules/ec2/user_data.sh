#!/bin/bash
set -e

# Logging
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "===== TaxiWatch EC2 Setup Started ====="
echo "Timestamp: $(date)"

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
systemctl start docker
systemctl enable docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install Git
echo "Installing Git..."
apt-get install -y git

# Clone repository
echo "Cloning repository..."
cd /home/ubuntu
sudo -u ubuntu git clone ${github_repo} app
cd app
sudo -u ubuntu git checkout ${github_branch}

# Create .env file for backend
echo "Creating environment variables..."
cat > /home/ubuntu/app/backend/.env <<EOF
DATABASE_URL=${database_url}
SECRET_KEY=${secret_key}
ENVIRONMENT=${environment}
DEBUG=False
S3_BUCKET_FRAMES=${s3_frames}
S3_BUCKET_VIDEOS=${s3_videos}
AWS_REGION=us-west-2
CORS_ORIGINS=["http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"]
EOF

# Create production docker-compose override
cat > /home/ubuntu/app/docker-compose.prod.yml <<EOF
version: '3.8'

services:
  backend:
    restart: always
    environment:
      - DATABASE_URL=${database_url}
      - SECRET_KEY=${secret_key}
      - ENVIRONMENT=${environment}
      - DEBUG=False
      - S3_BUCKET_FRAMES=${s3_frames}
      - S3_BUCKET_VIDEOS=${s3_videos}
      - AWS_REGION=us-west-2

  frontend:
    restart: always
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/api/v1

  # Remove local postgres and redis - use RDS
  postgres:
    profiles:
      - disabled

  redis:
    profiles:
      - disabled

  # Keep simulators for demo
  gps_simulator:
    restart: always
    environment:
      - DATABASE_URL=${database_url}

  camera_simulator:
    restart: always
    environment:
      - BACKEND_URL=http://backend:8000
EOF

# Set proper ownership
chown -R ubuntu:ubuntu /home/ubuntu/app

# Run database migrations
echo "Running database migrations..."
cd /home/ubuntu/app/backend
sudo -u ubuntu docker compose -f /home/ubuntu/app/docker-compose.yml -f /home/ubuntu/app/docker-compose.prod.yml run --rm backend alembic upgrade head || echo "Migration skipped or failed"

# Start application
echo "Starting application..."
cd /home/ubuntu/app
sudo -u ubuntu docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Setup systemd service for auto-restart
cat > /etc/systemd/system/taxiwatch.service <<EOF
[Unit]
Description=TaxiWatch Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/app
ExecStart=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable taxiwatch.service

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Health check
echo "Running health checks..."
curl -f http://localhost:8000/health || echo "Backend health check failed"
curl -f http://localhost:3000 || echo "Frontend health check failed"

echo "===== TaxiWatch EC2 Setup Completed ====="
echo "Timestamp: $(date)"
echo "Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
echo "Backend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "Backend Docs: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs"
