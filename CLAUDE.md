# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaxiWatch is a real-time taxi fleet monitoring system with AI-powered video analysis. It combines GPS tracking, live video streaming, incident detection using OpenAI Vision API, and comprehensive reporting for taxi fleet management.

**Tech Stack:**
- **Backend**: Django 5.2+ with Django REST Framework, running via `uv` package manager
- **Frontend**: Next.js 14+ with TypeScript, using App Router
- **Real-time**: Django Channels (WebSockets), Celery for background tasks
- **Database**: PostgreSQL 15+, Redis for caching/message broker
- **AI**: OpenAI GPT-4 Vision API for incident detection and analysis
- **Infrastructure**: Docker Compose (development), AWS (production)

## Architecture

The project is split into two main directories:

### Backend (`/core`)
Django monolithic application with multiple apps following Django's app-per-feature pattern:
- `accounts/` - Custom user model with role-based access (Admin, Fleet Manager, Dispatcher, Operator)
- `vehicles/` - Vehicle, Driver, and Trip management
- `tracking/` - GPS location tracking (models, WebSocket consumers for real-time updates)
- `video/` - Video streaming and archive management
- `incidents/` - Incident and Alert models with AI analysis integration
- `reports/` - Report generation system
- `taxiwatch/` - Main Django project settings, URL routing, Celery/Channels configuration

**Key architectural patterns:**
- JWT authentication via `djangorestframework-simplejwt`
- WebSocket routing defined in `taxiwatch/routing.py` (currently placeholder)
- Celery workers handle async tasks (video processing, AI analysis, report generation)
- Models use `JSONField` for flexible location/metadata storage

### Frontend (`/ui`)
Next.js application using:
- App Router architecture (`/app` directory)
- TypeScript
- Tailwind CSS v4 with Shadcn/ui components
- Package manager: pnpm (lockfile: `pnpm-lock.yaml`)

## Common Development Commands

### Backend (Django)

**Prerequisites**: Python 3.12+, `uv` package manager installed

```bash
# Navigate to backend
cd core/

# Install dependencies (uv creates .venv automatically)
uv sync

# Run database migrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Run development server (port 8000)
uv run python manage.py runserver

# Run a single test
uv run python manage.py test <app_name>.<test_file>.<TestClass>.<test_method>

# Create new migrations after model changes
uv run python manage.py makemigrations

# Access Django shell
uv run python manage.py shell

# Start Celery worker (for background tasks)
uv run celery -A taxiwatch worker -l info

# Start Celery beat (for scheduled tasks)
uv run celery -A taxiwatch beat -l info
```

### Frontend (Next.js)

```bash
# Navigate to frontend
cd ui/

# Install dependencies
pnpm install

# Run development server (port 3000)
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Run linter
pnpm lint
```

### Docker Compose (Full Stack)

```bash
# Start all services (backend, postgres, redis, celery workers)
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Rebuild containers after dependency changes
docker-compose build

# Run migrations in container
docker-compose exec backend uv run python manage.py migrate
```

**Note**: Frontend service is commented out in `docker-compose.yml` - run frontend locally with `cd ui && pnpm dev`

## Database Architecture

**Custom User Model**: `accounts.User` (extends AbstractUser)
- Defines AUTH_USER_MODEL in settings
- Role-based access with `Role` choices (ADMIN, FLEET_MANAGER, DISPATCHER, OPERATOR)

**Key Relationships**:
- `Driver` (1-to-1 with User) tracks license info and status
- `Vehicle` has current_driver FK to Driver
- `Trip` links Vehicle and Driver with location/time data
- `Incident` references Vehicle, Driver, and can have multiple VideoArchive clips
- `Alert` can be associated with an Incident and tracks acknowledgment

**Location Data**: Stored as JSONField with format: `{lat, lng, address}`

## AI Integration

OpenAI Vision API is used for:
1. Incident detection from video frames (accidents, harsh braking, etc.)
2. Driver behavior analysis (drowsiness, distraction, phone usage)
3. Object detection and collision risk assessment
4. Generating natural language incident summaries

**Key configuration**: `OPENAI_API_KEY` in environment variables (see `taxiwatch/settings.py`)

**Processing pipeline**: Extract frames via FFmpeg → Batch API calls → Parse responses → Generate alerts

## Configuration & Environment

**Backend environment variables** (see `docker-compose.yml` and `taxiwatch/settings.py`):
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - PostgreSQL config
- `REDIS_HOST`, `REDIS_PORT` - Redis connection
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Celery configuration
- `OPENAI_API_KEY` - OpenAI API access
- `SECRET_KEY`, `DEBUG` - Django settings
- `CORS_ALLOWED_ORIGINS` - Frontend URL whitelist

**Settings files**:
- `taxiwatch/settings.py` - Main settings (production-ready with env vars)
- `taxiwatch/settings_dev.py` - Development overrides (if needed)

## Development Workflow

1. **Model changes**: Modify models → `makemigrations` → `migrate`
2. **API endpoints**: Add views in app's `views.py` → Add routes to app's `urls.py` → Include in `taxiwatch/urls.py`
3. **WebSocket consumers**: Create consumer in app → Add to `taxiwatch/routing.py` websocket_urlpatterns
4. **Background tasks**: Define Celery tasks in app's `tasks.py` → Ensure Celery autodiscovery is enabled
5. **Frontend API integration**: API base URL is `http://localhost:8000/api/v1/` (CORS configured for localhost:3000)

## Testing

- Django tests use Django's test framework (`django.test.TestCase`)
- Run tests with `uv run python manage.py test`
- Test database is created/destroyed automatically
- Frontend testing setup: TBD (no test configuration in package.json yet)

## Authentication Flow

1. POST `/api/v1/auth/login` → Returns JWT access/refresh tokens
2. Include `Authorization: Bearer <access_token>` header in subsequent requests
3. Refresh tokens via `/api/v1/auth/refresh`
4. Protected endpoints require authentication (configured in REST_FRAMEWORK settings)

## WebSocket Endpoints (Planned)

- `ws://localhost:8000/ws/tracking/` - Live GPS updates
- `ws://localhost:8000/ws/alerts/` - Real-time alert notifications
- `ws://localhost:8000/ws/video/<vehicle_id>/` - Video streaming

**Current status**: Routing file exists but consumers not yet implemented

## Video Storage

- Development: Local filesystem at `core/media/`
- Production: AWS S3 (configuration in settings: `AWS_ACCESS_KEY_ID`, `AWS_S3_BUCKET_NAME`, etc.)
- FFmpeg required for video processing (installed in Dockerfile)

## Key Files to Understand

- `core/taxiwatch/settings.py` - All configuration and installed apps
- `core/taxiwatch/urls.py` - Main URL routing
- `core/taxiwatch/celery.py` - Celery app configuration
- `docker-compose.yml` - Service orchestration and environment setup
- `core/pyproject.toml` - Python dependencies (managed by uv)
- `ui/package.json` - Frontend dependencies

## Known Limitations

- Frontend Docker service disabled in compose file (run manually)
- WebSocket consumers are scaffolded but not implemented
- Task files (`tasks.py`) don't exist yet - Celery autodiscovery won't find tasks until created
- No automated tests written yet despite test files existing

[PLEASE DON'T ADD MARKDOWN FILES]
