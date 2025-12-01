# Plan de Validación - TaxiWatch

## Objetivo
Validar todas las funcionalidades localmente antes del despliegue en AWS.

---

## FASE 1: CONFIGURACIÓN BASE (Día 1)

### 1.1 Verificar Estado Actual

```bash
# 1. Verificar Docker Compose
cd /Users/moralespanitz/me/lab/cognitive-computing/cognitive-final-project
docker-compose up -d postgres redis

# 2. Verificar conexión PostgreSQL
docker-compose exec postgres psql -U postgres -d taxiwatch -c "\dt"

# 3. Verificar Redis
docker-compose exec redis redis-cli ping
# Debe retornar: PONG

# 4. Backend - Migraciones
cd core
uv run python manage.py migrate

# 5. Crear superuser
uv run python manage.py createsuperuser
# Username: admin
# Email: admin@taxiwatch.com
# Password: Admin123!

# 6. Levantar backend
uv run python manage.py runserver
# Abrir: http://localhost:8000/admin/
# Login con credenciales creadas
```

**✅ Checklist:**
- [ ] PostgreSQL corriendo y accesible
- [ ] Redis corriendo
- [ ] Migraciones ejecutadas sin errores
- [ ] Django Admin accesible
- [ ] Superuser creado

---

## FASE 2: IMPLEMENTAR ENDPOINTS FALTANTES (Días 2-3)

### 2.1 Tracking GPS

**Archivo:** `/core/tracking/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from .models import GPS_Location
from .serializers import (
    GPS_LocationSerializer,
    GPS_LocationCreateSerializer,
    LiveLocationSerializer
)
from vehicles.models import Vehicle


class GPS_LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de ubicaciones GPS.
    """
    queryset = GPS_Location.objects.all()
    serializer_class = GPS_LocationSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return GPS_LocationCreateSerializer
        return GPS_LocationSerializer

    def get_permissions(self):
        # Permitir POST sin auth para dispositivos ESP32
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def live(self, request):
        """
        Obtener ubicaciones en vivo de todos los vehículos activos.
        GET /api/v1/tracking/live/
        """
        # Últimas ubicaciones (últimos 30 segundos)
        cutoff_time = timezone.now() - timedelta(seconds=30)

        # Obtener la última ubicación de cada vehículo
        from django.db.models import Max
        latest_locations = GPS_Location.objects.filter(
            timestamp__gte=cutoff_time
        ).values('vehicle_id').annotate(
            latest_timestamp=Max('timestamp')
        )

        location_ids = []
        for loc in latest_locations:
            location_ids.append(
                GPS_Location.objects.filter(
                    vehicle_id=loc['vehicle_id'],
                    timestamp=loc['latest_timestamp']
                ).first().id
            )

        locations = GPS_Location.objects.filter(id__in=location_ids)
        serializer = LiveLocationSerializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='vehicle/(?P<vehicle_id>[^/.]+)/history')
    def vehicle_history(self, request, vehicle_id=None):
        """
        Obtener historial de ubicaciones de un vehículo.
        GET /api/v1/tracking/vehicle/{vehicle_id}/history/?hours=24
        """
        hours = int(request.query_params.get('hours', 24))
        cutoff_time = timezone.now() - timedelta(hours=hours)

        locations = GPS_Location.objects.filter(
            vehicle_id=vehicle_id,
            timestamp__gte=cutoff_time
        ).order_by('-timestamp')

        serializer = GPS_LocationSerializer(locations, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])  # Para ESP32
def receive_location(request):
    """
    Endpoint simplificado para recibir ubicación desde ESP32.
    POST /api/v1/tracking/location/

    Body:
    {
        "device_id": "ESP32_001",
        "vehicle_id": 1,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "speed": 45.5,
        "heading": 180,
        "accuracy": 10.0
    }
    """
    serializer = GPS_LocationCreateSerializer(data=request.data)
    if serializer.is_valid():
        location = serializer.save()

        # Opcional: Broadcast via WebSocket (implementar después)
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     'tracking',
        #     {
        #         'type': 'location_update',
        #         'location': GPS_LocationSerializer(location).data
        #     }
        # )

        return Response(
            GPS_LocationSerializer(location).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

**Archivo:** `/core/tracking/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'locations', views.GPS_LocationViewSet, basename='gps-location')

urlpatterns = [
    path('', include(router.urls)),
    path('location/', views.receive_location, name='receive-location'),
]
```

**Activar en:** `/core/taxiwatch/urls.py`

```python
# Descomentar:
path('api/v1/tracking/', include('tracking.urls')),
```

**✅ Validación:**

```bash
# 1. Reiniciar servidor Django
uv run python manage.py runserver

# 2. Test endpoint (crear ubicación)
curl -X POST http://localhost:8000/api/v1/tracking/location/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_001",
    "vehicle_id": 1,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "speed": 45.5,
    "heading": 180,
    "accuracy": 10.0
  }'

# 3. Test endpoint (obtener ubicaciones en vivo)
# Necesitas token JWT primero
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!"
  }'

# Copiar el "access" token y usarlo:
curl http://localhost:8000/api/v1/tracking/live/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 2.2 Video Management

**Archivo:** `/core/video/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.files.base import ContentFile
from django.utils import timezone
import base64
import uuid
from .models import VideoStream, VideoArchive
from .serializers import (
    VideoStreamSerializer,
    VideoStreamCreateSerializer,
    VideoArchiveSerializer,
    VideoArchiveListSerializer
)


class VideoStreamViewSet(viewsets.ModelViewSet):
    queryset = VideoStream.objects.all()
    serializer_class = VideoStreamSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return VideoStreamCreateSerializer
        return VideoStreamSerializer

    @action(detail=False, methods=['get'], url_path='vehicle/(?P<vehicle_id>[^/.]+)')
    def by_vehicle(self, request, vehicle_id=None):
        """
        Obtener streams activos de un vehículo.
        GET /api/v1/video/streams/vehicle/{vehicle_id}/
        """
        streams = self.queryset.filter(
            vehicle_id=vehicle_id,
            status=VideoStream.Status.ACTIVE
        )
        serializer = self.get_serializer(streams, many=True)
        return Response(serializer.data)


class VideoArchiveViewSet(viewsets.ModelViewSet):
    queryset = VideoArchive.objects.all()
    serializer_class = VideoArchiveSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return VideoArchiveListSerializer
        return VideoArchiveSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        vehicle_id = self.request.query_params.get('vehicle_id')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        return queryset


@api_view(['POST'])
@permission_classes([AllowAny])  # Para ESP32
def upload_frame(request):
    """
    Endpoint para recibir frames desde ESP32.
    POST /api/v1/video/frames/upload/

    Body (JSON):
    {
        "device_id": "ESP32_001",
        "vehicle_id": 1,
        "frame_base64": "iVBORw0KGgoAAAANSUhEUg...",
        "camera_position": "FRONT"
    }

    OR (multipart/form-data):
    - device_id: ESP32_001
    - vehicle_id: 1
    - frame: <file>
    - camera_position: FRONT
    """
    device_id = request.data.get('device_id')
    vehicle_id = request.data.get('vehicle_id')
    camera_position = request.data.get('camera_position', 'FRONT')

    # Opción 1: Base64
    if 'frame_base64' in request.data:
        frame_data = request.data.get('frame_base64')
        try:
            # Decodificar base64
            image_data = base64.b64decode(frame_data)
            file_name = f"frame_{vehicle_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.jpg"

            # Crear VideoArchive
            archive = VideoArchive.objects.create(
                vehicle_id=vehicle_id,
                camera_position=camera_position,
                duration=0,  # Frame único
                file_size=len(image_data),
                metadata={
                    'device_id': device_id,
                    'type': 'frame',
                    'timestamp': timezone.now().isoformat()
                }
            )

            # Guardar archivo
            archive.file_path.save(file_name, ContentFile(image_data))

            # TODO: Enqueue para análisis de IA
            # from incidents.tasks import analyze_frame
            # analyze_frame.delay(archive.id)

            return Response({
                'id': archive.id,
                'file_url': request.build_absolute_uri(archive.file_path.url) if archive.file_path else None,
                'message': 'Frame uploaded successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Failed to decode frame: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Opción 2: Multipart file upload
    elif 'frame' in request.FILES:
        frame_file = request.FILES['frame']

        archive = VideoArchive.objects.create(
            vehicle_id=vehicle_id,
            camera_position=camera_position,
            file_path=frame_file,
            duration=0,
            file_size=frame_file.size,
            metadata={
                'device_id': device_id,
                'type': 'frame',
                'timestamp': timezone.now().isoformat()
            }
        )

        return Response({
            'id': archive.id,
            'file_url': request.build_absolute_uri(archive.file_path.url),
            'message': 'Frame uploaded successfully'
        }, status=status.HTTP_201_CREATED)

    else:
        return Response(
            {'error': 'No frame data provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
```

**Archivo:** `/core/video/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'streams', views.VideoStreamViewSet, basename='video-stream')
router.register(r'archives', views.VideoArchiveViewSet, basename='video-archive')

urlpatterns = [
    path('', include(router.urls)),
    path('frames/upload/', views.upload_frame, name='upload-frame'),
]
```

**Activar en:** `/core/taxiwatch/urls.py`

```python
path('api/v1/video/', include('video.urls')),
```

**✅ Validación:**

```bash
# Test upload de frame (base64)
curl -X POST http://localhost:8000/api/v1/video/frames/upload/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ESP32_001",
    "vehicle_id": 1,
    "camera_position": "FRONT",
    "frame_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
  }'

# Listar archives
curl http://localhost:8000/api/v1/video/archives/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 2.3 Incidents & Alerts

**Archivo:** `/core/incidents/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Incident, Alert
from .serializers import (
    IncidentSerializer,
    IncidentListSerializer,
    AlertSerializer,
    AlertListSerializer,
    AlertAcknowledgeSerializer
)


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return IncidentListSerializer
        return IncidentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros
        vehicle_id = self.request.query_params.get('vehicle_id')
        driver_id = self.request.query_params.get('driver_id')
        severity = self.request.query_params.get('severity')
        incident_type = self.request.query_params.get('type')

        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        if severity:
            queryset = queryset.filter(severity=severity)
        if incident_type:
            queryset = queryset.filter(type=incident_type)

        return queryset

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Resolver un incidente.
        POST /api/v1/incidents/{id}/resolve/
        """
        incident = self.get_object()
        incident.resolved_at = timezone.now()
        incident.resolved_by = request.user
        incident.resolution_notes = request.data.get('notes', '')
        incident.save()

        serializer = self.get_serializer(incident)
        return Response(serializer.data)


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return AlertListSerializer
        elif self.action == 'acknowledge':
            return AlertAcknowledgeSerializer
        return AlertSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar solo no reconocidas si se solicita
        unacknowledged = self.request.query_params.get('unacknowledged')
        if unacknowledged == 'true':
            queryset = queryset.filter(acknowledged=False)

        return queryset

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        Reconocer una alerta.
        POST /api/v1/alerts/{id}/acknowledge/
        """
        alert = self.get_object()
        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()

        serializer = self.get_serializer(alert)
        return Response(serializer.data)
```

**Archivo:** `/core/incidents/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'incidents', views.IncidentViewSet, basename='incident')
router.register(r'alerts', views.AlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Activar en:** `/core/taxiwatch/urls.py`

```python
path('api/v1/', include('incidents.urls')),
```

---

## FASE 3: MÓDULO DE IA (Días 4-5)

### 3.1 Servicio de Chatbot

**Archivo:** `/core/incidents/services/__init__.py`

```python
# Vacío, solo para hacer el directorio un paquete Python
```

**Archivo:** `/core/incidents/services/chat_service.py`

```python
from openai import OpenAI
from django.conf import settings
from typing import Optional, Dict
from accounts.models import User
from vehicles.models import Vehicle, Driver
from incidents.models import Incident


class ChatService:
    """
    Servicio para manejar conversaciones con el chatbot usando OpenAI.
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4"

    def _build_context(self, user: User) -> str:
        """
        Construir contexto del sistema basado en datos del usuario.
        """
        # Obtener estadísticas
        total_vehicles = Vehicle.objects.count()
        active_vehicles = Vehicle.objects.filter(status=Vehicle.Status.ACTIVE).count()
        total_drivers = Driver.objects.count()
        on_duty_drivers = Driver.objects.filter(status=Driver.Status.ON_DUTY).count()

        # Incidentes recientes
        from datetime import timedelta
        from django.utils import timezone
        recent_incidents = Incident.objects.filter(
            detected_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        context = f"""
Eres el asistente virtual de TaxiWatch, un sistema de monitoreo de flotas de taxis.

Información actual del sistema:
- Total de vehículos: {total_vehicles}
- Vehículos activos: {active_vehicles}
- Total de conductores: {total_drivers}
- Conductores en servicio: {on_duty_drivers}
- Incidentes en los últimos 7 días: {recent_incidents}

Usuario actual:
- Nombre: {user.get_full_name() or user.username}
- Rol: {user.get_role_display()}

Puedes ayudar con:
1. Consultas sobre el estado de la flota
2. Información sobre vehículos y conductores
3. Explicación de incidentes y alertas
4. Guía sobre cómo usar el sistema
5. Recomendaciones de seguridad

Responde de manera concisa y profesional. Si no tienes información exacta,
indica que el usuario puede consultar directamente en el panel correspondiente.
"""
        return context

    def get_response(
        self,
        user_message: str,
        user: Optional[User] = None,
        conversation_history: Optional[list] = None
    ) -> Dict[str, str]:
        """
        Obtener respuesta del chatbot.

        Args:
            user_message: Mensaje del usuario
            user: Usuario que envía el mensaje (para contexto)
            conversation_history: Historial de conversación previa

        Returns:
            Dict con 'response' y 'usage'
        """
        try:
            # Construir mensajes
            messages = []

            # Sistema (contexto)
            if user:
                system_context = self._build_context(user)
            else:
                system_context = "Eres el asistente virtual de TaxiWatch, un sistema de monitoreo de flotas de taxis."

            messages.append({
                "role": "system",
                "content": system_context
            })

            # Historial previo (si existe)
            if conversation_history:
                messages.extend(conversation_history)

            # Mensaje actual
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Llamar a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            assistant_message = response.choices[0].message.content
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }

            return {
                'response': assistant_message,
                'usage': usage
            }

        except Exception as e:
            return {
                'response': f"Lo siento, ocurrió un error al procesar tu mensaje: {str(e)}",
                'usage': {}
            }


# Instancia global del servicio
chat_service = ChatService()
```

**Archivo:** `/core/incidents/models.py` (agregar modelo ChatHistory)

```python
# Agregar al final del archivo:

class ChatHistory(models.Model):
    """
    Historial de conversaciones del chatbot.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_history'
    )
    session_id = models.UUIDField(
        default=uuid.uuid4,
        help_text='ID de sesión de conversación'
    )
    message = models.TextField(
        help_text='Mensaje del usuario'
    )
    response = models.TextField(
        help_text='Respuesta del chatbot'
    )
    tokens_used = models.IntegerField(
        default=0,
        help_text='Tokens usados en esta interacción'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


import uuid  # Agregar al inicio del archivo
```

**Crear migración:**

```bash
cd core
uv run python manage.py makemigrations incidents
uv run python manage.py migrate
```

**Archivo:** `/core/incidents/views.py` (agregar endpoint de chat)

```python
# Agregar al final del archivo:

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .services.chat_service import chat_service
from .models import ChatHistory
import uuid as uuid_module


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    Endpoint de chat con IA.
    POST /api/v1/chat/

    Body:
    {
        "message": "¿Cuántos vehículos tengo activos?",
        "session_id": "uuid-opcional"
    }
    """
    message = request.data.get('message')
    session_id = request.data.get('session_id')

    if not message:
        return Response(
            {'error': 'Message is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generar session_id si no existe
    if not session_id:
        session_id = str(uuid_module.uuid4())

    # Obtener historial de la sesión (últimos 10 mensajes)
    history = ChatHistory.objects.filter(
        user=request.user,
        session_id=session_id
    ).order_by('-created_at')[:10]

    # Convertir a formato OpenAI
    conversation_history = []
    for h in reversed(history):  # Orden cronológico
        conversation_history.append({"role": "user", "content": h.message})
        conversation_history.append({"role": "assistant", "content": h.response})

    # Obtener respuesta
    result = chat_service.get_response(
        user_message=message,
        user=request.user,
        conversation_history=conversation_history
    )

    # Guardar en historial
    ChatHistory.objects.create(
        user=request.user,
        session_id=session_id,
        message=message,
        response=result['response'],
        tokens_used=result.get('usage', {}).get('total_tokens', 0)
    )

    return Response({
        'response': result['response'],
        'session_id': session_id,
        'usage': result.get('usage', {})
    })
```

**Actualizar:** `/core/incidents/urls.py`

```python
urlpatterns = [
    path('', include(router.urls)),
    path('chat/', views.chat, name='chat'),  # Agregar esta línea
]
```

**✅ Validación:**

```bash
# Test chatbot
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, ¿cuántos vehículos activos tengo?"
  }'
```

---

## FASE 4: SCRIPT DE DATOS DE PRUEBA (Día 6)

**Archivo:** `/core/scripts/seed_data.py`

```python
"""
Script para poblar la base de datos con datos de prueba.
Ejecutar: uv run python scripts/seed_data.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxiwatch.settings')
django.setup()

from django.contrib.auth import get_user_model
from vehicles.models import Driver, Vehicle, Trip
from tracking.models import GPS_Location
from incidents.models import Incident, Alert
from datetime import datetime, timedelta
from django.utils import timezone
import random

User = get_user_model()


def create_users():
    """Crear usuarios de ejemplo"""
    print("Creando usuarios...")

    # Admin (si no existe)
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@taxiwatch.com',
            password='Admin123!',
            role=User.Role.ADMIN,
            first_name='Admin',
            last_name='User'
        )

    # Fleet Managers
    for i in range(1, 3):
        User.objects.get_or_create(
            username=f'manager{i}',
            defaults={
                'email': f'manager{i}@taxiwatch.com',
                'role': User.Role.FLEET_MANAGER,
                'first_name': f'Manager',
                'last_name': f'{i}'
            }
        )

    # Dispatchers
    for i in range(1, 3):
        User.objects.get_or_create(
            username=f'dispatcher{i}',
            defaults={
                'email': f'dispatcher{i}@taxiwatch.com',
                'role': User.Role.DISPATCHER,
                'first_name': f'Dispatcher',
                'last_name': f'{i}'
            }
        )

    # Operators (drivers)
    for i in range(1, 11):
        User.objects.get_or_create(
            username=f'driver{i}',
            defaults={
                'email': f'driver{i}@taxiwatch.com',
                'role': User.Role.OPERATOR,
                'first_name': f'Driver',
                'last_name': f'{i}'
            }
        )

    print(f"✅ Usuarios creados: {User.objects.count()}")


def create_drivers():
    """Crear conductores"""
    print("Creando conductores...")

    driver_users = User.objects.filter(role=User.Role.OPERATOR)

    for i, user in enumerate(driver_users, 1):
        if not hasattr(user, 'driver_profile'):
            Driver.objects.create(
                user=user,
                license_number=f'LIC-{1000 + i}',
                license_expiry=datetime.now().date() + timedelta(days=365 * 2),
                status=random.choice([Driver.Status.ON_DUTY, Driver.Status.OFF_DUTY]),
                rating=round(random.uniform(3.5, 5.0), 2),
                total_trips=random.randint(50, 500)
            )

    print(f"✅ Conductores creados: {Driver.objects.count()}")


def create_vehicles():
    """Crear vehículos"""
    print("Creando vehículos...")

    makes_models = [
        ('Toyota', 'Corolla'),
        ('Honda', 'Civic'),
        ('Ford', 'Focus'),
        ('Chevrolet', 'Cruze'),
        ('Nissan', 'Sentra'),
        ('Hyundai', 'Elantra'),
        ('Mazda', '3'),
        ('Volkswagen', 'Jetta'),
        ('Kia', 'Forte'),
        ('Subaru', 'Impreza'),
    ]

    colors = ['White', 'Black', 'Silver', 'Blue', 'Red', 'Gray']
    drivers = list(Driver.objects.all())

    for i in range(1, 11):
        make, model = makes_models[i-1]

        vehicle, created = Vehicle.objects.get_or_create(
            license_plate=f'ABC-{1000 + i}',
            defaults={
                'make': make,
                'model': model,
                'year': random.randint(2018, 2024),
                'color': random.choice(colors),
                'vin': f'VIN{i:013d}',
                'capacity': 4,
                'status': random.choice([
                    Vehicle.Status.ACTIVE,
                    Vehicle.Status.ACTIVE,
                    Vehicle.Status.ACTIVE,
                    Vehicle.Status.MAINTENANCE
                ]),
                'current_driver': drivers[i-1] if i <= len(drivers) else None,
                'registration_date': datetime.now().date() - timedelta(days=random.randint(100, 1000)),
                'insurance_expiry': datetime.now().date() + timedelta(days=random.randint(30, 365))
            }
        )

    print(f"✅ Vehículos creados: {Vehicle.objects.count()}")


def create_trips():
    """Crear viajes de ejemplo"""
    print("Creando viajes...")

    vehicles = Vehicle.objects.all()

    # Crear viajes de los últimos 7 días
    for vehicle in vehicles:
        if not vehicle.current_driver:
            continue

        for _ in range(random.randint(5, 15)):
            start_time = timezone.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            duration = random.randint(10, 60)  # minutos
            distance = round(random.uniform(2, 25), 2)  # km

            Trip.objects.create(
                vehicle=vehicle,
                driver=vehicle.current_driver,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=duration),
                start_location={
                    'lat': 40.7128 + random.uniform(-0.1, 0.1),
                    'lng': -74.0060 + random.uniform(-0.1, 0.1),
                    'address': f'{random.randint(1, 999)} Main St'
                },
                end_location={
                    'lat': 40.7128 + random.uniform(-0.1, 0.1),
                    'lng': -74.0060 + random.uniform(-0.1, 0.1),
                    'address': f'{random.randint(1, 999)} Broadway'
                },
                distance=distance,
                duration=duration,
                status=Trip.Status.COMPLETED,
                fare=round(distance * 2.5 + 3.5, 2)
            )

    print(f"✅ Viajes creados: {Trip.objects.count()}")


def create_gps_locations():
    """Crear ubicaciones GPS"""
    print("Creando ubicaciones GPS...")

    vehicles = Vehicle.objects.filter(status=Vehicle.Status.ACTIVE)

    # Ubicaciones recientes (últimas 2 horas)
    for vehicle in vehicles:
        for i in range(10):
            timestamp = timezone.now() - timedelta(minutes=i * 5)

            GPS_Location.objects.create(
                vehicle=vehicle,
                latitude=40.7128 + random.uniform(-0.05, 0.05),
                longitude=-74.0060 + random.uniform(-0.05, 0.05),
                speed=random.uniform(0, 60),
                heading=random.randint(0, 359),
                accuracy=random.uniform(5, 15),
                altitude=random.uniform(0, 100),
                timestamp=timestamp
            )

    print(f"✅ Ubicaciones GPS creadas: {GPS_Location.objects.count()}")


def create_incidents():
    """Crear incidentes de ejemplo"""
    print("Creando incidentes...")

    vehicles = Vehicle.objects.all()
    incident_types = [t[0] for t in Incident.IncidentType.choices]
    severities = [s[0] for s in Incident.Severity.choices]

    for _ in range(15):
        vehicle = random.choice(vehicles)
        if not vehicle.current_driver:
            continue

        incident_type = random.choice(incident_types)
        severity = random.choice(severities)

        incident = Incident.objects.create(
            vehicle=vehicle,
            driver=vehicle.current_driver,
            type=incident_type,
            severity=severity,
            description=f"Incident detected: {incident_type}",
            ai_summary=f"AI detected {incident_type.lower()} with {severity.lower()} severity.",
            location={
                'lat': 40.7128 + random.uniform(-0.1, 0.1),
                'lng': -74.0060 + random.uniform(-0.1, 0.1),
                'address': f'{random.randint(1, 999)} Street'
            },
            detected_at=timezone.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23)
            )
        )

        # Crear alerta asociada
        Alert.objects.create(
            incident=incident,
            vehicle=vehicle,
            type=incident_type,
            priority=Alert.Priority.CRITICAL if severity == Incident.Severity.CRITICAL else Alert.Priority.MEDIUM,
            message=f"{incident_type} detected on vehicle {vehicle.license_plate}",
            acknowledged=random.choice([True, False])
        )

    print(f"✅ Incidentes creados: {Incident.objects.count()}")
    print(f"✅ Alertas creadas: {Alert.objects.count()}")


def main():
    """Ejecutar todas las funciones de seed"""
    print("=" * 50)
    print("Iniciando seed de datos de prueba...")
    print("=" * 50)

    create_users()
    create_drivers()
    create_vehicles()
    create_trips()
    create_gps_locations()
    create_incidents()

    print("=" * 50)
    print("✅ Seed completado exitosamente!")
    print("=" * 50)


if __name__ == '__main__':
    main()
```

**✅ Ejecutar seed:**

```bash
cd core
uv run python scripts/seed_data.py
```

---

## FASE 5: SIMULADOR ESP32 (Día 7)

**Archivo:** `/hardware/gps_video_simulator.py`

```python
"""
Simulador de dispositivo ESP32 con GPS y cámara.
Simula envío de ubicaciones GPS y frames de video.
"""

import requests
import time
import base64
import random
import json
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


class ESP32Simulator:
    def __init__(self, device_id, vehicle_id, api_base_url):
        self.device_id = device_id
        self.vehicle_id = vehicle_id
        self.api_base_url = api_base_url

        # Posición inicial (Nueva York)
        self.lat = 40.7128
        self.lng = -74.0060
        self.speed = 0
        self.heading = 0

    def generate_frame(self):
        """Generar frame de ejemplo"""
        # Crear imagen de 640x480 con información
        img = Image.new('RGB', (640, 480), color=(73, 109, 137))
        d = ImageDraw.Draw(img)

        # Texto
        text = f"Vehicle {self.vehicle_id}\n"
        text += f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"Lat: {self.lat:.6f}\n"
        text += f"Lng: {self.lng:.6f}\n"
        text += f"Speed: {self.speed:.1f} km/h"

        d.text((10, 10), text, fill=(255, 255, 0))

        # Convertir a base64
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=70)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return img_str

    def send_location(self):
        """Enviar ubicación GPS"""
        data = {
            "device_id": self.device_id,
            "vehicle_id": self.vehicle_id,
            "latitude": self.lat,
            "longitude": self.lng,
            "speed": self.speed,
            "heading": self.heading,
            "accuracy": random.uniform(5, 15)
        }

        try:
            response = requests.post(
                f"{self.api_base_url}/tracking/location/",
                json=data,
                timeout=5
            )

            if response.status_code == 201:
                print(f"✅ Location sent: {self.lat:.6f}, {self.lng:.6f}")
            else:
                print(f"❌ Location error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Location exception: {e}")

    def send_frame(self):
        """Enviar frame de video"""
        frame_base64 = self.generate_frame()

        data = {
            "device_id": self.device_id,
            "vehicle_id": self.vehicle_id,
            "camera_position": "FRONT",
            "frame_base64": frame_base64
        }

        try:
            response = requests.post(
                f"{self.api_base_url}/video/frames/upload/",
                json=data,
                timeout=10
            )

            if response.status_code == 201:
                print(f"✅ Frame sent")
            else:
                print(f"❌ Frame error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Frame exception: {e}")

    def simulate_movement(self):
        """Simular movimiento del vehículo"""
        # Variar posición (movimiento aleatorio)
        self.lat += random.uniform(-0.001, 0.001)
        self.lng += random.uniform(-0.001, 0.001)

        # Variar velocidad
        if self.speed < 5:
            self.speed = random.uniform(20, 50)
        else:
            self.speed += random.uniform(-5, 5)
            self.speed = max(0, min(self.speed, 60))

        # Variar heading
        self.heading = (self.heading + random.randint(-15, 15)) % 360

    def run(self, interval_gps=10, interval_frame=3):
        """
        Ejecutar simulador.

        Args:
            interval_gps: Intervalo en segundos para enviar GPS (default 10s)
            interval_frame: Intervalo en segundos para enviar frames (default 3s)
        """
        print("=" * 60)
        print(f"🚗 ESP32 Simulator Started")
        print(f"Device ID: {self.device_id}")
        print(f"Vehicle ID: {self.vehicle_id}")
        print(f"API Base URL: {self.api_base_url}")
        print(f"GPS Interval: {interval_gps}s")
        print(f"Frame Interval: {interval_frame}s")
        print("=" * 60)

        last_gps = 0
        last_frame = 0

        try:
            while True:
                current_time = time.time()

                # Enviar GPS
                if current_time - last_gps >= interval_gps:
                    self.send_location()
                    last_gps = current_time

                # Enviar Frame
                if current_time - last_frame >= interval_frame:
                    self.send_frame()
                    last_frame = current_time

                # Simular movimiento
                self.simulate_movement()

                # Esperar 1 segundo
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Simulator stopped by user")
        except Exception as e:
            print(f"\n❌ Simulator error: {e}")


if __name__ == "__main__":
    # Configuración
    DEVICE_ID = "ESP32_SIM_001"
    VEHICLE_ID = 1  # Cambiar según el vehículo que exista en tu BD
    API_BASE_URL = "http://localhost:8000/api/v1"

    # Crear y ejecutar simulador
    simulator = ESP32Simulator(DEVICE_ID, VEHICLE_ID, API_BASE_URL)
    simulator.run(interval_gps=10, interval_frame=3)
```

**Instalar dependencias:**

```bash
pip install pillow requests
```

**✅ Ejecutar simulador:**

```bash
cd hardware
python gps_video_simulator.py
```

Deberías ver output como:
```
✅ Location sent: 40.713500, -74.005800
✅ Frame sent
✅ Location sent: 40.714200, -74.006100
✅ Frame sent
```

---

## CHECKLIST FINAL DE VALIDACIÓN LOCAL

### Backend
- [ ] Todos los endpoints funcionando
- [ ] Chatbot respondiendo correctamente
- [ ] Simulador ESP32 enviando datos
- [ ] Base de datos poblada con datos de prueba
- [ ] Django Admin accesible y funcional

### Próximo Paso
Implementar Frontend Next.js (será el siguiente documento).

¿Procedo con el plan de Frontend?
