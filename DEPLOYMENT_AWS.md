# Guía de Deployment AWS - TaxiWatch

## 📋 ÍNDICE

1. [Pre-requisitos](#pre-requisitos)
2. [Preparar Lambda Package](#preparar-lambda-package)
3. [Configurar Variables de Terraform](#configurar-variables)
4. [Deployment con Terraform](#deployment-con-terraform)
5. [Post-Deployment](#post-deployment)
6. [Testing en AWS](#testing-en-aws)
7. [Monitoreo](#monitoreo)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 PRE-REQUISITOS

### 1. Herramientas Necesarias

```bash
# Terraform
brew install terraform

# AWS CLI
brew install awscli

# Python 3.12+
python3 --version

# Docker (para builds)
docker --version
```

### 2. Configurar AWS Credentials

```bash
aws configure
# AWS Access Key ID: [tu-access-key]
# AWS Secret Access Key: [tu-secret-key]
# Default region name: us-east-1
# Default output format: json

# Verificar
aws sts get-caller-identity
```

### 3. Crear S3 Bucket para Terraform State

```bash
# Crear bucket para state (solo primera vez)
aws s3 mb s3://taxiwatch-terraform-state --region us-east-1

# Habilitar versionado
aws s3api put-bucket-versioning \
  --bucket taxiwatch-terraform-state \
  --versioning-configuration Status=Enabled

# Habilitar encriptación
aws s3api put-bucket-encryption \
  --bucket taxiwatch-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

---

## 📦 PREPARAR LAMBDA PACKAGE

### Opción 1: Script Automático (Recomendado)

Crear `backend/build_lambda.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Building Lambda packages..."

# Limpiar builds anteriores
rm -rf build/
rm -f lambda_package.zip lambda_layer.zip

# Crear directorios
mkdir -p build/lambda build/layer/python

# Copiar código de aplicación
echo "📦 Copying application code..."
cp -r app build/lambda/
cp -r alembic build/lambda/
cp alembic.ini build/lambda/

# Crear Lambda layer con dependencias
echo "📚 Creating Lambda layer..."
pip install -r requirements.txt -t build/layer/python/ --platform manylinux2014_x86_64 --only-binary=:all:

# Crear ZIPs
echo "🗜️ Creating ZIP files..."
cd build/lambda && zip -r ../../lambda_package.zip . -x "*.pyc" "__pycache__/*"
cd ../layer && zip -r ../../lambda_layer.zip .

cd ../..
echo "✅ Lambda packages created:"
ls -lh lambda_package.zip lambda_layer.zip
```

Ejecutar:

```bash
cd backend
chmod +x build_lambda.sh
./build_lambda.sh
```

### Opción 2: Manual

```bash
cd backend

# Crear layer con dependencias
mkdir -p build/layer/python
pip install -r requirements.txt -t build/layer/python/ \
  --platform manylinux2014_x86_64 --only-binary=:all:

cd build/layer
zip -r ../../lambda_layer.zip .
cd ../..

# Crear package con código
mkdir -p build/lambda
cp -r app alembic alembic.ini build/lambda/
cd build/lambda
zip -r ../../lambda_package.zip . -x "*.pyc" "__pycache__/*"
cd ../..

# Verificar
ls -lh lambda_package.zip lambda_layer.zip
```

**IMPORTANTE**: Los archivos ZIP deben estar en `backend/`:
- `lambda_package.zip` - Código de la aplicación
- `lambda_layer.zip` - Dependencias Python

---

## ⚙️ CONFIGURAR VARIABLES

### 1. Crear `terraform/terraform.tfvars`

```hcl
# General
project_name = "taxiwatch"
environment  = "prod"
aws_region   = "us-east-1"

# VPC
vpc_cidr             = "10.0.0.0/16"
availability_zones   = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
database_subnet_cidrs = ["10.0.20.0/24", "10.0.21.0/24"]

# RDS
db_name           = "taxiwatch"
db_username       = "taxiwatch_admin"
db_password       = "CAMBIAR-POR-PASSWORD-SEGURO"  # ⚠️ IMPORTANTE
db_instance_class = "db.t3.micro"  # Cambiar a db.t3.small para producción
db_allocated_storage = 20
db_multi_az       = false  # Cambiar a true para producción

# ElastiCache
redis_node_type = "cache.t3.micro"

# Secrets
secret_key     = "CAMBIAR-POR-SECRET-KEY-ALEATORIO-LARGO"  # ⚠️ IMPORTANTE
openai_api_key = "sk-..."  # ⚠️ Tu API key de OpenAI

# CORS
cors_origins      = "http://localhost:3000,https://yourdomain.com"
cors_origins_list = ["http://localhost:3000", "https://yourdomain.com"]

# Lambda
api_lambda_zip   = "../backend/lambda_package.zip"
lambda_layer_zip = "../backend/lambda_layer.zip"

# Custom Domain (Opcional - dejar vacío si no usas)
custom_domain_name = ""
certificate_arn    = ""
```

### 2. Generar Secrets Seguros

```bash
# Secret Key (Python)
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Database Password
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🚀 DEPLOYMENT CON TERRAFORM

### Paso 1: Inicializar Terraform

```bash
cd terraform

# Inicializar providers y backend
terraform init

# Verificar configuración
terraform validate
```

### Paso 2: Plan (Verificar cambios)

```bash
# Ver qué recursos se crearán
terraform plan -out=tfplan

# Revisar el output cuidadosamente
# Deberías ver ~50-60 recursos a crear
```

### Paso 3: Apply (Crear infraestructura)

```bash
# Aplicar cambios
terraform apply tfplan

# O interactivo:
terraform apply

# Confirmar con: yes
```

**Tiempo estimado**: 10-15 minutos

### Paso 4: Guardar Outputs

```bash
# Ver todos los outputs
terraform output

# Guardar API endpoint
terraform output -raw api_endpoint > ../API_ENDPOINT.txt
echo "API Endpoint: $(cat ../API_ENDPOINT.txt)"
```

---

## 🔧 POST-DEPLOYMENT

### 1. Ejecutar Migraciones de Base de Datos

```bash
# Opción A: Conectarse vía Lambda (recomendado)
aws lambda invoke \
  --function-name taxiwatch-prod-api \
  --payload '{"rawPath": "/migrate"}' \
  response.json

cat response.json
```

O manualmente vía Bastion Host:

```bash
# Crear EC2 Bastion en subnet pública (temporal)
# Conectar a RDS y ejecutar:
# psql -h [RDS_ENDPOINT] -U taxiwatch_admin -d taxiwatch

# Desde tu local con túnel SSH:
DB_HOST=$(terraform output -raw db_endpoint)
ssh -L 5432:$DB_HOST:5432 ec2-user@[BASTION_IP]

# En otra terminal:
cd backend
DATABASE_URL="postgresql+asyncpg://taxiwatch_admin:[PASSWORD]@localhost:5432/taxiwatch" \
  alembic upgrade head
```

### 2. Crear Usuario Admin

Crear `scripts/create_admin_aws.py`:

```python
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Usar endpoint de RDS
DATABASE_URL = os.getenv("DATABASE_URL")  # Desde output de Terraform

async def create_admin():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash

        admin = User(
            username="admin",
            email="admin@taxiwatch.com",
            hashed_password=get_password_hash("Admin123!"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_superuser=True,
            is_active=True
        )
        session.add(admin)
        await session.commit()
        print("✅ Admin user created!")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

Ejecutar:

```bash
cd backend
DB_ENDPOINT=$(cd ../terraform && terraform output -raw db_endpoint)
DB_PASSWORD="[tu-password]"

DATABASE_URL="postgresql+asyncpg://taxiwatch_admin:$DB_PASSWORD@$DB_ENDPOINT/taxiwatch" \
  python3 ../scripts/create_admin_aws.py
```

### 3. Verificar Logs

```bash
# Logs de Lambda API
aws logs tail /aws/lambda/taxiwatch-prod-api --follow

# Logs de Frame Processor
aws logs tail /aws/lambda/taxiwatch-prod-frame-processor --follow

# Logs de API Gateway
aws logs tail /aws/apigateway/taxiwatch-prod --follow
```

---

## 🧪 TESTING EN AWS

### 1. Health Check

```bash
API_ENDPOINT=$(cd terraform && terraform output -raw api_endpoint)

curl $API_ENDPOINT/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "app": "TaxiWatch API",
  "version": "2.0.0",
  "environment": "prod"
}
```

### 2. Login

```bash
curl -X POST $API_ENDPOINT/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'
```

Guardar el `access_token` para siguientes requests.

### 3. Crear Vehículo

```bash
TOKEN="eyJhbG..."

curl -X POST $API_ENDPOINT/api/v1/vehicles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "license_plate": "ABC-1234",
    "make": "Toyota",
    "model": "Corolla",
    "year": 2023,
    "color": "White",
    "vin": "12345678901234567",
    "capacity": 4,
    "status": "ACTIVE"
  }'
```

### 4. Enviar GPS desde ESP32

```bash
# Simular ESP32 enviando ubicación
curl -X POST $API_ENDPOINT/api/v1/tracking/location \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": 1,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "speed": 45.5,
    "heading": 180,
    "accuracy": 10.0,
    "device_id": "ESP32_001"
  }'
```

### 5. Subir Frame desde ESP32

```bash
# Crear frame de prueba en base64
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" > /tmp/test_frame.b64

curl -X POST $API_ENDPOINT/api/v1/video/frames/upload \
  -H "Content-Type: application/json" \
  -d "{
    \"device_id\": \"ESP32_001\",
    \"vehicle_id\": 1,
    \"camera_position\": \"FRONT\",
    \"frame_base64\": \"$(cat /tmp/test_frame.b64)\"
  }"
```

---

## 📊 MONITOREO

### CloudWatch Dashboards

```bash
# Ver métricas de Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=taxiwatch-prod-api \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Logs útiles

```bash
# Errores de Lambda
aws logs filter-pattern /aws/lambda/taxiwatch-prod-api --filter-pattern "ERROR"

# SQS DLQ (mensajes fallidos)
aws sqs receive-message --queue-url $(cd terraform && terraform output -raw dlq_url)
```

### Métricas Clave

- **Lambda Invocations**: API calls por minuto
- **Lambda Errors**: Errores en funciones
- **API Gateway 4xx/5xx**: Errores de cliente/servidor
- **RDS CPU/Connections**: Uso de base de datos
- **SQS Messages**: Cola de análisis AI

---

## 🐛 TROUBLESHOOTING

### Error: "Lambda timeout"

```bash
# Aumentar timeout en terraform/modules/lambda/main.tf
# Cambiar: timeout = 30
# A: timeout = 60

cd terraform
terraform apply
```

### Error: "Could not connect to database"

```bash
# Verificar security groups
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=taxiwatch-*"

# Verificar que Lambda SG puede acceder a RDS SG (puerto 5432)
```

### Error: "Module not found"

```bash
# Rebuild Lambda package con todas las dependencias
cd backend
rm -rf build/ lambda_package.zip lambda_layer.zip
./build_lambda.sh

# Re-deploy
cd ../terraform
terraform apply -replace=module.lambda.aws_lambda_function.api
```

### Error: "OpenAI API key invalid"

```bash
# Actualizar secret en Secrets Manager
aws secretsmanager update-secret \
  --secret-id taxiwatch-prod-secrets \
  --secret-string '{"SECRET_KEY":"...","OPENAI_API_KEY":"sk-...","DB_PASSWORD":"..."}'

# Forzar re-deploy de Lambda
cd terraform
terraform apply -replace=module.lambda.aws_lambda_function.api
```

### Logs no aparecen

```bash
# Verificar permisos de CloudWatch Logs
aws iam get-role-policy \
  --role-name taxiwatch-prod-lambda-role \
  --policy-name taxiwatch-lambda-custom-policy

# Debe incluir logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
```

---

## 🔄 ACTUALIZAR DEPLOYMENT

### Cambios de Código

```bash
# 1. Rebuild Lambda package
cd backend
./build_lambda.sh

# 2. Deploy con Terraform
cd ../terraform
terraform apply -replace=module.lambda.aws_lambda_function.api
```

### Cambios de Infraestructura

```bash
cd terraform

# Modificar variables.tf o main.tf según necesites
# Luego:
terraform plan
terraform apply
```

---

## 💰 ESTIMACIÓN DE COSTOS (AWS)

**Configuración Dev/Testing (db.t3.micro, cache.t3.micro)**:
- RDS: ~$15/mes
- ElastiCache: ~$12/mes
- Lambda: ~$5-10/mes (1M requests)
- S3: ~$5/mes (100GB)
- API Gateway: ~$3/mes (1M requests)
- **Total: ~$40-45/mes**

**Configuración Producción (db.t3.small, cache.t3.small, Multi-AZ)**:
- RDS: ~$60/mes
- ElastiCache: ~$40/mes
- Lambda: ~$20/mes (5M requests)
- S3: ~$20/mes (500GB)
- API Gateway: ~$10/mes (5M requests)
- **Total: ~$150/mes**

---

## 🎯 CHECKLIST DE DEPLOYMENT

- [ ] AWS CLI configurado con credentials
- [ ] S3 bucket creado para Terraform state
- [ ] Lambda packages creados (lambda_package.zip, lambda_layer.zip)
- [ ] Variables configuradas en terraform.tfvars
- [ ] Secrets seguros generados (SECRET_KEY, db_password)
- [ ] OpenAI API key configurada
- [ ] `terraform init` ejecutado
- [ ] `terraform plan` revisado
- [ ] `terraform apply` completado exitosamente
- [ ] Migraciones de BD ejecutadas
- [ ] Usuario admin creado
- [ ] Health check OK
- [ ] Login funciona
- [ ] GPS endpoint funciona
- [ ] Video upload funciona
- [ ] CloudWatch logs configurados
- [ ] API endpoint documentado para ESP32

---

## ✅ RESUMEN

**Con esta guía puedes:**

1. ✅ Deployar toda la infraestructura AWS con Terraform
2. ✅ Lambda functions para API y procesamiento de frames
3. ✅ RDS PostgreSQL para base de datos
4. ✅ ElastiCache Redis para caching
5. ✅ S3 para almacenamiento de frames y videos
6. ✅ SQS para procesamiento asíncrono de AI
7. ✅ API Gateway con endpoints públicos
8. ✅ CloudWatch para logs y métricas
9. ✅ Secrets Manager para credenciales

**Siguiente paso**: Configurar tu ESP32 para enviar datos al endpoint de AWS!
