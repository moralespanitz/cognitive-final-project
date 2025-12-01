#!/usr/bin/env python3
"""
Complete project generator - Creates ALL remaining files.
Run: python scripts/generate_complete_project.py
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

def create_file(filepath: str, content: str):
    """Create a file with given content."""
    file_path = BASE_DIR / filepath
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"✅ {filepath}")

# Store all files to create
FILES = {}

# ============================================================================
# API ROUTERS
# ============================================================================

FILES["backend/app/api/v1/video.py"] = '''"""
Video API endpoints.
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import base64
from datetime import datetime, timedelta

from ...database import get_db
from ...models.user import User
from ...models.video import VideoArchive, VideoStream
from ...models.vehicle import Vehicle
from ...schemas.video import VideoArchiveResponse, FrameUpload
from ...dependencies import get_current_user
from ...core.exceptions import NotFoundException

router = APIRouter()


@router.post("/frames/upload", response_model=VideoArchiveResponse, status_code=201)
async def upload_frame(
    frame_data: FrameUpload,
    db: AsyncSession = Depends(get_db)
):
    """Upload video frame from ESP32 (no auth required for devices)."""
    # Verify vehicle exists
    stmt = select(Vehicle).where(Vehicle.id == frame_data.vehicle_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise NotFoundException(detail="Vehicle not found")

    # Decode base64 frame
    try:
        frame_bytes = base64.b64decode(frame_data.frame_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {str(e)}")

    # Generate filename
    timestamp = datetime.utcnow()
    filename = f"frames/vehicle_{frame_data.vehicle_id}/{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"

    # Save to S3 (or local for development)
    # TODO: Implement S3 upload using boto3
    file_path = filename  # S3 key

    # Create archive record
    archive = VideoArchive(
        vehicle_id=frame_data.vehicle_id,
        camera_position=frame_data.camera_position,
        file_path=file_path,
        file_size=len(frame_bytes),
        duration=0,  # Single frame
        metadata={"device_id": frame_data.device_id, "type": "frame"},
        retention_until=timestamp + timedelta(days=7)
    )

    db.add(archive)
    await db.commit()
    await db.refresh(archive)

    # TODO: Enqueue for AI analysis
    # await enqueue_ai_analysis(archive.id)

    return archive


@router.get("/archives", response_model=List[VideoArchiveResponse])
async def list_video_archives(
    skip: int = 0,
    limit: int = 50,
    vehicle_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List video archives."""
    stmt = select(VideoArchive)

    if vehicle_id:
        stmt = stmt.where(VideoArchive.vehicle_id == vehicle_id)

    stmt = stmt.offset(skip).limit(limit).order_by(VideoArchive.created_at.desc())
    result = await db.execute(stmt)
    archives = result.scalars().all()

    return archives


@router.get("/archives/{archive_id}", response_model=VideoArchiveResponse)
async def get_video_archive(
    archive_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get video archive by ID."""
    stmt = select(VideoArchive).where(VideoArchive.id == archive_id)
    result = await db.execute(stmt)
    archive = result.scalar_one_or_none()

    if not archive:
        raise NotFoundException(detail="Video archive not found")

    return archive
'''

FILES["backend/app/api/v1/incidents.py"] = '''"""
Incidents and Alerts API endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ...database import get_db
from ...models.user import User
from ...models.incident import Incident, Alert
from ...schemas.incident import (
    IncidentCreate, IncidentUpdate, IncidentResponse,
    AlertResponse, AlertAcknowledge
)
from ...dependencies import get_current_user
from ...core.exceptions import NotFoundException

router = APIRouter()


# Incident Endpoints
@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    incident_data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new incident."""
    db_incident = Incident(**incident_data.model_dump())
    db.add(db_incident)
    await db.commit()
    await db.refresh(db_incident)

    return db_incident


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    skip: int = 0,
    limit: int = 50,
    vehicle_id: int = None,
    driver_id: int = None,
    severity: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List incidents with filters."""
    stmt = select(Incident)

    if vehicle_id:
        stmt = stmt.where(Incident.vehicle_id == vehicle_id)
    if driver_id:
        stmt = stmt.where(Incident.driver_id == driver_id)
    if severity:
        stmt = stmt.where(Incident.severity == severity)

    stmt = stmt.offset(skip).limit(limit).order_by(Incident.detected_at.desc())
    result = await db.execute(stmt)
    incidents = result.scalars().all()

    return incidents


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get incident by ID."""
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise NotFoundException(detail="Incident not found")

    return incident


@router.put("/incidents/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: int,
    resolution_notes: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve an incident."""
    stmt = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()

    if not incident:
        raise NotFoundException(detail="Incident not found")

    incident.resolved_at = datetime.utcnow()
    incident.resolved_by_id = current_user.id
    incident.resolution_notes = resolution_notes

    await db.commit()
    await db.refresh(incident)

    return incident


# Alert Endpoints
@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    skip: int = 0,
    limit: int = 50,
    unacknowledged: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List alerts."""
    stmt = select(Alert)

    if unacknowledged:
        stmt = stmt.where(Alert.acknowledged == False)

    stmt = stmt.offset(skip).limit(limit).order_by(Alert.created_at.desc())
    result = await db.execute(stmt)
    alerts = result.scalars().all()

    return alerts


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert."""
    stmt = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise NotFoundException(detail="Alert not found")

    alert.acknowledged = True
    alert.acknowledged_by_id = current_user.id
    alert.acknowledged_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    return alert
'''

# ============================================================================
# SERVICES
# ============================================================================

FILES["backend/app/services/ai_service.py"] = '''"""
AI service for vision analysis using OpenAI.
"""

from openai import OpenAI
from typing import Optional, Dict
from ..config import settings


class AIService:
    """Service for AI-powered incident detection using OpenAI Vision API."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.vision_model = settings.OPENAI_VISION_MODEL

    async def analyze_frame(self, image_base64: str) -> Dict[str, any]:
        """
        Analyze a video frame for incidents.

        Args:
            image_base64: Base64 encoded image

        Returns:
            Dict with incident_detected, type, severity, description, confidence
        """
        try:
            prompt = """
Analyze this image from a taxi camera. Identify any safety concerns or incidents:

- Accidents or collisions
- Harsh braking
- Aggressive driving
- Driver drowsiness or distraction
- Phone usage while driving
- Seatbelt not worn
- Any unusual or dangerous situations

Respond in JSON format:
{
    "incident_detected": true/false,
    "type": "ACCIDENT|HARSH_BRAKING|DROWSINESS|DISTRACTION|PHONE_USAGE|OTHER",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "description": "Brief description",
    "confidence": 0-100
}
"""

            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            # Parse response
            result_text = response.choices[0].message.content

            # Try to parse JSON from response
            import json
            try:
                result = json.loads(result_text)
            except:
                # If not valid JSON, return safe default
                result = {
                    "incident_detected": False,
                    "type": "OTHER",
                    "severity": "LOW",
                    "description": "Could not analyze frame",
                    "confidence": 0
                }

            return result

        except Exception as e:
            print(f"AI analysis error: {str(e)}")
            return {
                "incident_detected": False,
                "type": "OTHER",
                "severity": "LOW",
                "description": f"Error: {str(e)}",
                "confidence": 0
            }


# Global instance
ai_service = AIService()
'''

# ============================================================================
# LAMBDA HANDLERS
# ============================================================================

FILES["backend/app/lambda_handlers/frame_processor.py"] = '''"""
Lambda handler for processing video frames from ESP32.
"""

import json
import base64
import boto3
from datetime import datetime, timedelta

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')


def handler(event, context):
    """
    Process uploaded video frame.

    Event from API Gateway:
    {
        "device_id": "ESP32_001",
        "vehicle_id": 1,
        "camera_position": "FRONT",
        "frame_base64": "..."
    }
    """
    try:
        # Parse body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event

        device_id = body['device_id']
        vehicle_id = body['vehicle_id']
        camera_position = body.get('camera_position', 'FRONT')
        frame_base64 = body['frame_base64']

        # Decode frame
        frame_bytes = base64.b64decode(frame_base64)

        # Generate S3 key
        timestamp = datetime.utcnow()
        s3_key = f"frames/vehicle_{vehicle_id}/{timestamp.strftime('%Y/%m/%d/%H%M%S')}.jpg"

        # Upload to S3
        s3_bucket = 'taxiwatch-frames'  # From environment variable
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=frame_bytes,
            ContentType='image/jpeg',
            Metadata={
                'device_id': device_id,
                'vehicle_id': str(vehicle_id),
                'camera_position': camera_position
            }
        )

        # Enqueue for AI analysis
        sqs_queue_url = 'https://sqs.us-east-1.amazonaws.com/...'  # From env
        sqs_client.send_message(
            QueueUrl=sqs_queue_url,
            MessageBody=json.dumps({
                'vehicle_id': vehicle_id,
                's3_bucket': s3_bucket,
                's3_key': s3_key,
                'timestamp': timestamp.isoformat()
            })
        )

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Frame uploaded successfully',
                's3_key': s3_key
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
'''

# ============================================================================
# ALEMBIC
# ============================================================================

FILES["backend/alembic.ini"] = '''[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/taxiwatch

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''

FILES["backend/alembic/env.py"] = '''from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.database import Base
from app.models import *  # Import all models

config = context.config

# Override sqlalchemy.url with our config
config.set_main_option('sqlalchemy.url', settings.database_url_sync)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

# ============================================================================
# DOCKER
# ============================================================================

FILES["backend/Dockerfile"] = '''FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

FILES["docker-compose.yml"] = '''version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: taxiwatch_postgres
    environment:
      POSTGRES_DB: taxiwatch
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: taxiwatch_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: taxiwatch_backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/taxiwatch
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=True
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
'''

# ============================================================================
# GENERATE ALL FILES
# ============================================================================

def main():
    print("=" * 70)
    print("Generating complete FastAPI project...")
    print("=" * 70)

    for filepath, content in FILES.items():
        create_file(filepath, content)

    print("=" * 70)
    print(f"✅ Generated {len(FILES)} files successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. cd backend")
    print("2. pip install -r requirements.txt")
    print("3. cp .env.example .env  # Configure your .env")
    print("4. alembic upgrade head")
    print("5. uvicorn app.main:app --reload")
    print("\nOr use Docker:")
    print("docker-compose up")

if __name__ == "__main__":
    main()
