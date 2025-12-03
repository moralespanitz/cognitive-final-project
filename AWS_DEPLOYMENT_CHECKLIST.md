# AWS Deployment Checklist - TaxiWatch

Use this checklist to track progress through manual AWS deployment.

## Pre-Deployment

- [ ] AWS CLI installed and configured: `aws configure`
- [ ] Verify credentials: `aws sts get-caller-identity`
- [ ] Have secure password for RDS ready
- [ ] Have random SECRET_KEY ready (min 32 chars)
- [ ] Git repository cloned locally for reference

## Phase 1: Permission Verification

- [ ] Check if can create Security Groups
- [ ] Check if can create S3 buckets
- [ ] Check if can create RDS instances
- [ ] Check if can create EC2 instances
- [ ] Check if can create IAM users/policies

**If any fail:** Document which resources cannot be created, may need to use AWS Console

## Phase 2: S3 Setup

### Frames Bucket
- [ ] Create S3 bucket for video frames
- [ ] Save bucket name: `__________________`
- [ ] Enable versioning
- [ ] Configure CORS rules
- [ ] Save endpoint: `__________________`

### Archive Bucket
- [ ] Create S3 bucket for video archive
- [ ] Save bucket name: `__________________`
- [ ] Enable lifecycle rules (30-day expiration)
- [ ] Save endpoint: `__________________`

### IAM User for Application
- [ ] Create IAM user: `taxiwatch-app`
- [ ] Create access key
- [ ] Save AccessKeyId: `__________________`
- [ ] Save SecretAccessKey: `__________________` (⚠️ Save securely!)
- [ ] Attach S3 policy for bucket access

## Phase 3: RDS PostgreSQL

### Pre-Setup
- [ ] Identify VPC ID: `__________________`
- [ ] Identify subnet IDs: `__________________`, `__________________`
- [ ] RDS password decided: `__________________`

### DB Subnet Group
- [ ] Create DB subnet group
- [ ] Name: `__________________`

### RDS Security Group
- [ ] Create security group for RDS
- [ ] SG ID: `__________________`
- [ ] Port 5432 configured

### RDS Instance
- [ ] Create RDS instance (db.t3.micro PostgreSQL)
- [ ] Instance ID: `__________________`
- [ ] Wait for "available" status (5-10 min)
- [ ] Get RDS endpoint: `__________________`
- [ ] Test connection from local machine

### Connection String
- [ ] DATABASE_URL formatted:
```
postgresql+asyncpg://postgres:PASSWORD@ENDPOINT:5432/taxiwatch
```
- [ ] Save securely

## Phase 4: EC2 Security Group

- [ ] Create security group for EC2
- [ ] SG ID: `__________________`
- [ ] SSH (22): Open from 0.0.0.0/0
- [ ] Backend API (8000): Open from 0.0.0.0/0
- [ ] Frontend (3000): Open from 0.0.0.0/0
- [ ] HTTP (80): Open from 0.0.0.0/0
- [ ] HTTPS (443): Open from 0.0.0.0/0

## Phase 5: EC2 Key Pair

- [ ] Create key pair: `taxiwatch-prod-key`
- [ ] Download and save: `taxiwatch-prod-key.pem`
- [ ] Set permissions: `chmod 400 taxiwatch-prod-key.pem`
- [ ] Verify file exists: `ls -la taxiwatch-prod-key.pem`

## Phase 6: EC2 Instance

- [ ] Launch EC2 instance (t3.small, Ubuntu 22)
- [ ] Instance ID: `__________________`
- [ ] Wait for "running" status
- [ ] Public IP: `__________________`

## Phase 7: Elastic IP

- [ ] Allocate Elastic IP
- [ ] Allocation ID: `__________________`
- [ ] Associate with EC2 instance
- [ ] Elastic IP (permanent): `__________________`

## Phase 8: Application Deployment

### Connect to EC2
- [ ] SSH connection successful: `ssh -i taxiwatch-prod-key.pem ubuntu@ELASTIC_IP`
- [ ] Ubuntu prompt visible

### Install Docker
- [ ] System updated: `sudo apt-get update`
- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker-compose --version`
- [ ] User added to docker group

### Clone Repository
- [ ] Repository cloned: `cd ~/cognitive-final-project`
- [ ] Master branch checked out
- [ ] Code verified

### Environment Configuration
- [ ] `.env` file created with:
  - [ ] DATABASE_URL (RDS endpoint)
  - [ ] SECRET_KEY (random)
  - [ ] AWS_ACCESS_KEY_ID
  - [ ] AWS_SECRET_ACCESS_KEY
  - [ ] AWS_S3_FRAMES_BUCKET
  - [ ] AWS_S3_ARCHIVE_BUCKET

### Docker Compose Configuration
- [ ] `docker-compose.yml` created/updated
- [ ] PostgreSQL service configured
- [ ] Redis service configured
- [ ] Backend service configured
- [ ] Frontend service configured
- [ ] NEXT_PUBLIC_API_URL set to EC2 Elastic IP

### Database Setup
- [ ] Services started: `docker-compose up -d`
- [ ] Migrations run: `docker-compose exec backend uv run alembic upgrade head`
- [ ] All services running: `docker-compose ps`

### Systemd Service
- [ ] Service file created: `/etc/systemd/system/taxiwatch.service`
- [ ] Service enabled: `sudo systemctl enable taxiwatch`
- [ ] Service started: `sudo systemctl start taxiwatch`
- [ ] Service status verified

## Phase 9: Verification Testing

### Backend Health
- [ ] Health check endpoint: `curl http://ELASTIC_IP:8000/health`
- [ ] Returns 200 OK with healthy response

### API Documentation
- [ ] Swagger UI accessible: `http://ELASTIC_IP:8000/docs`
- [ ] All endpoints visible
- [ ] Can expand endpoint schemas

### Frontend
- [ ] Next.js homepage loads: `http://ELASTIC_IP:3000`
- [ ] No 5XX errors in browser console
- [ ] Can navigate between pages

### Admin Interface
- [ ] Admin accessible: `http://ELASTIC_IP:8000/admin`
- [ ] Can login with admin/Admin123!
- [ ] All 8 model views visible (User, Driver, Vehicle, Trip, etc.)
- [ ] Can view/create/edit records

### Video Streaming
- [ ] Run ESP32 mock: `python app/scripts/esp32_mock.py --url "http://ELASTIC_IP:8000/api/v1/video/device/upload"`
- [ ] Frames received in backend logs
- [ ] Can see frames in admin → Trip Images
- [ ] WebSocket endpoint responding at: `ws://ELASTIC_IP:8000/ws/video/route-1`

## Phase 10: Production Readiness

### Monitoring
- [ ] CloudWatch logs accessible
- [ ] Set up billing alerts (optional)
- [ ] Review security group rules

### Backup & Recovery
- [ ] RDS backup retention: 7 days
- [ ] S3 versioning enabled
- [ ] Database credentials stored securely
- [ ] SSH key backed up securely

### Documentation
- [ ] Saved all AWS resource IDs
- [ ] Saved all credentials securely
- [ ] Documented access procedures
- [ ] Shared deployment guide with team

## Rollback Procedure (if needed)

To remove all AWS resources:

```bash
# Stop services
docker-compose down

# Terminate EC2
aws ec2 terminate-instances --instance-ids INSTANCE_ID

# Release Elastic IP
aws ec2 release-address --allocation-id ALLOCATION_ID

# Delete RDS
aws rds delete-db-instance --db-instance-identifier taxiwatch-prod-db --skip-final-snapshot

# Delete security groups
aws ec2 delete-security-group --group-id EC2_SG_ID
aws ec2 delete-security-group --group-id RDS_SG_ID

# Delete S3 buckets
aws s3 rb s3://taxiwatch-frames-* --force
aws s3 rb s3://taxiwatch-archive-* --force

# Delete IAM user
aws iam delete-user-policy --user-name taxiwatch-app --policy-name TaxiWatchS3Access
aws iam delete-access-key --user-name taxiwatch-app --access-key-id ACCESS_KEY_ID
aws iam delete-user --user-name taxiwatch-app
```

---

## Quick Reference: Important Endpoints

After deployment, access your application at:

| Component | URL |
|-----------|-----|
| Frontend | `http://ELASTIC_IP:3000` |
| Backend API | `http://ELASTIC_IP:8000` |
| API Docs | `http://ELASTIC_IP:8000/docs` |
| Admin Panel | `http://ELASTIC_IP:8000/admin` |
| WebSocket Video | `ws://ELASTIC_IP:8000/ws/video/{route_id}` |

## Credentials to Save

**Keep these secure in a password manager:**

- [ ] AWS Account ID: `__________________`
- [ ] RDS Master Password: `__________________`
- [ ] RDS Endpoint: `__________________`
- [ ] IAM User Access Key: `__________________`
- [ ] IAM User Secret Key: `__________________`
- [ ] EC2 SSH Key Pair: `taxiwatch-prod-key.pem` (stored locally)
- [ ] Elastic IP: `__________________`
- [ ] S3 Frames Bucket: `__________________`
- [ ] S3 Archive Bucket: `__________________`
- [ ] Django Secret Key: `__________________`

---

**Status:** Ready for Phase 1 execution

**Last Updated:** [Date]
