# Migración a FastAPI + Lambda + Terraform

## Cambios Arquitectónicos

### Antes (Django + ECS)
- Django monolithic app
- Django REST Framework
- Django Admin
- ECS Fargate containers
- Celery workers

### Después (FastAPI + Lambda)
- FastAPI microservices
- SQLAdmin for admin panel
- AWS Lambda functions
- API Gateway
- SQS + EventBridge for async tasks
- Terraform for IaC

---

## Nueva Estructura del Proyecto

```
cognitive-final-project/
├── backend/                      # Nueva carpeta FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app principal
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy async setup
│   │   ├── dependencies.py      # FastAPI dependencies
│   │   │
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── vehicle.py
│   │   │   ├── tracking.py
│   │   │   ├── incident.py
│   │   │   └── video.py
│   │   │
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── vehicle.py
│   │   │   ├── tracking.py
│   │   │   └── ...
│   │   │
│   │   ├── api/                 # API routers
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py      # Login, register
│   │   │   │   ├── users.py     # User CRUD
│   │   │   │   ├── vehicles.py  # Vehicle CRUD
│   │   │   │   ├── tracking.py  # GPS tracking
│   │   │   │   ├── video.py     # Video frames
│   │   │   │   ├── incidents.py # Incidents & alerts
│   │   │   │   └── chat.py      # AI Chatbot
│   │   │
│   │   ├── admin/               # SQLAdmin setup
│   │   │   ├── __init__.py
│   │   │   ├── views.py         # ModelView classes
│   │   │   └── auth.py          # Admin authentication
│   │   │
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── chat_service.py  # OpenAI integration
│   │   │   └── ai_service.py    # Vision API
│   │   │
│   │   ├── core/                # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py      # JWT, password hashing
│   │   │   └── exceptions.py
│   │   │
│   │   └── lambda_handlers/     # AWS Lambda handlers
│   │       ├── __init__.py
│   │       ├── api_handler.py   # Main API handler (Mangum)
│   │       ├── frame_processor.py
│   │       ├── incident_detector.py
│   │       └── chatbot_handler.py
│   │
│   ├── alembic/                 # DB migrations
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api/
│   │   └── test_services/
│   │
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── README.md
│
├── terraform/                   # Infraestructura como código
│   ├── main.tf                  # Main config
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf              # AWS provider
│   │
│   ├── modules/
│   │   ├── vpc/                 # VPC, subnets, security groups
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── rds/                 # PostgreSQL RDS
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── lambda/              # Lambda functions
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── api_gateway/         # API Gateway HTTP
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── s3/                  # S3 buckets
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   ├── sqs/                 # SQS queues
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   │
│   │   └── elasticache/         # Redis cluster
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   │
│   ├── environments/
│   │   ├── dev.tfvars
│   │   ├── staging.tfvars
│   │   └── prod.tfvars
│   │
│   └── backend.tf               # Terraform state (S3)
│
├── scripts/
│   ├── deploy.sh                # Deploy to AWS
│   ├── build_lambda.sh          # Build Lambda layers
│   └── seed_data.py             # Populate DB
│
├── ui/                          # Frontend (Next.js - mantener)
│   └── ...
│
├── hardware/                    # ESP32 simulator
│   └── ...
│
├── docker-compose.yml           # Para desarrollo local
├── .env.example
└── README.md
```

---

## Stack Tecnológico (Actualizado)

### Backend
- **FastAPI 0.104+** - Framework web asíncrono
- **SQLAlchemy 2.0** - ORM con async support
- **SQLAdmin** - Panel de administración
- **Alembic** - Migraciones de base de datos
- **Pydantic v2** - Validación de datos
- **AsyncPG** - Driver PostgreSQL asíncrono
- **Python-Jose** - JWT tokens
- **Passlib** - Password hashing
- **Mangum** - ASGI adapter para Lambda

### IA
- **OpenAI Python SDK** - GPT-4 y Vision API
- **Pillow** - Procesamiento de imágenes

### AWS Services
- **Lambda** - Compute serverless
- **API Gateway HTTP** - Routing
- **RDS PostgreSQL** - Base de datos
- **ElastiCache Redis** - Cache
- **S3** - Storage (frames, videos, static)
- **SQS** - Message queues
- **EventBridge** - Event scheduling
- **Secrets Manager** - Secrets
- **CloudWatch** - Logs y métricas
- **CloudFront** - CDN

### IaC
- **Terraform 1.6+** - Infrastructure as Code
- **AWS Provider** - Terraform AWS plugin

---

## Arquitectura Lambda

### Lambda Functions

#### 1. **Main API Lambda** (`api_handler`)
- **Runtime:** Python 3.12
- **Memory:** 1024 MB
- **Timeout:** 30s
- **Trigger:** API Gateway HTTP API
- **Endpoints:** Todos los `/api/v1/*`
- **VPC:** Sí (acceso a RDS)
- **Handler:** Mangum(app)

#### 2. **Frame Processor Lambda** (`frame_processor`)
- **Runtime:** Python 3.12
- **Memory:** 512 MB
- **Timeout:** 60s
- **Trigger:** API Gateway POST `/video/frames/upload`
- **VPC:** No
- **Función:**
  - Recibir frame desde ESP32
  - Validar y optimizar imagen
  - Subir a S3
  - Enviar mensaje a SQS para análisis

#### 3. **Incident Detector Lambda** (`incident_detector`)
- **Runtime:** Python 3.12
- **Memory:** 2048 MB (IA requiere más memoria)
- **Timeout:** 300s (5 min)
- **Trigger:** SQS Queue (AI Analysis Tasks)
- **VPC:** Sí (escribir a RDS)
- **Función:**
  - Descargar frame de S3
  - Llamar OpenAI Vision API
  - Crear Incident si detectado
  - Crear Alert
  - (Opcional) Enviar SNS notification

#### 4. **Chatbot Lambda** (`chatbot_handler`)
- **Runtime:** Python 3.12
- **Memory:** 1024 MB
- **Timeout:** 60s
- **Trigger:** API Gateway POST `/api/v1/chat`
- **VPC:** Sí (leer context de RDS)
- **Función:**
  - Cargar contexto del usuario
  - Llamar OpenAI GPT-4
  - Guardar historial en RDS
  - Retornar respuesta

#### 5. **Scheduled Tasks Lambda** (`scheduled_tasks`)
- **Runtime:** Python 3.12
- **Memory:** 512 MB
- **Timeout:** 900s (15 min)
- **Trigger:** EventBridge cron
- **VPC:** Sí
- **Función:**
  - Generar reportes diarios (6:00 AM)
  - Limpiar frames antiguos de S3 (2:00 AM)
  - Verificar vencimiento de licencias (8:00 AM)

---

## Comparación de Arquitecturas

| Aspecto | Django + ECS | FastAPI + Lambda |
|---------|--------------|------------------|
| **Compute** | ECS Fargate (siempre corriendo) | Lambda (pago por uso) |
| **Escalabilidad** | Manual/Auto-scaling (2-10 tasks) | Automática (0-1000+ concurrent) |
| **Costo Idle** | $150/mes (tasks running 24/7) | $0 (sin requests) |
| **Cold Start** | No | Sí (~1-2s primera request) |
| **Admin Panel** | Django Admin (built-in) | SQLAdmin (integrado) |
| **Async Tasks** | Celery + Redis | SQS + Lambda |
| **IaC** | Docker Compose | Terraform |
| **CI/CD** | Docker build + ECS deploy | Zip + Lambda update |
| **Costo estimado/mes** | $742 | $250-400 |

---

## Ventajas de Lambda

1. **Pay-per-use:** Solo pagas cuando se ejecuta código
2. **Auto-scaling:** Escala automáticamente a miles de requests
3. **No servers:** AWS maneja todo el infrastructure
4. **Terraform friendly:** Fácil de provisionar con IaC
5. **Microservices:** Cada función es independiente
6. **Mejor para demos:** Fácil de mostrar en presentación

---

## Desventajas de Lambda

1. **Cold starts:** Primera request lenta (~1-2s)
2. **Timeout límite:** Max 15 minutos
3. **No WebSockets nativos:** Requiere API Gateway WebSocket API
4. **Package size:** Max 250MB (con layers)
5. **VPC latency:** Conectar a RDS agrega ~100ms

---

## Mitigaciones

### Cold Starts
- **Provisioned Concurrency:** Mantener 1-2 Lambdas warm (costo adicional)
- **Lambda SnapStart:** Para Java (no aplica para Python)
- **Keep-alive pings:** EventBridge cada 5 min

### WebSockets
- **Alternativa 1:** API Gateway WebSocket API (más complejo con Terraform)
- **Alternativa 2:** Polling desde frontend (cada 3-5s)
- **Alternativa 3:** Server-Sent Events (SSE)

### Package Size
- **Lambda Layers:** Dependencias comunes (SQLAlchemy, OpenAI, etc.)
- **Slim requirements:** Solo lo necesario
- **Docker image:** Alternativa (hasta 10GB)

---

## Plan de Implementación

### Fase 1: Setup Inicial (Día 1)
1. Crear nueva estructura `/backend`
2. Instalar dependencias FastAPI
3. Configurar SQLAlchemy async
4. Modelos de base de datos
5. Alembic migrations

### Fase 2: FastAPI App (Días 2-3)
1. Main app con SQLAdmin
2. API routers (auth, users, vehicles)
3. Tracking, video, incidents endpoints
4. Chatbot endpoint
5. Testing local con `uvicorn`

### Fase 3: Lambda Handlers (Día 4)
1. API handler (Mangum)
2. Frame processor
3. Incident detector
4. Chatbot handler
5. Scheduled tasks

### Fase 4: Terraform (Días 5-6)
1. VPC module
2. RDS module
3. Lambda module
4. API Gateway module
5. S3, SQS modules
6. Variables y outputs

### Fase 5: Deploy & Testing (Día 7)
1. `terraform apply`
2. Deploy Lambda functions
3. Run migrations en RDS
4. Test endpoints
5. Test ESP32 simulator
6. Verify admin panel

---

## Próximos Pasos

1. ✅ Revisar este documento
2. ⏳ Crear estructura `/backend`
3. ⏳ Implementar modelos SQLAlchemy
4. ⏳ Implementar API routers
5. ⏳ Crear Lambda handlers
6. ⏳ Crear módulos Terraform
7. ⏳ Deploy a AWS
8. ⏳ Testing completo

¿Procedemos con la creación del código FastAPI?
