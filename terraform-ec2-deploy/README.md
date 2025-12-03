# TaxiWatch AWS Deployment - EC2 + RDS + S3

Guía rápida para deployar TaxiWatch en AWS usando Terraform.

## Arquitectura

```
Internet → Elastic IP → EC2 (t3.small)
                        ├── Docker Compose
                        │   ├── Backend (port 8000)
                        │   └── Frontend (port 3000)
                        ↓
                     RDS PostgreSQL (db.t3.micro)
                     S3 Buckets (frames, videos)
```

## Pre-requisitos

1. **AWS CLI configurado**:
   ```bash
   aws configure
   # Ya lo tienes configurado según confirmaste
   ```

2. **Terraform instalado**:
   ```bash
   # Mac
   brew install terraform

   # O descargar desde: https://www.terraform.io/downloads
   ```

3. **Git y Docker** (en tu máquina local para desarrollo)

## Pasos de Deployment

### 1. Configurar Variables

Edita `terraform/terraform.tfvars`:

```hcl
# General
project_name = "taxiwatch"
environment  = "prod"
aws_region   = "us-west-2"

# EC2
ec2_instance_type = "t3.small"
ec2_ami_id        = "ami-047f8ab1a8e4de3659"
ec2_key_name      = ""  # Dejar vacío para auto-generar

# RDS
db_password = "TU_PASSWORD_SEGURO_AQUI"  # ⚠️ CAMBIAR

# Application
secret_key = "GENERAR_CON: openssl rand -hex 32"  # ⚠️ CAMBIAR
```

### 2. Generar Secret Key

```bash
# Generar secret key aleatorio
openssl rand -hex 32
# Copiar resultado a terraform.tfvars
```

### 3. Initialize Terraform

```bash
cd terraform

# Usar los archivos EC2 (no los de Lambda)
mv main.tf main-lambda.tf.bak
mv variables.tf variables-lambda.tf.bak
mv outputs.tf outputs-lambda.tf.bak

mv main-ec2.tf main.tf
mv variables-ec2.tf variables.tf
mv outputs-ec2.tf outputs.tf

# Initialize
terraform init
```

### 4. Plan y Apply

```bash
# Ver qué se va a crear
terraform plan

# Crear infraestructura (toma ~10-15 minutos)
terraform apply

# Confirmar con: yes
```

### 5. Obtener Outputs

```bash
# Ver toda la información
terraform output

# URLs específicas
terraform output frontend_url
terraform output backend_url
terraform output ssh_command
```

Ejemplo de output:
```
frontend_url = "http://54.123.456.789:3000"
backend_url = "http://54.123.456.789:8000"
backend_docs_url = "http://54.123.456.789:8000/docs"
ssh_command = "ssh -i taxiwatch-prod-key.pem ubuntu@54.123.456.789"
```

### 6. Esperar Inicialización

El EC2 se configura automáticamente (user_data script):
- Instala Docker y Docker Compose
- Clona el repositorio
- Ejecuta migraciones
- Levanta los servicios

**Tiempo estimado**: 5-10 minutos

### 7. Verificar Deployment

```bash
# Obtener IP pública
EC2_IP=$(terraform output -raw ec2_public_ip)

# Verificar backend
curl http://$EC2_IP:8000/health

# Verificar frontend (en navegador)
open http://$EC2_IP:3000
```

### 8. Acceder por SSH (opcional)

```bash
# Usar la key generada
chmod 400 taxiwatch-prod-key.pem
ssh -i taxiwatch-prod-key.pem ubuntu@$EC2_IP

# Ver logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Ver servicios corriendo
docker compose ps
```

## Actualizar Aplicación

```bash
# SSH al EC2
ssh -i taxiwatch-prod-key.pem ubuntu@$EC2_IP

# Actualizar código
cd ~/app
git pull origin master

# Rebuild y restart
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Ver logs
docker compose logs -f
```

## Configurar ESP32-CAM

En tu código ESP32, actualiza la URL:

```cpp
// Reemplazar con tu IP pública de EC2
String serverName = "http://54.123.456.789:8000/api/v1/video/device/upload";
String route_id = "taxi-01";
```

## Destruir Infraestructura

```bash
cd terraform

# Ver qué se va a eliminar
terraform plan -destroy

# Eliminar todo
terraform destroy

# Confirmar con: yes
```

**⚠️ ADVERTENCIA**: Esto eliminará TODO (EC2, RDS, S3). Los datos se perderán.

## Costos Estimados

- EC2 t3.small: ~$15/mes
- RDS db.t3.micro: FREE TIER (primer año), luego ~$15/mes
- S3 storage: ~$1-3/mes
- Elastic IP: FREE (mientras esté attached)
- **Total**: ~$5-20/mes (con free tier) o ~$30-35/mes (sin free tier)

## Troubleshooting

### Backend no arranca

```bash
# SSH al EC2
ssh -i taxiwatch-prod-key.pem ubuntu@$EC2_IP

# Ver logs del backend
docker compose logs backend

# Verificar env vars
docker compose exec backend env | grep DATABASE_URL
```

### Frontend no carga

```bash
# Verificar que el puerto 3000 esté abierto
curl http://localhost:3000

# Ver logs
docker compose logs frontend

# Rebuild frontend
docker compose up -d --build frontend
```

### RDS connection error

```bash
# Verificar que RDS esté corriendo
aws rds describe-db-instances --region us-west-2

# Verificar security group
# EC2 debe tener acceso al security group de RDS
```

### User data script falló

```bash
# SSH al EC2
ssh -i taxiwatch-prod-key.pem ubuntu@$EC2_IP

# Ver logs de user data
sudo cat /var/log/user-data.log
sudo tail -100 /var/log/cloud-init-output.log
```

## URLs Importantes

Después del deployment, tendrás:

- **Frontend**: http://<EC2_IP>:3000
- **Backend API**: http://<EC2_IP>:8000
- **API Docs**: http://<EC2_IP>:8000/docs
- **Admin Panel**: http://<EC2_IP>:8000/admin

## Siguiente Pasos (Producción Real)

Para un deployment de producción completo:

1. **Domain name**: Comprar dominio y configurar DNS
2. **HTTPS**: Usar Let's Encrypt + Nginx para SSL
3. **Application Load Balancer**: Para escalabilidad
4. **CloudWatch**: Configurar monitoring y alertas
5. **Backups**: Configurar automated backups de RDS
6. **CI/CD**: GitHub Actions para auto-deployment

## Soporte

Si algo no funciona:
1. Revisa logs: `docker compose logs`
2. Verifica security groups en AWS Console
3. Revisa user data logs: `/var/log/user-data.log`
