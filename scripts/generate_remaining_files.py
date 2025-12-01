#!/usr/bin/env python3
"""
Script to generate remaining FastAPI project files.
Run: python scripts/generate_remaining_files.py
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

# File templates
FILES = {
    # Schemas
    "backend/app/schemas/__init__.py": '''"""Pydantic schemas."""
from .user import UserCreate, UserUpdate, UserResponse, UserLogin
from .token import Token, TokenPayload
from .vehicle import DriverCreate, DriverUpdate, DriverResponse
from .vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from .vehicle import TripCreate, TripUpdate, TripResponse
from .tracking import GPSLocationCreate, GPSLocationResponse
from .video import VideoArchiveResponse, VideoStreamResponse
from .incident import IncidentCreate, IncidentResponse, AlertResponse
from .chat import ChatMessage, ChatResponse

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "Token", "TokenPayload",
    "DriverCreate", "DriverUpdate", "DriverResponse",
    "VehicleCreate", "VehicleUpdate", "VehicleResponse",
    "TripCreate", "TripUpdate", "TripResponse",
    "GPSLocationCreate", "GPSLocationResponse",
    "VideoArchiveResponse", "VideoStreamResponse",
    "IncidentCreate", "IncidentResponse", "AlertResponse",
    "ChatMessage", "ChatResponse",
]
''',

    "backend/app/schemas/user.py": '''"""User schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from ..models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.OPERATOR


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str
''',

    "backend/app/schemas/token.py": '''"""Token schemas."""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: str  # Subject (user ID or username)
    exp: int  # Expiration time
    type: str  # Token type (access or refresh)
''',

    "backend/app/api/__init__.py": "# API routers\n",
    "backend/app/api/v1/__init__.py": "# API v1 routers\n",

    "backend/app/services/__init__.py": "# Services\n",

    "backend/app/admin/__init__.py": "# SQLAdmin\n",

    "backend/app/lambda_handlers/__init__.py": "# Lambda handlers\n",

    "backend/app/__init__.py": "# TaxiWatch Backend\n",

    "backend/.env.example": '''# Application
APP_NAME=TaxiWatch API
DEBUG=False
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/taxiwatch

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# S3 Buckets
S3_BUCKET_FRAMES=taxiwatch-frames
S3_BUCKET_VIDEOS=taxiwatch-videos
S3_BUCKET_STATIC=taxiwatch-static

# SQS
SQS_AI_ANALYSIS_QUEUE=taxiwatch-ai-analysis-queue

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_VISION_MODEL=gpt-4-vision-preview

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me-in-production
ADMIN_SECRET_KEY=admin-secret-key-change-me
''',

    "backend/README.md": '''# TaxiWatch Backend - FastAPI + Lambda

## Tech Stack
- FastAPI 0.104+
- SQLAlchemy 2.0 (async)
- PostgreSQL
- SQLAdmin
- AWS Lambda (via Mangum)
- OpenAI API

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start development server:
```bash
uvicorn app.main:app --reload
```

5. Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

### Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app tests/
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── core/            # Core utilities
│   ├── admin/           # SQLAdmin setup
│   ├── lambda_handlers/ # AWS Lambda handlers
│   ├── config.py        # Settings
│   ├── database.py      # DB setup
│   └── main.py          # FastAPI app
├── alembic/             # DB migrations
├── tests/               # Tests
└── requirements.txt     # Dependencies
```

## AWS Lambda Deployment

See `../terraform/` for infrastructure setup.

Build Lambda package:
```bash
../scripts/build_lambda.sh
```

Deploy:
```bash
cd ../terraform
terraform apply
```
''',
}


def create_file(filepath: str, content: str):
    """Create a file with given content."""
    file_path = BASE_DIR / filepath
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✅ Created: {filepath}")


def main():
    """Generate all files."""
    print("=" * 60)
    print("Generating remaining FastAPI files...")
    print("=" * 60)

    for filepath, content in FILES.items():
        create_file(filepath, content)

    print("=" * 60)
    print(f"✅ Generated {len(FILES)} files successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review generated files")
    print("2. Run: cd backend && pip install -r requirements.txt")
    print("3. Configure .env file")
    print("4. Run: alembic upgrade head")
    print("5. Run: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
