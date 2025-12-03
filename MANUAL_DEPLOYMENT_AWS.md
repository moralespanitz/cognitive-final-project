# Manual AWS Deployment Guide for TaxiWatch

This guide covers manual deployment to AWS Academy environment when Terraform is blocked by IAM restrictions.

## Prerequisites

1. **AWS CLI** configured with AWS Academy credentials:
   ```bash
   aws configure
   # Enter credentials when prompted
   # Region: us-west-2
   # Output format: json
   ```

2. **Verify credentials work:**
   ```bash
   aws sts get-caller-identity
   # Should return: Account ID, ARN, UserId
   ```

3. **Local tools installed:**
   - SSH client
   - Git
   - Docker (or plan to install on EC2)

## Phase 1: Check Available Resources & Permissions

### 1.1 Identify Existing VPC and Subnets

```bash
# List VPCs
aws ec2 describe-vpcs --region us-west-2

# List subnets in default VPC
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=<VPC-ID>" \
  --region us-west-2
```

**Expected output:** Default VPC (vpc-xxxxx) with at least one subnet in us-west-2

### 1.2 Test Permission Scope

```bash
# Check if you can create Security Groups
aws ec2 create-security-group \
  --group-name test-taxiwatch-sg \
  --description "Test security group" \
  --vpc-id <VPC-ID> \
  --region us-west-2

# If successful, delete it:
aws ec2 delete-security-group \
  --group-id <SG-ID> \
  --region us-west-2

# Check if you can create S3 buckets
aws s3api create-bucket \
  --bucket taxiwatch-test-bucket-$(date +%s) \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

# If successful, delete it:
aws s3 rb s3://taxiwatch-test-bucket-xxxxx
```

**If any of these fail:** Contact AWS Academy support - manual workaround below

---

## Phase 2: Create S3 Buckets (AWS CLI)

### 2.1 Create Video Frames Bucket

```bash
# Create bucket
aws s3api create-bucket \
  --bucket taxiwatch-frames-$(date +%s | tail -c 6) \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

# Store bucket name in variable for later use
export S3_FRAMES_BUCKET="taxiwatch-frames-XXXXX"

# Enable versioning (optional, for backup)
aws s3api put-bucket-versioning \
  --bucket $S3_FRAMES_BUCKET \
  --versioning-configuration Status=Enabled

# Set CORS for web access (required for frontend video display)
cat > /tmp/cors.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExpireHeader": 3000,
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

aws s3api put-bucket-cors \
  --bucket $S3_FRAMES_BUCKET \
  --cors-configuration file:///tmp/cors.json
```

### 2.2 Create Video Archive Bucket

```bash
# Create archive bucket
aws s3api create-bucket \
  --bucket taxiwatch-archive-$(date +%s | tail -c 6) \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

export S3_ARCHIVE_BUCKET="taxiwatch-archive-XXXXX"

# Enable lifecycle rule (delete old videos after 30 days to save costs)
cat > /tmp/lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "Id": "DeleteOldVideos",
      "Status": "Enabled",
      "ExpirationInDays": 30,
      "NoncurrentVersionExpirationInDays": 7
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket $S3_ARCHIVE_BUCKET \
  --lifecycle-configuration file:///tmp/lifecycle.json
```

### 2.3 Create IAM User for Application Access

```bash
# Create IAM user for EC2 application
aws iam create-user --user-name taxiwatch-app

# Create access key for EC2 to assume
aws iam create-access-key --user-name taxiwatch-app

# Save the AccessKeyId and SecretAccessKey output!
# You'll need these in EC2 environment variables
```

### 2.4 Attach S3 Permissions to IAM User

```bash
cat > /tmp/s3-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::taxiwatch-frames-*/*",
        "arn:aws:s3:::taxiwatch-archive-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::taxiwatch-frames-*",
        "arn:aws:s3:::taxiwatch-archive-*"
      ]
    }
  ]
}
EOF

aws iam put-user-policy \
  --user-name taxiwatch-app \
  --policy-name TaxiWatchS3Access \
  --policy-document file:///tmp/s3-policy.json
```

---

## Phase 3: Create RDS PostgreSQL Database (AWS CLI)

### 3.1 Create DB Subnet Group

```bash
# First, get all subnet IDs in your VPC
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=<VPC-ID>" \
  --region us-west-2 \
  --query 'Subnets[*].[SubnetId, AvailabilityZone]' \
  --output table
```

```bash
# Create subnet group (replace with actual subnet IDs)
aws rds create-db-subnet-group \
  --db-subnet-group-name taxiwatch-db-subnet \
  --db-subnet-group-description "Subnet group for TaxiWatch RDS" \
  --subnet-ids subnet-xxxxx subnet-yyyyy \
  --region us-west-2
```

### 3.2 Create Security Group for RDS

```bash
# Create security group for RDS (accept PostgreSQL on port 5432)
RDS_SG_ID=$(aws ec2 create-security-group \
  --group-name taxiwatch-rds-sg \
  --description "Security group for TaxiWatch RDS" \
  --vpc-id <VPC-ID> \
  --region us-west-2 \
  --query 'GroupId' \
  --output text)

echo "RDS Security Group ID: $RDS_SG_ID"

# Add ingress rule for PostgreSQL (from EC2 security group)
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group <EC2-SG-ID> \
  --region us-west-2
```

### 3.3 Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier taxiwatch-prod-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.5 \
  --master-username postgres \
  --master-user-password "YourSecurePassword123!" \
  --allocated-storage 20 \
  --storage-type gp3 \
  --db-subnet-group-name taxiwatch-db-subnet \
  --vpc-security-group-ids $RDS_SG_ID \
  --publicly-accessible false \
  --backup-retention-period 7 \
  --multi-az false \
  --region us-west-2
```

**Wait 5-10 minutes for database to be available:**

```bash
# Check status (repeat until Status is "available")
aws rds describe-db-instances \
  --db-instance-identifier taxiwatch-prod-db \
  --region us-west-2 \
  --query 'DBInstances[0].[DBInstanceStatus, Endpoint.Address, Endpoint.Port]'
```

### 3.4 Get RDS Endpoint

```bash
# Save endpoint for later use in EC2
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier taxiwatch-prod-db \
  --region us-west-2 \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"

# Full connection string (save for EC2 environment)
DATABASE_URL="postgresql+asyncpg://postgres:YourSecurePassword123!@$RDS_ENDPOINT:5432/taxiwatch"
echo "DATABASE_URL=$DATABASE_URL"
```

---

## Phase 4: Create EC2 Security Group

```bash
# Create security group
EC2_SG_ID=$(aws ec2 create-security-group \
  --group-name taxiwatch-app-sg \
  --description "Security group for TaxiWatch EC2" \
  --vpc-id <VPC-ID> \
  --region us-west-2 \
  --query 'GroupId' \
  --output text)

echo "EC2 Security Group ID: $EC2_SG_ID"

# SSH access
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region us-west-2

# Frontend (Next.js)
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 3000 \
  --cidr 0.0.0.0/0 \
  --region us-west-2

# Backend API
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0 \
  --region us-west-2

# HTTP (optional, for Nginx if added later)
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region us-west-2

# HTTPS (optional)
aws ec2 authorize-security-group-ingress \
  --group-id $EC2_SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0 \
  --region us-west-2
```

---

## Phase 5: Create EC2 Key Pair

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name taxiwatch-prod-key \
  --region us-west-2 \
  --query 'KeyMaterial' \
  --output text > taxiwatch-prod-key.pem

# Secure the key
chmod 400 taxiwatch-prod-key.pem

# Verify
ls -la taxiwatch-prod-key.pem
```

---

## Phase 6: Create EC2 Instance

```bash
# Get default subnet (or specify your preferred one)
SUBNET_ID=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=<VPC-ID>" \
  --region us-west-2 \
  --query 'Subnets[0].SubnetId' \
  --output text)

echo "Using subnet: $SUBNET_ID"

# Launch EC2 instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id ami-047f8ab1a8e4de3659 \
  --instance-type t3.small \
  --key-name taxiwatch-prod-key \
  --security-group-ids $EC2_SG_ID \
  --subnet-id $SUBNET_ID \
  --region us-west-2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=taxiwatch-prod},{Key=Environment,Value=prod}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "EC2 Instance created: $INSTANCE_ID"

# Wait for instance to be running
aws ec2 wait instance-running \
  --instance-ids $INSTANCE_ID \
  --region us-west-2

# Get public IP
EC2_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region us-west-2 \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "EC2 Public IP: $EC2_IP"
```

---

## Phase 7: Allocate Elastic IP

```bash
# Allocate Elastic IP
ALLOCATION_ID=$(aws ec2 allocate-address \
  --domain vpc \
  --region us-west-2 \
  --query 'AllocationId' \
  --output text)

echo "Allocation ID: $ALLOCATION_ID"

# Associate with EC2 instance
aws ec2 associate-address \
  --instance-id $INSTANCE_ID \
  --allocation-id $ALLOCATION_ID \
  --region us-west-2

# Get the Elastic IP
ELASTIC_IP=$(aws ec2 describe-addresses \
  --allocation-ids $ALLOCATION_ID \
  --region us-west-2 \
  --query 'Addresses[0].PublicIp' \
  --output text)

echo "Elastic IP assigned: $ELASTIC_IP"
```

---

## Phase 8: Deploy Application to EC2

### 8.1 Connect to EC2

```bash
ssh -i taxiwatch-prod-key.pem ubuntu@$ELASTIC_IP

# Verify you're connected (you should see ubuntu@ip-xxxxx prompt)
```

### 8.2 Install Docker and Docker Compose

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and back in for docker group permissions
exit
ssh -i taxiwatch-prod-key.pem ubuntu@$ELASTIC_IP
```

### 8.3 Clone Repository

```bash
# Clone TaxiWatch repository
git clone https://github.com/moralespanitz/cognitive-final-project.git
cd cognitive-final-project

# Switch to master branch (if needed)
git checkout master
```

### 8.4 Create Environment Files

**Backend environment (.env file in root or terraform-ec2-deploy/):**

```bash
cat > .env << 'EOF'
# FastAPI Configuration
DEBUG=false
SECRET_KEY="your-random-secret-key-32-chars-minimum-change-this-please"

# Database
DATABASE_URL="postgresql+asyncpg://postgres:YourSecurePassword123!@RDS_ENDPOINT:5432/taxiwatch"

# Redis (using Docker Compose internal Redis)
REDIS_URL="redis://redis:6379/0"

# JWT
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# AWS (if using S3 for video storage)
AWS_ACCESS_KEY_ID="YOUR_IAM_USER_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY="YOUR_IAM_USER_SECRET_KEY"
AWS_S3_REGION="us-west-2"
AWS_S3_FRAMES_BUCKET="taxiwatch-frames-XXXXX"
AWS_S3_ARCHIVE_BUCKET="taxiwatch-archive-XXXXX"

# OpenAI (optional for future AI features)
OPENAI_API_KEY=""
EOF
```

### 8.5 Update docker-compose.yml

Create/update `docker-compose.yml` in the root directory:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: taxiwatch-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: YourSecurePassword123!
      POSTGRES_DB: taxiwatch
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: taxiwatch-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: taxiwatch-backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:YourSecurePassword123!@postgres:5432/taxiwatch
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=false
      - SECRET_KEY=your-random-secret-key-32-chars-minimum-change-this-please
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_S3_REGION=us-west-2
      - AWS_S3_FRAMES_BUCKET=${AWS_S3_FRAMES_BUCKET}
      - AWS_S3_ARCHIVE_BUCKET=${AWS_S3_ARCHIVE_BUCKET}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./ui
      dockerfile: Dockerfile
    container_name: taxiwatch-frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://${ELASTIC_IP}:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./ui:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
    driver: local

networks:
  default:
    name: taxiwatch-network
```

### 8.6 Run Migrations

```bash
# Wait for PostgreSQL to be ready, then run migrations
docker-compose exec backend uv run alembic upgrade head
```

### 8.7 Start Application

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 8.8 Set Up Auto-restart on Reboot

Create a systemd service:

```bash
sudo cat > /etc/systemd/system/taxiwatch.service << 'EOF'
[Unit]
Description=TaxiWatch Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/cognitive-final-project
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable taxiwatch
sudo systemctl start taxiwatch

# Check status
sudo systemctl status taxiwatch
```

---

## Phase 9: Verify Deployment

### 9.1 Test Backend

```bash
# From your local machine
curl http://$ELASTIC_IP:8000/health

# Should return: {"status":"ok"} or similar
```

### 9.2 Test API Documentation

```
Open in browser: http://$ELASTIC_IP:8000/docs
```

### 9.3 Test Frontend

```
Open in browser: http://$ELASTIC_IP:3000
```

### 9.4 Test Admin Interface

```
Open in browser: http://$ELASTIC_IP:8000/admin
# Login with admin/Admin123!
```

### 9.5 Test Video Streaming

```bash
# From your local machine, run the ESP32 mock simulator
cd backend
python app/scripts/esp32_mock.py --url "http://$ELASTIC_IP:8000/api/v1/video/device/upload"
```

---

## Phase 10: Troubleshooting

### Issue: Cannot connect to RDS from EC2

**Solution:**
```bash
# Verify security group rules
aws ec2 describe-security-groups \
  --group-ids $RDS_SG_ID \
  --region us-west-2

# Should show ingress rule for port 5432 from EC2 security group
```

### Issue: EC2 containers cannot access RDS

**Solution - Use RDS internal hostname:**
In docker-compose.yml, use the actual RDS endpoint (not localhost):
```yaml
DATABASE_URL=postgresql+asyncpg://postgres:password@YOUR_RDS_ENDPOINT:5432/taxiwatch
```

### Issue: Cannot reach frontend/backend from internet

**Solution:**
1. Verify security group allows inbound on ports 3000 and 8000
2. Verify Elastic IP is associated with EC2 instance
3. Check service logs: `docker-compose logs backend`

### Issue: High AWS costs

**Solution:**
- Stop services when not using: `docker-compose stop`
- Delete RDS backups if not needed: `aws rds delete-db-snapshot`
- Use S3 lifecycle rules to delete old video archives (already configured)

---

## Cost Estimate

- **EC2 t3.small**: ~$15/month (running 24/7)
- **RDS db.t3.micro**: FREE (first year AWS free tier), then ~$15/month
- **S3 storage**: ~$1-3/month (100GB video data)
- **Elastic IP**: FREE (while attached)
- **Data transfer**: ~$5/month
- **Total**: ~$20-25/month (or ~$5/month with free tier)

---

## Summary of AWS Resources Created

| Resource | Name | Details |
|----------|------|---------|
| S3 Bucket | taxiwatch-frames-* | Video frame storage with CORS enabled |
| S3 Bucket | taxiwatch-archive-* | Video archive with 30-day lifecycle |
| IAM User | taxiwatch-app | Application credentials for S3 access |
| RDS Instance | taxiwatch-prod-db | PostgreSQL 15, db.t3.micro |
| Security Group | taxiwatch-rds-sg | PostgreSQL port 5432 access |
| Security Group | taxiwatch-app-sg | Ports 22, 80, 443, 3000, 8000 |
| EC2 Instance | taxiwatch-prod | Ubuntu 22, t3.small |
| Key Pair | taxiwatch-prod-key | SSH access credentials |
| Elastic IP | (auto-assigned) | Static public IP for EC2 |

---

## Next Steps

1. Execute Phase 1 to verify permissions
2. Proceed through phases sequentially
3. Test each phase before moving to next
4. Save all outputs (IPs, endpoints, credentials) in a secure location
5. Monitor costs and set billing alerts

**Estimated deployment time:** 30-45 minutes (after AWS resource provisioning)
