"""
Seed FAQs for TaxiWatch AI chatbot.
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.faq import FAQ, FAQCategory


async def seed_faqs():
    """Create initial FAQs for the chatbot."""
    async with AsyncSessionLocal() as db:
        # Check if FAQs already exist
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(FAQ.id)))
        count = result.scalar()

        if count > 0:
            print(f"✓ FAQs already exist ({count} FAQs found)")
            return

        faqs_data = [
            # GENERAL
            {
                "question": "¿Qué es TaxiWatch?",
                "answer": "TaxiWatch es un sistema completo de gestión y monitoreo en tiempo real para flotas de taxis. Integra reservas de viajes, seguimiento GPS, streaming de video en vivo desde dispositivos ESP32-CAM, y gestión centralizada de usuarios y dispositivos.",
                "category": FAQCategory.GENERAL,
                "keywords": "sistema, taxiwatch, qué es, descripción",
                "priority": 100
            },
            {
                "question": "¿Cómo funciona el sistema?",
                "answer": "TaxiWatch utiliza una arquitectura cloud-native con backend FastAPI, frontend Next.js, base de datos PostgreSQL y dispositivos ESP32-CAM instalados en los vehículos. Los clientes pueden reservar taxis a través de la aplicación web, los conductores reciben y gestionan viajes, y los administradores monitorean toda la flota en tiempo real.",
                "category": FAQCategory.GENERAL,
                "keywords": "funcionamiento, cómo funciona, arquitectura",
                "priority": 90
            },
            {
                "question": "¿Qué roles de usuario existen?",
                "answer": "TaxiWatch tiene 4 roles principales: ADMIN (administrador con acceso completo), FLEET_MANAGER (gestor de flota), OPERATOR (conductor), y CUSTOMER (cliente/pasajero). Cada rol tiene permisos y funcionalidades específicas.",
                "category": FAQCategory.GENERAL,
                "keywords": "roles, usuarios, permisos, admin, conductor, cliente",
                "priority": 85
            },

            # TRIPS / RESERVAS
            {
                "question": "¿Cómo reservo un taxi?",
                "answer": "Para reservar un taxi: 1) Ingresa a la aplicación web y haz login, 2) Ve a 'Book Taxi', 3) Ingresa tu ubicación de origen y destino, 4) Revisa la tarifa estimada, 5) Confirma la reserva. El sistema asignará automáticamente el conductor más cercano disponible.",
                "category": FAQCategory.TRIPS,
                "keywords": "reservar, book, taxi, viaje, cómo reservar",
                "priority": 95
            },
            {
                "question": "¿Cómo se calcula la tarifa?",
                "answer": "La tarifa se calcula con la fórmula: Tarifa Base ($2.00) + Distancia en km × $1.50. Por ejemplo, un viaje de 5 km costaría: $2.00 + (5 × $1.50) = $9.50. Esta es una tarifa estimada que se ajusta al finalizar el viaje.",
                "category": FAQCategory.TRIPS,
                "keywords": "tarifa, precio, costo, calcular, cuánto cuesta",
                "priority": 90
            },
            {
                "question": "¿Puedo cancelar un viaje?",
                "answer": "Sí, puedes cancelar un viaje en cualquier momento antes de que finalice. Si eres cliente, contacta al conductor o usa la opción de cancelar en la app. Si eres conductor, usa el botón 'Cancel Trip' en el panel de conductor.",
                "category": FAQCategory.TRIPS,
                "keywords": "cancelar, viaje, trip, cancel",
                "priority": 80
            },
            {
                "question": "¿Cuáles son los estados de un viaje?",
                "answer": "Un viaje pasa por estos estados: REQUESTED (solicitado), ACCEPTED (aceptado por conductor), ARRIVED (conductor llegó al punto de recogida), IN_PROGRESS (viaje en curso), COMPLETED (completado) o CANCELLED (cancelado).",
                "category": FAQCategory.TRIPS,
                "keywords": "estados, viaje, status, trip",
                "priority": 75
            },

            # VEHICLES / VEHÍCULOS
            {
                "question": "¿Cómo registro un vehículo?",
                "answer": "Solo administradores pueden registrar vehículos. Ve a 'Vehicles' → 'Add Vehicle' y completa: placa (license plate), marca (make), modelo (model), año (year), VIN (opcional) y color. Luego puedes asignar un conductor al vehículo.",
                "category": FAQCategory.VEHICLES,
                "keywords": "registrar vehículo, añadir taxi, vehicle",
                "priority": 70
            },
            {
                "question": "¿Cómo funciona el video streaming?",
                "answer": "Cada vehículo tiene un dispositivo ESP32-CAM que captura imágenes cada 3 segundos y las envía al servidor. Los usuarios autorizados pueden ver el stream en tiempo real en el 'Video Monitor' a través de WebSocket. Las imágenes no se almacenan permanentemente por privacidad.",
                "category": FAQCategory.VEHICLES,
                "keywords": "video, cámara, streaming, esp32, monitor",
                "priority": 85
            },

            # DRIVERS / CONDUCTORES
            {
                "question": "¿Cómo acepto un viaje como conductor?",
                "answer": "Cuando un viaje es asignado, aparecerá en tu panel de conductor. Revisa los detalles (cliente, origen, destino, tarifa) y haz click en 'Accept Trip'. El estado cambiará a ACCEPTED y debes navegar al punto de recogida.",
                "category": FAQCategory.DRIVERS,
                "keywords": "aceptar viaje, conductor, driver, accept",
                "priority": 88
            },
            {
                "question": "¿Qué estados de disponibilidad hay para conductores?",
                "answer": "Los conductores tienen 3 estados: ON_DUTY (disponible para recibir viajes), OFF_DUTY (no disponible), y BUSY (en viaje activo). El estado cambia automáticamente a ON_DUTY al hacer login y a BUSY al aceptar un viaje.",
                "category": FAQCategory.DRIVERS,
                "keywords": "estado conductor, disponibilidad, on duty, off duty",
                "priority": 82
            },

            # SYSTEM / SISTEMA
            {
                "question": "¿Cómo accedo al sistema?",
                "answer": "Accede a http://98.92.214.232:3000, ingresa tu username y password, y haz click en Login. Si olvidaste tu contraseña, contacta al administrador. Usuarios de prueba: admin/driver1/customer1 (password: password123).",
                "category": FAQCategory.SYSTEM,
                "keywords": "login, acceso, ingresar, entrar",
                "priority": 92
            },
            {
                "question": "¿El sistema es seguro?",
                "answer": "Sí, TaxiWatch implementa múltiples medidas de seguridad: autenticación JWT con tokens de acceso y refresh, contraseñas hasheadas con bcrypt, validación de entrada con Pydantic, RBAC (control de acceso basado en roles), y las imágenes de video no se almacenan permanentemente.",
                "category": FAQCategory.SYSTEM,
                "keywords": "seguridad, seguro, privacidad, protección",
                "priority": 78
            },
            {
                "question": "¿Puedo usar TaxiWatch desde mi teléfono?",
                "answer": "Sí, TaxiWatch es una aplicación web responsive que funciona en navegadores de escritorio y móviles. Simplemente accede desde el navegador de tu teléfono. Una aplicación móvil nativa está planificada para el futuro.",
                "category": FAQCategory.SYSTEM,
                "keywords": "móvil, celular, teléfono, mobile, app",
                "priority": 73
            },

            # INCIDENTS / INCIDENTES
            {
                "question": "¿Qué pasa si hay un problema durante el viaje?",
                "answer": "Si hay un problema durante el viaje, tanto conductor como pasajero pueden cancelar el viaje. El sistema registra todos los estados del viaje para auditoría. En el futuro, se implementarán alertas automáticas basadas en el análisis de video.",
                "category": FAQCategory.INCIDENTS,
                "keywords": "problema, incidente, emergencia, ayuda",
                "priority": 76
            },

            # TECHNICAL
            {
                "question": "¿Dónde está desplegado el sistema?",
                "answer": "TaxiWatch está desplegado en AWS EC2 (instancia t2.medium en Ubuntu 24.04) usando Docker Compose. La infraestructura incluye PostgreSQL, Redis, Backend FastAPI y Frontend Next.js. La IP pública es 98.92.214.232.",
                "category": FAQCategory.SYSTEM,
                "keywords": "despliegue, aws, servidor, infrastructure",
                "priority": 65
            },
            {
                "question": "¿Qué tecnologías usa TaxiWatch?",
                "answer": "Backend: FastAPI + Python 3.12 + PostgreSQL + Redis. Frontend: Next.js 16 + TypeScript + Tailwind CSS. Hardware: ESP32-CAM. Infraestructura: Docker Compose + AWS EC2. AI: OpenAI GPT-4o-mini para el chatbot.",
                "category": FAQCategory.SYSTEM,
                "keywords": "tecnologías, stack, tech stack",
                "priority": 60
            },
        ]

        # Create FAQs
        for faq_data in faqs_data:
            faq = FAQ(**faq_data)
            db.add(faq)

        await db.commit()
        print(f"✓ Created {len(faqs_data)} FAQs successfully")


if __name__ == "__main__":
    asyncio.run(seed_faqs())
