# Código Completo FastAPI - Archivos Restantes

## INSTRUCCIONES

Copia cada sección de código en el archivo correspondiente.

---

## 1. API Router: Authentication

**Archivo:** `backend/app/api/v1/auth.py`

```python
"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...database import get_db
from ...models.user import User
from ...schemas.user import UserCreate, UserResponse, UserLogin
from ...schemas.token import Token
from ...core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from ...core.exceptions import UnauthorizedException, ConflictException
from jose import JWTError

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if username exists
    stmt = select(User).where(User.username == user_data.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException(detail="Username already registered")

    # Check if email exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictException(detail="Email already registered")

    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get JWT tokens."""
    # Find user
    stmt = select(User).where(User.username == user_credentials.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise UnauthorizedException(detail="Incorrect username or password")

    if not user.is_active:
        raise UnauthorizedException(detail="User is inactive")

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise UnauthorizedException(detail="Invalid token type")

        user_id = int(payload.get("sub"))
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException(detail="User not found or inactive")

        # Create new tokens
        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    except JWTError:
        raise UnauthorizedException(detail="Could not validate refresh token")
```

---

## 2. API Router: Tracking (GPS)

**Archivo:** `backend/app/api/v1/tracking.py`

```python
"""
GPS Tracking API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from typing import List

from ...database import get_db
from ...models.tracking import GPSLocation
from ...models.vehicle import Vehicle
from ...schemas.tracking import GPSLocationCreate, GPSLocationResponse
from ...dependencies import get_current_user
from ...models.user import User

router = APIRouter()


@router.post("/location", response_model=GPSLocationResponse, status_code=201)
async def receive_gps_location(
    location_data: GPSLocationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Receive GPS location from device (ESP32).
    No authentication required for devices.
    """
    # Verify vehicle exists
    stmt = select(Vehicle).where(Vehicle.id == location_data.vehicle_id)
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Create GPS location
    db_location = GPSLocation(
        vehicle_id=location_data.vehicle_id,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        speed=location_data.speed,
        heading=location_data.heading,
        accuracy=location_data.accuracy,
        altitude=location_data.altitude,
        device_id=location_data.device_id,
        timestamp=datetime.utcnow()
    )

    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)

    # TODO: Broadcast to WebSocket clients
    # await broadcast_location_update(db_location)

    return db_location


@router.get("/live", response_model=List[GPSLocationResponse])
async def get_live_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get latest GPS locations for all active vehicles."""
    # Get latest location for each vehicle (last 60 seconds)
    cutoff_time = datetime.utcnow() - timedelta(seconds=60)

    # Subquery to get latest timestamp per vehicle
    from sqlalchemy import func
    subq = (
        select(
            GPSLocation.vehicle_id,
            func.max(GPSLocation.timestamp).label('max_timestamp')
        )
        .where(GPSLocation.timestamp >= cutoff_time)
        .group_by(GPSLocation.vehicle_id)
        .subquery()
    )

    # Get full location records
    stmt = (
        select(GPSLocation)
        .join(
            subq,
            (GPSLocation.vehicle_id == subq.c.vehicle_id) &
            (GPSLocation.timestamp == subq.c.max_timestamp)
        )
        .order_by(desc(GPSLocation.timestamp))
    )

    result = await db.execute(stmt)
    locations = result.scalars().all()

    return locations


@router.get("/vehicle/{vehicle_id}/history", response_model=List[GPSLocationResponse])
async def get_vehicle_location_history(
    vehicle_id: int,
    hours: int = Query(default=24, ge=1, le=168),  # Max 1 week
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get GPS location history for a specific vehicle."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    stmt = (
        select(GPSLocation)
        .where(
            GPSLocation.vehicle_id == vehicle_id,
            GPSLocation.timestamp >= cutoff_time
        )
        .order_by(desc(GPSLocation.timestamp))
        .limit(1000)  # Max 1000 points
    )

    result = await db.execute(stmt)
    locations = result.scalars().all()

    return locations
```

---

## 3. Schemas: Tracking

**Archivo:** `backend/app/schemas/tracking.py`

```python
"""Tracking schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class GPSLocationBase(BaseModel):
    """Base GPS location schema."""
    vehicle_id: int
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    speed: Optional[Decimal] = Field(None, ge=0)
    heading: Optional[int] = Field(None, ge=0, le=359)
    accuracy: Optional[Decimal] = None
    altitude: Optional[Decimal] = None
    device_id: Optional[str] = None


class GPSLocationCreate(GPSLocationBase):
    """Schema for creating GPS location."""
    pass


class GPSLocationResponse(GPSLocationBase):
    """Schema for GPS location response."""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
```

---

## 4. Service: Chat (OpenAI)

**Archivo:** `backend/app/services/chat_service.py`

```python
"""
Chat service for AI chatbot using OpenAI.
"""

from openai import OpenAI
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..config import settings
from ..models.user import User
from ..models.vehicle import Vehicle, Driver
from ..models.incident import Incident


class ChatService:
    """Service for handling chatbot conversations."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def _build_context(self, user: User, db: AsyncSession) -> str:
        """Build system context from database."""
        # Get statistics
        total_vehicles = await db.scalar(select(func.count()).select_from(Vehicle))
        active_vehicles = await db.scalar(
            select(func.count()).select_from(Vehicle).where(Vehicle.status == "ACTIVE")
        )
        total_drivers = await db.scalar(select(func.count()).select_from(Driver))
        on_duty_drivers = await db.scalar(
            select(func.count()).select_from(Driver).where(Driver.status == "ON_DUTY")
        )

        context = f"""
You are the AI assistant for TaxiWatch, a real-time taxi fleet monitoring system.

Current System Status:
- Total Vehicles: {total_vehicles}
- Active Vehicles: {active_vehicles}
- Total Drivers: {total_drivers}
- On-Duty Drivers: {on_duty_drivers}

User Information:
- Name: {user.full_name}
- Role: {user.role.value}

You can help with:
1. Fleet status and statistics
2. Vehicle and driver information
3. Incident explanations
4. System usage guidance
5. Safety recommendations

Respond concisely and professionally in Spanish or English based on user's language.
"""
        return context

    async def get_response(
        self,
        user_message: str,
        user: User,
        db: AsyncSession,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        Get chatbot response.

        Args:
            user_message: User's message
            user: Current user
            db: Database session
            conversation_history: Previous messages

        Returns:
            Dict with response and usage info
        """
        try:
            # Build context
            system_context = await self._build_context(user, db)

            # Prepare messages
            messages = [{"role": "system", "content": system_context}]

            if conversation_history:
                messages.extend(conversation_history)

            messages.append({"role": "user", "content": user_message})

            # Call OpenAI
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
                'response': f"Lo siento, ocurrió un error: {str(e)}",
                'usage': {}
            }


# Global instance
chat_service = ChatService()
```

---

## 5. API Router: Chat

**Archivo:** `backend/app/api/v1/chat.py`

```python
"""
Chat API endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid

from ...database import get_db
from ...dependencies import get_current_user
from ...models.user import User
from ...models.incident import ChatHistory
from ...schemas.chat import ChatMessage, ChatResponse
from ...services.chat_service import chat_service

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send message to chatbot and get response.
    """
    # Generate session ID if not provided
    session_id = message.session_id or str(uuid.uuid4())

    # Get conversation history (last 10 messages)
    stmt = (
        select(ChatHistory)
        .where(
            ChatHistory.user_id == current_user.id,
            ChatHistory.session_id == session_id
        )
        .order_by(ChatHistory.created_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    history_records = result.scalars().all()

    # Convert to OpenAI format (reverse order for chronological)
    conversation_history = []
    for record in reversed(history_records):
        conversation_history.append({"role": "user", "content": record.message})
        conversation_history.append({"role": "assistant", "content": record.response})

    # Get response from chat service
    result = await chat_service.get_response(
        user_message=message.message,
        user=current_user,
        db=db,
        conversation_history=conversation_history
    )

    # Save to database
    chat_record = ChatHistory(
        user_id=current_user.id,
        session_id=session_id,
        message=message.message,
        response=result['response'],
        tokens_used=result.get('usage', {}).get('total_tokens', 0)
    )
    db.add(chat_record)
    await db.commit()

    return {
        "response": result['response'],
        "session_id": session_id,
        "usage": result.get('usage', {})
    }
```

---

## 6. Schemas: Chat

**Archivo:** `backend/app/schemas/chat.py`

```python
"""Chat schemas."""
from pydantic import BaseModel
from typing import Optional, Dict


class ChatMessage(BaseModel):
    """Schema for chat message."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    response: str
    session_id: str
    usage: Optional[Dict[str, int]] = {}
```

---

## 7. Lambda Handler: API (Mangum)

**Archivo:** `backend/app/lambda_handlers/api_handler.py`

```python
"""
Lambda handler for FastAPI app using Mangum.
This is the main entry point for AWS Lambda.
"""

from mangum import Mangum
from ..main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")


# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## CONTINÚA EN SIGUIENTE MENSAJE...

Por limitaciones de espacio, el resto del código (Terraform, Alembic, más routers, etc.) lo pondré en archivos separados.

**SIGUIENTE PASO:**
1. Copia el código de arriba en los archivos correspondientes
2. Te enviaré Terraform y el resto en el siguiente mensaje

¿Procedo?
