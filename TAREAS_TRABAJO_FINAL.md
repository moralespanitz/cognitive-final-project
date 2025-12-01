# TaxiWatch - Tareas para Trabajo Final

**Proyecto:** TaxiWatch - Sistema de Monitoreo de Flota de Taxis con IA
**Stack Actual:** Django 5.2 + Next.js 16 + PostgreSQL + Redis + Celery
**Fecha:** Noviembre 2024

---

## Resumen del Estado Actual

### ✅ Implementado y Funcionando
- Autenticación JWT (login, registro, refresh tokens)
- CRUD de Usuarios con roles (Admin, Fleet Manager, Dispatcher, Operator)
- CRUD de Vehículos, Conductores y Viajes
- Modelos de base de datos completos
- Configuración Docker Compose (PostgreSQL, Redis, Celery Worker/Beat)
- Django Admin configurado para todos los modelos

### 🟡 Parcialmente Implementado (Modelos + Serializers, sin Views)
- Tracking GPS
- Gestión de Video
- Incidentes y Alertas
- Reportes

### ❌ No Implementado
- Frontend completo (solo template Next.js default)
- Tareas Celery
- WebSocket consumers
- Integración OpenAI/Chatbot
- Hardware (sensores, dispositivos)

---

## TAREAS PENDIENTES

### 1. FUNCIONALIDAD ROL CLIENTE (3 puntos)

#### 1.1 Frontend - Autenticación
- [ ] **Página de Login** (`/ui/app/login/page.tsx`)
  - Formulario email/contraseña
  - Integración con `POST /api/v1/auth/login/`
  - Almacenamiento de tokens (localStorage o cookies)
  - Redirección post-login según rol

- [ ] **Página de Registro** (`/ui/app/register/page.tsx`)
  - Formulario de registro
  - Integración con `POST /api/v1/users/`
  - Validaciones en frontend

- [ ] **Recuperación de Contraseña** (Backend + Frontend)
  - Backend: Endpoint `POST /api/v1/auth/password-reset/`
  - Backend: Endpoint `POST /api/v1/auth/password-reset-confirm/`
  - Frontend: Páginas de recuperación

#### 1.2 Frontend - Dashboard Cliente
- [ ] **Layout Principal** (`/ui/app/(dashboard)/layout.tsx`)
  - Sidebar con navegación
  - Header con info de usuario
  - Protección de rutas (middleware)

- [ ] **Dashboard Home** (`/ui/app/(dashboard)/page.tsx`)
  - Métricas básicas (vehículos activos, viajes hoy, alertas)
  - Mapa con ubicación de vehículos
  - Feed de alertas recientes

#### 1.3 Frontend - Flujo Principal (Monitoreo de Flota)
- [ ] **Vista de Mapa en Tiempo Real** (`/ui/app/(dashboard)/map/page.tsx`)
  - Integración Mapbox/Google Maps
  - Marcadores de vehículos con estado (colores)
  - WebSocket para actualizaciones en tiempo real
  - Click en vehículo → ver detalles

- [ ] **Lista de Vehículos** (`/ui/app/(dashboard)/vehicles/page.tsx`)
  - Tabla con filtros (estado, conductor)
  - Búsqueda
  - Ver detalles de vehículo

- [ ] **Detalle de Vehículo** (`/ui/app/(dashboard)/vehicles/[id]/page.tsx`)
  - Info del vehículo y conductor
  - Historial de viajes
  - Ubicación actual
  - Stream de video (si disponible)

#### 1.4 Frontend - Visualización de Datos del Hardware
- [ ] **Panel de Métricas GPS**
  - Velocidad actual
  - Historial de ruta (playback)
  - Alertas de velocidad

- [ ] **Vista de Video en Vivo**
  - Player de video (HLS.js)
  - Múltiples cámaras (grid view)
  - Captura de snapshot

#### 1.5 Frontend - Chat con IA
- [ ] **Página de Chatbot** (`/ui/app/(dashboard)/chat/page.tsx`)
  - Interface de chat
  - Historial de conversación
  - Integración con endpoint de IA

---

### 2. FUNCIONALIDAD ROL ADMIN (3 puntos)

#### 2.1 Panel de Administración
- [ ] **Dashboard Admin** (`/ui/app/(dashboard)/admin/page.tsx`)
  - Métricas globales de la flota
  - Gráficos de rendimiento
  - Resumen de incidentes

#### 2.2 Gestión de Usuarios/Clientes
- [ ] **Lista de Usuarios** (`/ui/app/(dashboard)/admin/users/page.tsx`)
  - Tabla con todos los usuarios
  - Filtros por rol, estado
  - Acciones: bloquear, activar, reset password

- [ ] **Crear/Editar Usuario**
  - Formulario completo
  - Asignación de roles

- [ ] **Backend: Bloquear Usuario**
  - Endpoint `POST /api/v1/users/{id}/block/`
  - Endpoint `POST /api/v1/users/{id}/unblock/`

- [ ] **Backend: Reset Password por Admin**
  - Endpoint `POST /api/v1/users/{id}/admin-reset-password/`

#### 2.3 Gestión de Dispositivos/Hardware
- [ ] **Lista de Dispositivos** (`/ui/app/(dashboard)/admin/devices/page.tsx`)
  - Estado de conexión (online/offline)
  - Última comunicación
  - Logs de actividad

- [ ] **Backend: Modelo Device** (`/core/tracking/models.py`)
  ```python
  class Device(models.Model):
      vehicle = models.ForeignKey(Vehicle)
      device_type = models.CharField()  # GPS, CAMERA, SENSOR
      serial_number = models.CharField()
      status = models.CharField()  # ONLINE, OFFLINE, ERROR
      last_ping = models.DateTimeField()
      config = models.JSONField()
  ```

- [ ] **Backend: DeviceViewSet** con CRUD + estado

#### 2.4 Configuración del Chatbot/IA
- [ ] **Panel de Config IA** (`/ui/app/(dashboard)/admin/ai-config/page.tsx`)
  - Cargar/editar FAQs
  - Ver historial de conversaciones
  - Métricas de uso

- [ ] **Backend: Modelo FAQ** (`/core/incidents/models.py` o nueva app)
  ```python
  class FAQ(models.Model):
      question = models.TextField()
      answer = models.TextField()
      category = models.CharField()
      is_active = models.BooleanField()
  ```

---

### 3. INTEGRACIÓN DE HARDWARE (3 puntos)

#### 3.1 Simulador de Dispositivo GPS (para desarrollo/demo)
- [ ] **Script Python** (`/hardware/gps_simulator.py`)
  - Simula envío de coordenadas GPS
  - Ruta predefinida o aleatoria
  - Envía datos cada 5-10 segundos
  - Usa HTTP POST a `/api/v1/tracking/location/`

#### 3.2 Backend - Endpoints de Tracking
- [ ] **Implementar TrackingViewSet** (`/core/tracking/views.py`)
  ```python
  class GPS_LocationViewSet(viewsets.ModelViewSet):
      # POST /api/v1/tracking/location/ - Recibir ubicación
      # GET /api/v1/tracking/vehicles/live/ - Ubicaciones en vivo
      # GET /api/v1/tracking/vehicles/{id}/history/ - Historial
  ```

- [ ] **Activar rutas en urls.py**
  - Descomentar `path('api/v1/tracking/', include('tracking.urls'))`

#### 3.3 WebSocket para Tiempo Real
- [ ] **TrackingConsumer** (`/core/tracking/consumers.py`)
  ```python
  class TrackingConsumer(AsyncWebsocketConsumer):
      # Broadcast ubicaciones a clientes conectados
      # Grupos por vehicle_id o "all_vehicles"
  ```

- [ ] **Activar en routing.py**

#### 3.4 Hardware Real (ESP32/Arduino) - Opcional para Demo
- [ ] **Firmware ESP32** (`/hardware/esp32_gps/`)
  - Lee GPS (módulo NEO-6M)
  - Envía por WiFi HTTP/MQTT
  - LED de estado

- [ ] **Alternativa: Raspberry Pi con Cámara**
  - Script Python para captura
  - Streaming RTSP/HLS
  - Envío de frames para análisis IA

---

### 4. MÓDULO DE IA (2 puntos)

#### 4.1 Chatbot con OpenAI
- [ ] **Servicio de Chat** (`/core/incidents/services/chat_service.py`)
  ```python
  class ChatService:
      def __init__(self):
          self.client = OpenAI()

      def get_response(self, user_message, context=None):
          # Cargar FAQs del sistema
          # Construir prompt con contexto
          # Llamar a OpenAI API
          # Retornar respuesta
  ```

- [ ] **Endpoint de Chat** (`/core/incidents/views.py`)
  ```python
  @api_view(['POST'])
  def chat(request):
      message = request.data.get('message')
      response = chat_service.get_response(message)
      return Response({'response': response})
  ```

- [ ] **Modelo ChatHistory** para guardar conversaciones

#### 4.2 Análisis de Incidentes con Vision API
- [ ] **Servicio de Análisis** (`/core/incidents/services/vision_service.py`)
  ```python
  class VisionService:
      def analyze_frame(self, image_base64):
          # Llamar OpenAI Vision API
          # Detectar incidentes
          # Retornar tipo, severidad, descripción
  ```

- [ ] **Tarea Celery para Análisis**
  ```python
  @shared_task
  def analyze_video_frame(frame_id):
      # Obtener frame
      # Analizar con Vision API
      # Crear Incident si detectado
      # Crear Alert
  ```

#### 4.3 Generación de Resúmenes
- [ ] **Generar AI Summary para Incidentes**
  - Al crear incidente, generar resumen automático
  - Campo `ai_summary` en modelo Incident ya existe

---

### 5. BASE DE DATOS (2 puntos)

#### 5.1 Completar Migraciones
- [ ] Agregar modelo `Device` (tracking)
- [ ] Agregar modelo `FAQ` (IA)
- [ ] Agregar modelo `ChatHistory` (IA)
- [ ] Ejecutar `makemigrations` y `migrate`

#### 5.2 Script de Datos de Prueba
- [ ] **Crear script** (`/core/scripts/seed_data.py`)
  - Usuarios de ejemplo (1 admin, 2 fleet managers, 5 operators)
  - 10 vehículos con diferentes estados
  - 5 conductores
  - Historial de viajes (últimos 7 días)
  - Incidentes de ejemplo
  - FAQs para el chatbot

#### 5.3 Índices y Optimización
- [ ] Índice en `GPS_Location.timestamp`
- [ ] Índice en `GPS_Location.vehicle_id`
- [ ] Índice en `Incident.detected_at`
- [ ] Índice en `Alert.created_at`

---

### 6. DESPLIEGUE EN AWS (2 puntos)

#### 6.1 Infraestructura
- [ ] **RDS PostgreSQL**
  - Crear instancia db.t3.micro
  - Configurar security groups
  - Crear base de datos `taxiwatch`

- [ ] **ElastiCache Redis**
  - Cluster para Celery broker
  - Cluster para cache/channels

- [ ] **EC2 o ECS Fargate**
  - Desplegar backend Django
  - Configurar nginx + gunicorn
  - Desplegar Celery worker/beat

- [ ] **S3**
  - Bucket para videos
  - Bucket para archivos estáticos

- [ ] **CloudFront** (opcional)
  - CDN para frontend y videos

#### 6.2 CI/CD
- [ ] **GitHub Actions** (`.github/workflows/deploy.yml`)
  - Build Docker images
  - Push a ECR
  - Deploy a ECS/EC2

#### 6.3 Configuración de Producción
- [ ] **Variables de entorno en AWS**
  - Secrets Manager para API keys
  - Parameter Store para config

- [ ] **Logs y Monitoreo**
  - CloudWatch Logs
  - Alarmas básicas (CPU, memoria, errores 5xx)

- [ ] **Endpoint de Health**
  - `GET /api/v1/health/` → `{"status": "ok"}`

---

### 7. DOCUMENTACIÓN (2 puntos)

#### 7.1 Informe Técnico (PDF)
- [ ] Portada con nombre del proyecto, integrantes, fecha
- [ ] Resumen ejecutivo (1 página)
- [ ] Problema y objetivos
- [ ] Arquitectura del sistema (diagrama)
- [ ] Diagrama de despliegue AWS
- [ ] Modelo Entidad-Relación (MER)
- [ ] Descripción del módulo de IA
- [ ] Guía de despliegue paso a paso
- [ ] Estimación de costos AWS (mensual)
- [ ] Trabajo futuro y lecciones aprendidas

#### 7.2 Manual de Usuario (PDF)
- [ ] Guía para rol Cliente (con capturas)
- [ ] Guía para rol Admin (con capturas)
- [ ] Preguntas frecuentes

#### 7.3 Documentación Técnica
- [ ] Actualizar CLAUDE.md con nuevas features
- [ ] README.md con instrucciones de instalación
- [ ] Documentar API endpoints (Swagger/OpenAPI)

---

### 8. PRESENTACIÓN Y DEMO (3 puntos)

#### 8.1 Presentación (10-12 slides)
- [ ] Slide 1: Título y equipo
- [ ] Slide 2: Problema y solución
- [ ] Slide 3: Arquitectura del sistema
- [ ] Slide 4: Stack tecnológico
- [ ] Slide 5: Funcionalidades Cliente
- [ ] Slide 6: Funcionalidades Admin
- [ ] Slide 7: Integración Hardware
- [ ] Slide 8: Módulo de IA
- [ ] Slide 9: Despliegue AWS
- [ ] Slide 10: Demo (screenshots/GIFs)
- [ ] Slide 11: Lecciones aprendidas
- [ ] Slide 12: Preguntas

#### 8.2 Video Demo (5-8 min)
- [ ] Intro del proyecto (30 seg)
- [ ] Recorrido rol Cliente (2 min)
  - Login
  - Dashboard
  - Mapa en tiempo real
  - Chat con IA
- [ ] Recorrido rol Admin (2 min)
  - Panel de métricas
  - Gestión de usuarios
  - Gestión de dispositivos
  - Config de IA
- [ ] Hardware funcionando (1 min)
  - Dispositivo enviando datos
  - Actualización en tiempo real
- [ ] IA en acción (1 min)
  - Chatbot respondiendo
  - Detección de incidente
- [ ] Evidencia AWS (30 seg)
  - URL pública funcionando
  - Consola AWS

#### 8.3 Entregables Finales
- [ ] URL pública de la app
- [ ] URL del endpoint `/health`
- [ ] Repositorio con tag `v1.0`
- [ ] Video en YouTube/Drive

---

## CRONOGRAMA SUGERIDO

| Semana | Tareas Principales |
|--------|-------------------|
| 1 | Frontend Auth + Layout + Dashboard básico |
| 2 | Frontend Mapa + Lista Vehículos + WebSocket |
| 3 | Panel Admin + Gestión Usuarios + Dispositivos |
| 4 | Hardware (simulador + endpoints tracking) |
| 5 | Módulo IA (Chatbot + Vision API) |
| 6 | Despliegue AWS + CI/CD |
| 7 | Documentación + Presentación + Video |

---

## PRIORIZACIÓN (MVP)

### Crítico (Sin esto no funciona la demo)
1. Frontend Login/Register
2. Frontend Dashboard con mapa
3. WebSocket para tracking en tiempo real
4. Simulador GPS (hardware)
5. Chatbot básico
6. Despliegue en AWS con URL pública

### Importante (Para buena nota)
1. Panel Admin completo
2. Gestión de dispositivos
3. Vision API para detección de incidentes
4. Documentación completa
5. Video demo profesional

### Nice to Have (Si hay tiempo)
1. Hardware real (ESP32)
2. Streaming de video en vivo
3. Reportes con gráficos
4. Notificaciones push
5. App móvil

---

## NOTAS TÉCNICAS

### Configuración de API Client (Frontend)
```typescript
// /ui/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchWithAuth(endpoint: string, options = {}) {
  const token = localStorage.getItem('access_token');
  return fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
      ...options.headers,
    },
  });
}
```

### WebSocket Connection (Frontend)
```typescript
// /ui/lib/websocket.ts
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function connectTracking(onMessage: (data: any) => void) {
  const ws = new WebSocket(`${WS_BASE}/ws/tracking/`);
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  return ws;
}
```

### OpenAI Integration (Backend)
```python
# /core/incidents/services/openai_service.py
from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_chat_response(message: str, system_prompt: str = None) -> str:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt or "Eres un asistente de TaxiWatch..."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content
```
