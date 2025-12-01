# Arquitectura AWS - TaxiWatch

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE USUARIOS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐          │
│  │   Cliente    │        │    Admin     │        │   ESP32      │          │
│  │   Web App    │        │   Web App    │        │   Camera     │          │
│  └──────┬───────┘        └──────┬───────┘        └──────┬───────┘          │
│         │                       │                       │                   │
└─────────┼───────────────────────┼───────────────────────┼───────────────────┘
          │                       │                       │
          │                       │                       │
┌─────────┼───────────────────────┼───────────────────────┼───────────────────┐
│         │              CAPA DE ENTRADA (AWS)            │                   │
├─────────┼───────────────────────┼───────────────────────┼───────────────────┤
│         ▼                       ▼                       ▼                   │
│  ┌──────────────────────────────────────────────────────────────┐          │
│  │                     Route 53 (DNS)                            │          │
│  │              taxiwatch.com / api.taxiwatch.com                │          │
│  └────────────────┬─────────────────────┬─────────────────┬─────┘          │
│                   │                     │                 │                 │
│  ┌────────────────▼─────────┐  ┌────────▼──────────┐  ┌──▼──────────────┐ │
│  │   CloudFront CDN         │  │  Application      │  │  API Gateway    │ │
│  │   (Frontend Static)      │  │  Load Balancer    │  │  (REST API)     │ │
│  │   - Next.js build        │  │  (ALB)            │  │  - Throttling   │ │
│  │   - Images, CSS, JS      │  │  - SSL/TLS        │  │  - Auth         │ │
│  └──────────────────────────┘  │  - Health checks  │  └──┬──────────────┘ │
│                                 └────────┬──────────┘     │                │
└─────────────────────────────────────────┼────────────────┼────────────────┘
                                          │                │
                                          │                │
┌─────────────────────────────────────────┼────────────────┼────────────────┐
│                    CAPA DE APLICACIÓN                    │                │
├─────────────────────────────────────────┼────────────────┼────────────────┤
│                                         ▼                ▼                │
│  ┌───────────────────────────────────────────────────────────────┐       │
│  │                    ECS Fargate Cluster                         │       │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐│       │
│  │  │  Django API      │  │  Django API      │  │  Django API  ││       │
│  │  │  Task (Auto-     │  │  Task (Auto-     │  │  Task        ││       │
│  │  │  Scaling 2-10)   │  │  Scaling 2-10)   │  │              ││       │
│  │  │  - REST API      │  │  - REST API      │  │  - REST API  ││       │
│  │  │  - WebSocket     │  │  - WebSocket     │  │  - WebSocket ││       │
│  │  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘│       │
│  └───────────┼─────────────────────┼────────────────────┼────────┘       │
│              │                     │                    │                │
│              └─────────────────────┴────────────────────┘                │
│                                    │                                     │
│  ┌─────────────────────────────────▼──────────────────────────────┐     │
│  │              ECS Fargate - Celery Workers                       │     │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │     │
│  │  │  Celery Worker   │  │  Celery Worker   │  │ Celery Beat  │ │     │
│  │  │  - AI Analysis   │  │  - Video Proc.   │  │ - Scheduler  │ │     │
│  │  │  - OpenAI API    │  │  - Frame Proc.   │  │ - Reports    │ │     │
│  │  └──────────────────┘  └──────────────────┘  └──────────────┘ │     │
│  └─────────────────────────────────────────────────────────────────     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
┌───────────────────────────────────┼─────────────────────────────────────┐
│                    CAPA DE DATOS Y MENSAJERÍA                            │
├───────────────────────────────────┼─────────────────────────────────────┤
│                                   │                                      │
│  ┌────────────────┐  ┌────────────▼──────┐  ┌─────────────────────┐    │
│  │  RDS PostgreSQL│  │  ElastiCache Redis│  │  SQS Queues         │    │
│  │  Multi-AZ      │  │  - Cache          │  │  ┌────────────────┐ │    │
│  │  - Primary     │  │  - Session Store  │  │  │ Frame Queue    │ │    │
│  │  - Standby     │  │  - Celery Broker  │  │  │ (from ESP32)   │ │    │
│  │  - Auto Backup │  │  - Channel Layer  │  │  └────────────────┘ │    │
│  │                │  │                   │  │  ┌────────────────┐ │    │
│  └────────────────┘  └───────────────────┘  │  │ AI Task Queue  │ │    │
│                                              │  │ (for analysis) │ │    │
│                                              │  └────────────────┘ │    │
│                                              └─────────────────────┘    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      S3 Buckets                                   │  │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌──────────────────┐  │  │
│  │  │ Video Frames    │  │ Video Archives │  │ Static Files     │  │  │
│  │  │ /frames/{vid}/  │  │ /videos/{id}/  │  │ /static/         │  │  │
│  │  │ Lifecycle: 7d   │  │ Lifecycle: 90d │  │ Public Read      │  │  │
│  │  └─────────────────┘  └────────────────┘  └──────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
┌───────────────────────────────────┼─────────────────────────────────────┐
│                    CAPA DE PROCESAMIENTO IA                              │
├───────────────────────────────────┼─────────────────────────────────────┤
│                                   │                                      │
│  ┌────────────────────────────────▼──────────────────────────────────┐  │
│  │              Lambda Functions (Event-Driven)                       │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │  │
│  │  │ Frame Processor  │  │ Incident Detector│  │ Chatbot Handler │ │  │
│  │  │ - S3 trigger     │  │ - SQS trigger    │  │ - API Gateway   │ │  │
│  │  │ - Resize/optimize│  │ - OpenAI Vision  │  │ - OpenAI GPT-4  │ │  │
│  │  │ - Enqueue AI task│  │ - Create alert   │  │ - FAQ context   │ │  │
│  │  └──────────────────┘  └──────────────────┘  └─────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    External Services                                │ │
│  │  ┌──────────────────┐             ┌──────────────────────┐         │ │
│  │  │  OpenAI API      │             │  AWS Bedrock         │         │ │
│  │  │  - GPT-4 Turbo   │             │  (Alternativa)       │         │ │
│  │  │  - Vision API    │             │  - Claude 3          │         │ │
│  │  └──────────────────┘             └──────────────────────┘         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
┌───────────────────────────────────┼─────────────────────────────────────┐
│                 CAPA DE MONITOREO Y SEGURIDAD                            │
├───────────────────────────────────┼─────────────────────────────────────┤
│                                   │                                      │
│  ┌────────────────┐  ┌────────────▼──────┐  ┌─────────────────────┐    │
│  │  CloudWatch    │  │  Secrets Manager  │  │  WAF                │    │
│  │  - Logs        │  │  - OPENAI_API_KEY │  │  - Rate Limiting    │    │
│  │  - Metrics     │  │  - DB Password    │  │  - SQL Injection    │    │
│  │  - Alarms      │  │  - JWT Secret     │  │  - DDoS Protection  │    │
│  │  - Dashboards  │  └───────────────────┘  └─────────────────────┘    │
│  └────────────────┘                                                     │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    IAM Roles & Policies                           │   │
│  │  - ECS Task Role (S3, SQS, Secrets access)                        │   │
│  │  - Lambda Execution Role (S3, OpenAI, SQS)                        │   │
│  │  - EC2 Instance Profile (if needed)                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Flujo de Datos

### 1. Flujo de Frame de Video (ESP32 → Sistema)

```
ESP32 Camera
    │
    │ HTTP POST /api/v1/video/frames/upload
    │ (multipart/form-data)
    │
    ▼
API Gateway
    │
    ▼
Lambda: Frame Processor
    │
    ├─→ S3: Save frame (s3://taxiwatch-frames/vehicle_123/2024-11-27_14-30-45.jpg)
    │
    ├─→ SQS: Enqueue AI Analysis Task
    │   {
    │     "frame_id": "...",
    │     "vehicle_id": 123,
    │     "s3_key": "...",
    │     "timestamp": "..."
    │   }
    │
    └─→ WebSocket: Broadcast to connected clients
        {
          "type": "new_frame",
          "vehicle_id": 123,
          "frame_url": "https://cdn.taxiwatch.com/frames/..."
        }
```

### 2. Flujo de Análisis de IA (Asíncrono)

```
SQS Queue: AI Analysis Tasks
    │
    │ (Celery Worker polling)
    │
    ▼
Celery Worker (ECS Fargate)
    │
    ├─→ Download frame from S3
    │
    ├─→ Call OpenAI Vision API
    │   Prompt: "Analiza esta imagen de cámara de taxi.
    │            Detecta: accidentes, frenado brusco, uso de teléfono,
    │            somnolencia, distracciones. Severidad: LOW/MEDIUM/HIGH/CRITICAL"
    │
    ├─→ Parse response
    │   {
    │     "incident_detected": true,
    │     "type": "PHONE_USAGE",
    │     "severity": "MEDIUM",
    │     "confidence": 0.87,
    │     "description": "Driver using phone while driving"
    │   }
    │
    ├─→ If incident detected:
    │   │
    │   ├─→ Create Incident record (PostgreSQL)
    │   │
    │   ├─→ Create Alert record
    │   │
    │   ├─→ WebSocket: Broadcast alert
    │   │   {
    │   │     "type": "new_alert",
    │   │     "incident_id": 456,
    │   │     "vehicle_id": 123,
    │   │     "severity": "MEDIUM",
    │   │     "message": "Driver using phone detected"
    │   │   }
    │   │
    │   └─→ (Optional) SNS: Send notification to admin
    │
    └─→ Update frame metadata in DB
```

### 3. Flujo de GPS Tracking (Tiempo Real)

```
ESP32 GPS Module
    │
    │ HTTP POST /api/v1/tracking/location
    │ {
    │   "vehicle_id": 123,
    │   "latitude": 40.7128,
    │   "longitude": -74.0060,
    │   "speed": 45.5,
    │   "heading": 180,
    │   "timestamp": "2024-11-27T14:30:45Z"
    │ }
    │
    ▼
API Gateway → Lambda: Location Processor
    │
    ├─→ PostgreSQL: Insert GPS_Location
    │
    ├─→ Redis: Update cache "vehicle:123:location" (TTL 10s)
    │
    └─→ WebSocket: Broadcast to map viewers
        {
          "type": "location_update",
          "vehicle_id": 123,
          "location": {...}
        }
```

### 4. Flujo de Chatbot (Usuario → IA)

```
Client Web App
    │
    │ POST /api/v1/chat/message
    │ {
    │   "message": "¿Cuántos vehículos tengo activos?",
    │   "session_id": "..."
    │ }
    │
    ▼
API Gateway → Lambda: Chatbot Handler
    │
    ├─→ Load context from PostgreSQL:
    │   - User info
    │   - FAQs
    │   - Recent data (vehicles, trips, incidents)
    │
    ├─→ Build prompt:
    │   System: "Eres el asistente de TaxiWatch. El usuario tiene
    │            15 vehículos activos, 3 en mantenimiento..."
    │   User: "¿Cuántos vehículos tengo activos?"
    │
    ├─→ Call OpenAI GPT-4
    │
    ├─→ Parse response
    │
    ├─→ Save to ChatHistory (PostgreSQL)
    │
    └─→ Return response
        {
          "response": "Actualmente tienes 15 vehículos activos.",
          "timestamp": "..."
        }
```

---

## Servicios AWS Detallados

### 1. **Route 53**
- **Dominio:** `taxiwatch.com`
- **Subdominios:**
  - `www.taxiwatch.com` → CloudFront (Frontend)
  - `api.taxiwatch.com` → ALB (Backend API)
  - `ws.taxiwatch.com` → ALB (WebSocket)

### 2. **CloudFront**
- **Origen:** S3 bucket con Next.js build estático
- **Caching:** Aggressive (max-age=31536000 para assets con hash)
- **Certificado SSL:** ACM (Amazon Certificate Manager)
- **Compresión:** Gzip, Brotli

### 3. **Application Load Balancer (ALB)**
- **Target Groups:**
  - TG1: ECS Fargate Tasks (Django API) - Port 8000
  - TG2: WebSocket connections - Port 8001
- **Health Check:** `GET /api/v1/health/` → 200 OK
- **SSL/TLS:** Certificate from ACM
- **Sticky Sessions:** Enabled para WebSocket

### 4. **API Gateway**
- **Endpoints:**
  - `POST /video/frames/upload` → Lambda Frame Processor
  - `POST /tracking/location` → Lambda Location Processor
  - `POST /chat/message` → Lambda Chatbot Handler
- **Throttling:** 1000 req/sec
- **API Keys:** Para ESP32 devices
- **CORS:** Configured

### 5. **ECS Fargate**
- **Cluster:** taxiwatch-cluster

**Service 1: Django API**
- **Task Definition:** django-api-task
- **CPU:** 1 vCPU
- **Memory:** 2 GB
- **Desired Count:** 2 (Auto-scaling 2-10)
- **Scaling Policy:** CPU > 70% → Scale out
- **Environment:**
  - `DB_HOST` → RDS endpoint
  - `REDIS_HOST` → ElastiCache endpoint
  - `OPENAI_API_KEY` → From Secrets Manager

**Service 2: Celery Workers**
- **Task Definition:** celery-worker-task
- **CPU:** 2 vCPU (IA analysis is CPU intensive)
- **Memory:** 4 GB
- **Desired Count:** 2 (Auto-scaling 2-5)
- **Scaling Policy:** SQS queue depth > 100 → Scale out

**Service 3: Celery Beat**
- **Task Definition:** celery-beat-task
- **CPU:** 0.5 vCPU
- **Memory:** 1 GB
- **Desired Count:** 1 (singleton)
- **Tareas programadas:**
  - Generate daily reports (6:00 AM)
  - Clean old frames from S3 (2:00 AM)
  - Check license expirations (8:00 AM)

### 6. **Lambda Functions**

**Function 1: Frame Processor**
- **Runtime:** Python 3.12
- **Memory:** 512 MB
- **Timeout:** 30s
- **Trigger:** API Gateway POST
- **Código:**
  - Validate request
  - Resize/optimize image
  - Upload to S3
  - Enqueue SQS message for AI
  - Return presigned URL

**Function 2: Location Processor**
- **Runtime:** Python 3.12
- **Memory:** 256 MB
- **Timeout:** 10s
- **Trigger:** API Gateway POST
- **Código:**
  - Validate GPS data
  - Insert to PostgreSQL
  - Update Redis cache
  - Broadcast via WebSocket (using API to ECS)

**Function 3: Chatbot Handler**
- **Runtime:** Python 3.12
- **Memory:** 1024 MB
- **Timeout:** 60s
- **Trigger:** API Gateway POST
- **Código:**
  - Load context from DB
  - Call OpenAI GPT-4
  - Save conversation history
  - Return response

**Function 4: Incident Detector** (Event-driven)
- **Runtime:** Python 3.12
- **Memory:** 2048 MB
- **Timeout:** 300s (5 min)
- **Trigger:** SQS Queue (AI Analysis Tasks)
- **Código:**
  - Download frame from S3
  - Call OpenAI Vision API
  - Parse response
  - Create Incident/Alert if detected
  - Send notifications

### 7. **RDS PostgreSQL**
- **Instance Class:** db.t3.medium (2 vCPU, 4 GB RAM)
- **Multi-AZ:** Enabled (high availability)
- **Storage:** 100 GB GP3 (auto-scaling to 1 TB)
- **Backup:** Automated daily, 7 days retention
- **Encryption:** At rest (KMS)
- **Parameter Group:** Custom (optimized for Django)

### 8. **ElastiCache Redis**
- **Node Type:** cache.t3.medium (2 vCPU, 3.09 GB)
- **Cluster Mode:** Disabled (simpler for Celery)
- **Replicas:** 1 read replica
- **Multi-AZ:** Enabled
- **Use Cases:**
  - Session storage
  - Cache (vehicle locations, user data)
  - Celery broker & result backend
  - Django Channels layer

### 9. **SQS Queues**

**Queue 1: ai-analysis-tasks.fifo**
- **Type:** FIFO (preservar orden por vehículo)
- **Message Retention:** 4 hours
- **Visibility Timeout:** 300s
- **Dead Letter Queue:** ai-analysis-dlq

**Queue 2: notification-queue**
- **Type:** Standard
- **Message Retention:** 14 days
- **Visibility Timeout:** 60s

### 10. **S3 Buckets**

**Bucket 1: taxiwatch-frames**
- **Path:** `frames/{vehicle_id}/{timestamp}.jpg`
- **Lifecycle:** Delete after 7 days
- **Access:** Private (presigned URLs)
- **Versioning:** Disabled
- **Encryption:** SSE-S3

**Bucket 2: taxiwatch-videos**
- **Path:** `videos/{vehicle_id}/{date}/{clip_id}.mp4`
- **Lifecycle:** Move to Glacier after 30 days, delete after 90 days
- **Access:** Private
- **Versioning:** Enabled

**Bucket 3: taxiwatch-static**
- **Path:** `static/*`
- **Access:** Public read
- **CloudFront:** Origin for CDN

**Bucket 4: taxiwatch-reports**
- **Path:** `reports/{user_id}/{report_id}.pdf`
- **Lifecycle:** Delete after 30 days
- **Access:** Private (presigned URLs)

### 11. **Secrets Manager**
- **Secret 1:** `taxiwatch/db`
  - `username`, `password`, `host`, `port`, `database`
- **Secret 2:** `taxiwatch/openai`
  - `api_key`
- **Secret 3:** `taxiwatch/jwt`
  - `secret_key`, `algorithm`

### 12. **CloudWatch**
- **Log Groups:**
  - `/ecs/django-api`
  - `/ecs/celery-worker`
  - `/lambda/frame-processor`
  - `/lambda/incident-detector`
  - `/lambda/chatbot-handler`

- **Alarms:**
  - ECS CPU > 80% → SNS notification
  - RDS Connections > 90% → SNS
  - SQS Queue depth > 500 → SNS
  - Lambda errors > 10/5min → SNS
  - ALB 5xx errors > 50/5min → SNS

- **Dashboards:**
  - Fleet Overview
  - API Performance
  - AI Processing Metrics
  - Cost Monitoring

### 13. **WAF (Web Application Firewall)**
- **Rules:**
  - Rate limiting: 2000 req/5min per IP
  - SQL injection protection
  - XSS protection
  - Block known bad IPs (AWS Managed Rules)
- **Attached to:** ALB, CloudFront

### 14. **SNS (Simple Notification Service)**
- **Topic 1:** `critical-alerts`
  - Subscriptions: Admin emails, SMS
- **Topic 2:** `system-alarms`
  - Subscriptions: DevOps team emails

---

## Estimación de Costos AWS (Mensual)

### Escenario: 50 vehículos activos, 10,000 usuarios

| Servicio | Configuración | Costo Mensual (USD) |
|----------|---------------|---------------------|
| **ECS Fargate** | 2 API tasks + 2 Workers + 1 Beat (24/7) | ~$150 |
| **RDS PostgreSQL** | db.t3.medium Multi-AZ + 100GB | ~$85 |
| **ElastiCache Redis** | cache.t3.medium + replica | ~$75 |
| **Lambda** | 1M invocations, 512MB avg | ~$20 |
| **S3** | 500GB storage + 1TB transfer | ~$35 |
| **CloudFront** | 1TB transfer | ~$85 |
| **ALB** | 1 ALB + LCUs | ~$25 |
| **API Gateway** | 1M requests | ~$3.50 |
| **SQS** | 5M requests | ~$2 |
| **Secrets Manager** | 3 secrets | ~$1.20 |
| **CloudWatch** | Logs 50GB + Alarms | ~$20 |
| **Route 53** | Hosted zone + queries | ~$1 |
| **OpenAI API** | 100k GPT-4 tokens/day | ~$150 |
| **OpenAI Vision** | 5k images/day | ~$50 |
| **Data Transfer** | Out to internet | ~$30 |
| **Misc** | Backups, SNS, etc | ~$10 |
| **TOTAL** | | **~$742/month** |

**Optimizaciones para reducir costos:**
- Usar Spot instances para Celery workers (-70%)
- Usar AWS Bedrock en lugar de OpenAI (-50% en IA)
- Aggressive S3 lifecycle policies
- Reserved Instances para RDS (-40%)
- **Costo optimizado:** ~$400-500/month

---

## Seguridad

### 1. Network Security
- **VPC:** Isolated VPC con subnets públicas y privadas
- **Security Groups:**
  - SG-ALB: Allow 80, 443 from 0.0.0.0/0
  - SG-ECS: Allow 8000-8001 from SG-ALB only
  - SG-RDS: Allow 5432 from SG-ECS only
  - SG-Redis: Allow 6379 from SG-ECS only
- **NACLs:** Default allow, deny known malicious IPs

### 2. Identity & Access Management
- **IAM Roles:** Principle of least privilege
- **MFA:** Required for admin users
- **API Keys:** Rotated every 90 days
- **Secrets:** Never in code, always Secrets Manager

### 3. Data Protection
- **Encryption at rest:** All RDS, S3, ElastiCache
- **Encryption in transit:** TLS 1.2+ everywhere
- **Backups:** Automated, encrypted
- **Data retention:** GDPR compliant

### 4. Application Security
- **JWT:** Short-lived tokens (1h), refresh rotation
- **CORS:** Whitelist only
- **Rate Limiting:** WAF + Application level
- **Input Validation:** All endpoints
- **SQL Injection:** ORM (SQLAlchemy) + parameterized queries

---

## CI/CD Pipeline

```
GitHub Repository
    │
    │ Push to main branch
    │
    ▼
GitHub Actions Workflow
    │
    ├─→ Run tests (pytest)
    │
    ├─→ Lint code (flake8, eslint)
    │
    ├─→ Build Docker images
    │   - Backend (Django)
    │   - Frontend (Next.js)
    │   - Celery Worker
    │
    ├─→ Push images to ECR
    │   - taxiwatch/backend:latest
    │   - taxiwatch/frontend:latest
    │   - taxiwatch/celery:latest
    │
    ├─→ Run DB migrations (ECS task)
    │
    ├─→ Update ECS Services
    │   - Rolling update strategy
    │   - Health check before routing traffic
    │
    ├─→ Deploy Lambda functions
    │   - Package + upload to S3
    │   - Update function code
    │
    ├─→ Sync static files to S3
    │
    ├─→ Invalidate CloudFront cache
    │
    └─→ Notify Slack/Teams
        "Deployment complete! 🚀"
```

---

## Disaster Recovery

### RTO (Recovery Time Objective): 1 hour
### RPO (Recovery Point Objective): 15 minutes

**Backup Strategy:**
1. **RDS:** Automated daily snapshots + transaction logs every 5 min
2. **S3:** Versioning enabled, cross-region replication
3. **Code:** GitHub (redundant)
4. **Config:** Infrastructure as Code (Terraform) in Git

**Recovery Procedures:**
1. **Database failure:** Promote read replica (< 5 min)
2. **AZ failure:** Multi-AZ handles automatically
3. **Region failure:** Deploy to secondary region from Terraform
4. **Application bug:** Rollback ECS task definition

---

## Monitoreo y Alertas

### Métricas Clave

**Application Metrics:**
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active WebSocket connections

**Infrastructure Metrics:**
- ECS CPU/Memory utilization
- RDS IOPS, connections
- Redis hit rate
- Lambda duration, errors
- SQS queue depth

**Business Metrics:**
- Active vehicles
- Incidents detected/hour
- AI analysis throughput
- Cost per vehicle/month

### Dashboards

**Dashboard 1: Operations**
- Real-time map of vehicles
- Active incidents
- Alert feed
- System health status

**Dashboard 2: Engineering**
- API latency graphs
- Error rates
- Database performance
- Lambda execution times

**Dashboard 3: Business**
- Daily active users
- Incidents by type
- Cost breakdown
- AI accuracy metrics

---

## Escalabilidad

### Auto-Scaling Triggers

**ECS Django API:**
- Metric: CPU > 70% for 2 min → Scale out +1 task
- Metric: CPU < 30% for 5 min → Scale in -1 task
- Min: 2, Max: 10 tasks

**ECS Celery Workers:**
- Metric: SQS queue depth > 100 → Scale out +1 task
- Metric: SQS queue depth < 10 for 5 min → Scale in -1 task
- Min: 2, Max: 5 tasks

**RDS Read Replicas:**
- Manual scaling (create up to 5 read replicas)
- Route read queries to replicas

### Performance Targets

- **API Response Time:** < 200ms (p95)
- **WebSocket Latency:** < 100ms
- **Frame Processing:** < 2s (upload → S3)
- **AI Analysis:** < 30s per frame
- **Dashboard Load:** < 2s
- **Concurrent Users:** 1000+
- **Concurrent Vehicles:** 500+

---

## Next Steps para Implementación

1. **Validación Local (Semana 1)**
   - Docker Compose funcionando
   - Todos los endpoints implementados
   - WebSocket funcionando
   - Chatbot básico operativo

2. **Preparación AWS (Semana 2)**
   - Crear cuenta AWS
   - Setup Terraform/CloudFormation
   - Crear VPC, subnets, security groups

3. **Deploy Infraestructura (Semana 3)**
   - RDS PostgreSQL
   - ElastiCache Redis
   - S3 buckets
   - ECR repositories

4. **Deploy Aplicación (Semana 4)**
   - ECS Cluster + Services
   - Lambda functions
   - API Gateway
   - CloudFront

5. **Testing & Tuning (Semana 5)**
   - Load testing
   - Security audit
   - Cost optimization
   - Monitoring setup

6. **Demo & Presentación (Semana 6)**
   - Video demo
   - Documentación
   - Presentación final
