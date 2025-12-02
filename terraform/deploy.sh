#!/bin/bash
set -e

echo "======================================"
echo "TaxiWatch AWS EC2 Deployment Script"
echo "======================================"
echo ""

# Colors
RED='\033[0[31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Install it first:${NC}"
    echo "   brew install terraform"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not configured. Run: aws configure${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Backup Lambda files
echo "📦 Backing up Lambda configuration files..."
if [ -f "main.tf" ] && grep -q "module \"lambda\"" main.tf; then
    mv main.tf main-lambda.tf.bak 2>/dev/null || true
    mv variables.tf variables-lambda.tf.bak 2>/dev/null || true
    mv outputs.tf outputs-lambda.tf.bak 2>/dev/null || true
    echo -e "${YELLOW}   Backed up Lambda configs${NC}"
fi

# Use EC2 configuration
echo "🔧 Setting up EC2 configuration..."
if [ -f "main-ec2.tf" ]; then
    cp main-ec2.tf main.tf
    cp variables-ec2.tf variables.tf
    cp outputs-ec2.tf outputs.tf
    echo -e "${GREEN}   EC2 configuration activated${NC}"
fi

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${RED}❌ terraform.tfvars not found${NC}"
    echo "   Create it from terraform.tfvars.example"
    echo "   cp terraform.tfvars.example terraform.tfvars"
    echo "   Then edit terraform.tfvars with your values"
    exit 1
fi

# Check if sensitive values are set
if grep -q "CHANGE_ME" terraform.tfvars; then
    echo -e "${RED}❌ Please update terraform.tfvars with real values${NC}"
    echo "   - db_password: Generate a strong password"
    echo "   - secret_key: Run: openssl rand -hex 32"
    exit 1
fi

echo ""
echo "🚀 Starting Terraform deployment..."
echo ""

# Initialize Terraform
echo "1️⃣  Initializing Terraform..."
terraform init

# Validate configuration
echo ""
echo "2️⃣  Validating configuration..."
terraform validate

# Plan
echo ""
echo "3️⃣  Creating execution plan..."
terraform plan -out=tfplan

# Confirm
echo ""
echo -e "${YELLOW}⚠️  Review the plan above. This will create:${NC}"
echo "   - VPC and subnets"
echo "   - RDS PostgreSQL database"
echo "   - S3 buckets"
echo "   - EC2 instance"
echo "   - Security groups"
echo "   - Elastic IP"
echo ""
read -p "Do you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    rm -f tfplan
    exit 0
fi

# Apply
echo ""
echo "4️⃣  Applying changes..."
terraform apply tfplan

# Clean up plan file
rm -f tfplan

echo ""
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""

# Show outputs
echo "📋 Deployment Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
terraform output -json | jq -r '
  "Frontend URL:     \(.frontend_url.value)",
  "Backend URL:      \(.backend_url.value)",
  "Backend Docs:     \(.backend_docs_url.value)",
  "SSH Command:      \(.ssh_command.value)",
  "",
  "RDS Endpoint:     \(.rds_endpoint.value)",
  "S3 Frames Bucket: \(.s3_frames_bucket.value)",
  "S3 Videos Bucket: \(.s3_videos_bucket.value)"
'
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get EC2 IP
EC2_IP=$(terraform output -raw ec2_public_ip)

echo -e "${YELLOW}⏳ EC2 is initializing (5-10 minutes)...${NC}"
echo ""
echo "Monitor progress:"
echo "  1. SSH to EC2: ssh -i taxiwatch-prod-key.pem ubuntu@$EC2_IP"
echo "  2. View logs: sudo tail -f /var/log/user-data.log"
echo ""
echo "When ready, access your application:"
echo "  • Frontend: http://$EC2_IP:3000"
echo "  • Backend:  http://$EC2_IP:8000"
echo "  • API Docs: http://$EC2_IP:8000/docs"
echo ""
echo -e "${GREEN}🎉 Deployment script finished!${NC}"
