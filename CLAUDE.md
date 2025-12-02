# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaxiWatch is a real-time taxi fleet monitoring system with GPS tracking, live video streaming from ESP32-CAM devices, and comprehensive taxi booking management.

**Tech Stack:**
- **Backend**: FastAPI with SQLAlchemy (async), running via `uv` package manager
- **Frontend**: Next.js 16+ with TypeScript, using App Router and Tailwind CSS v4
- **Real-time**: FastAPI WebSockets for live video streaming and GPS updates
- **Database**: PostgreSQL 15+ with asyncpg driver, Redis for caching
- **Video**: ESP32-CAM devices streaming JPEG images via HTTP POST
- **Infrastructure**: Docker Compose (development), AWS-ready (production)

## Architecture

The project is split into two main directories:

### Backend (`/backend`)
FastAPI application with modular structure:
- `app/models/` - SQLAlchemy models (User, Vehicle, Driver, Trip, Device, GPSLocation, FAQ)
- `app/api/v1/` - API endpoints organized by feature
  - `auth.py` - JWT authentication (login, register, token refresh)
  - `users.py` - User management and profile endpoints
  - `vehicles.py` - Vehicle, Driver, and Trip management with complete booking flow
  - `tracking.py` - GPS location tracking endpoints
  - `video.py` - ESP32-CAM video upload and WebSocket streaming
  - `devices.py` - IoT device management and health checks
  - `faqs.py` - FAQ CRUD operations
- `app/core/` - Core utilities (security, config, exceptions)
- `app/schemas/` - Pydantic schemas for request/response validation
- `app/dependencies.py` - FastAPI dependency injection (authentication, etc.)

**Key architectural patterns:**
- JWT authentication with passlib bcrypt hashing
- Async SQLAlchemy with asyncpg for PostgreSQL
- WebSocket endpoint at `/ws/video/{route_id}` for real-time video streaming
- In-memory frame storage for latest device images
- Role-based access control (ADMIN, FLEET_MANAGER, DISPATCHER, OPERATOR)
- JSON fields for flexible location data: `{lat, lng, address}`

### Frontend (`/ui`)
Next.js application using:
- App Router with route groups: `(dashboard)` for authenticated pages
- TypeScript with strict type checking
- Tailwind CSS v4 with Shadcn/ui components
- Zustand for state management (auth, vehicles, tracking)
- Package manager: pnpm (lockfile: `pnpm-lock.yaml`)
- Pages:
  - `/login` - Authentication page
  - `/` - Dashboard with fleet overview and live map
  - `/book` - Customer taxi booking interface
  - `/trip/[id]` - Real-time trip tracking
  - `/driver` - Driver panel for accepting/managing trips
  - `/map` - Live GPS tracking map
  - `/vehicles` - Vehicle management
  - `/chat` - AI chat interface
  - `/admin/*` - Admin panels for users, devices, FAQs

## Common Development Commands

### Backend (FastAPI)

**Prerequisites**: Python 3.12+, `uv` package manager installed

```bash
# Navigate to backend
cd backend/

# Install dependencies (uv creates .venv automatically)
uv sync

# Run database migrations (Alembic)
uv run alembic upgrade head

# Create new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Run development server (port 8000)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access Python shell with app context
uv run python -c "from app.database import SessionLocal; db = SessionLocal()"

# Run tests (if configured)
uv run pytest

# Interactive API docs
# Open browser: http://localhost:8000/docs (Swagger UI)
# Open browser: http://localhost:8000/redoc (ReDoc)
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
# Start all services (postgres, redis, backend, frontend)
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Rebuild containers after dependency changes
docker-compose build

# Restart a specific service
docker-compose restart backend

# Check service status
docker-compose ps

# Access database
docker-compose exec postgres psql -U postgres -d taxiwatch

# Run migrations in container
docker-compose exec backend uv run alembic upgrade head
```

**Services:**
- **postgres**: PostgreSQL 15 on port 5432
- **redis**: Redis 7 on port 6379
- **backend**: FastAPI on port 8000
- **frontend**: Next.js on port 3000

## Database Architecture

**User Model** (`app/models/user.py`):
- Role-based access with enum: ADMIN, FLEET_MANAGER, DISPATCHER, OPERATOR
- Fields: username (unique), email, hashed_password (bcrypt), first_name, last_name, is_active, is_superuser
- Relationships: trips (as customer), driver profile

**Driver Model** (`app/models/vehicle.py`):
- 1-to-1 relationship with User (user_id FK)
- Fields: license_number (unique), license_expiry, rating, status (ON_DUTY, OFF_DUTY, BUSY)
- Relationships: vehicles (via current_driver), trips

**Vehicle Model** (`app/models/vehicle.py`):
- Fields: license_plate (unique), make, model, year, vin (unique), color, status (ACTIVE, MAINTENANCE, OUT_OF_SERVICE)
- FK: current_driver_id (nullable)
- Relationships: driver, trips, gps_locations

**Trip Model** (`app/models/vehicle.py`):
- Complete booking lifecycle: REQUESTED → ACCEPTED → ARRIVED → IN_PROGRESS → COMPLETED/CANCELLED
- Fields: customer_id, driver_id, vehicle_id, pickup_location (JSON), destination (JSON), estimated_fare, fare, distance, duration
- Timestamps: start_time, end_time, created_at, updated_at

**GPSLocation Model** (`app/models/tracking.py`):
- Fields: vehicle_id, device_id, latitude, longitude, altitude, speed, heading, accuracy, timestamp
- Indexes on vehicle_id and timestamp for performance

**Device Model** (`app/models/device.py`):
- IoT device management: device_id, route_id, device_type (GPS_TRACKER, CAMERA, SENSOR), status, last_ping
- FK: vehicle_id (nullable)

**FAQ Model** (`app/models/faq.py`):
- Fields: question, answer, category, display_order, is_published

**Location Data Format**: JSON with structure `{lat: float, lng: float, address: string}`

## Video Streaming Architecture

**ESP32-CAM Integration**:
- ESP32-CAM devices capture JPEG images every 3 seconds
- Images sent via HTTP POST to `/api/v1/video/device/upload`
- Custom header: `X-Route-ID` identifies the device/route
- Images stored in-memory as base64 for WebSocket streaming
- No AI analysis - simple real-time monitoring

**WebSocket Streaming** (`/ws/video/{route_id}`):
- Clients connect to WebSocket endpoint for specific route
- Server broadcasts latest frame every 100ms (10 FPS max)
- Frame format: `{type: "frame", route_id: string, image: base64, timestamp: ISO8601, size: int}`
- Connection management via VideoConnectionManager class

**Endpoints**:
- `POST /api/v1/video/device/upload` - Receive image from ESP32-CAM
- `GET /api/v1/video/device/latest/{route_id}` - Get latest frame for route
- `GET /api/v1/video/device/list` - List all active devices with frames
- `WS /ws/video/{route_id}` - WebSocket for real-time streaming

## Configuration & Environment

**Backend environment variables** (see `docker-compose.yml` and `app/config.py`):
- `DATABASE_URL` - PostgreSQL connection string (default: postgresql+asyncpg://postgres:postgres@postgres:5432/taxiwatch)
- `REDIS_URL` - Redis connection string (default: redis://redis:6379/0)
- `SECRET_KEY` - JWT signing key (required for production)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiry (default: 30 days)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiry (default: 7 days)
- `DEBUG` - Debug mode flag (default: True)
- `OPENAI_API_KEY` - OpenAI API key (optional, for future AI features)

**Configuration file**:
- `backend/app/config.py` - Pydantic Settings with environment variable loading

## Development Workflow

1. **Model changes**:
   - Modify models in `app/models/`
   - Create migration: `uv run alembic revision --autogenerate -m "description"`
   - Apply migration: `uv run alembic upgrade head`

2. **API endpoints**:
   - Create/update endpoint in `app/api/v1/{module}.py`
   - Add router to `app/main.py` if new module
   - Define Pydantic schemas in `app/schemas/`
   - Add dependencies if authentication required

3. **WebSocket endpoints**:
   - Add WebSocket route in `app/main.py` with `@app.websocket()`
   - Implement connection manager for multi-client handling
   - Handle connect/disconnect lifecycle

4. **Frontend pages**:
   - Create page in `ui/app/(dashboard)/{route}/page.tsx`
   - Update navigation in `ui/app/(dashboard)/layout.tsx`
   - Add API calls in page component
   - Use Zustand stores for state management

5. **API Integration**:
   - Base URL: `http://localhost:8000/api/v1/`
   - CORS configured for `http://localhost:3000`
   - Include `Authorization: Bearer {token}` header for protected routes

## Taxi Booking Flow

**Complete end-to-end booking system:**

1. **Customer requests taxi** (`POST /api/v1/trips/request`):
   - Provide pickup_location and destination (JSON with lat, lng, address)
   - System finds nearest available driver using Haversine distance formula
   - Calculates estimated fare: $2.00 base + $1.50/km
   - Creates trip with status REQUESTED
   - Returns trip with assigned driver and vehicle

2. **Driver accepts trip** (`POST /api/v1/trips/{trip_id}/accept`):
   - Changes status to ACCEPTED
   - Driver navigates to pickup location

3. **Driver arrives** (`POST /api/v1/trips/{trip_id}/arrive`):
   - Changes status to ARRIVED
   - Customer notified driver is waiting

4. **Trip starts** (`POST /api/v1/trips/{trip_id}/start`):
   - Changes status to IN_PROGRESS
   - Records start_time
   - Customer onboard

5. **Trip completes** (`POST /api/v1/trips/{trip_id}/complete`):
   - Changes status to COMPLETED
   - Records end_time
   - Calculates duration
   - Sets final fare

**Additional endpoints**:
- `POST /api/v1/trips/{trip_id}/cancel` - Cancel trip
- `GET /api/v1/trips/{trip_id}` - Get trip details
- `GET /api/v1/trips` - List trips (filterable by status, driver, vehicle)
- `GET /api/v1/drivers/available?lat={lat}&lng={lng}` - Find available drivers

## Testing

**Backend testing**:
- FastAPI testing with pytest (setup pending)
- Manual testing via Swagger UI at http://localhost:8000/docs
- Test with curl or Postman

**Frontend testing**:
- No automated tests configured yet
- Manual E2E testing with real users and trips

**Test credentials**:
- Admin: `admin` / `Admin123!`
- Drivers: `driver1` through `driver8` / `Admin123!`
- Customer: `customer1` / `Admin123!`

## Authentication Flow

1. **Login**: `POST /api/v1/auth/login`
   - Body: `{username: string, password: string}`
   - Returns: `{access_token: string, refresh_token: string, token_type: "bearer"}`

2. **Get current user**: `GET /api/v1/users/me`
   - Header: `Authorization: Bearer {access_token}`
   - Returns user object with id, username, email, role, etc.

3. **Register**: `POST /api/v1/auth/register`
   - Body: `{username, email, password, first_name, last_name, role}`
   - Returns: Created user object

4. **Refresh token**: `POST /api/v1/auth/refresh`
   - Body: `{refresh_token: string}`
   - Returns: New access_token

5. **Protected endpoints**:
   - Use `Depends(get_current_user)` for any authenticated user
   - Use `Depends(get_current_manager_user)` for admin/manager only
   - Automatically returns 401 if token invalid/expired

## WebSocket Endpoints

- `ws://localhost:8000/ws/video/{route_id}` - Real-time video streaming from ESP32-CAM devices

**Planned/Future**:
- `ws://localhost:8000/ws/tracking/` - Live GPS updates
- `ws://localhost:8000/ws/alerts/` - Real-time alert notifications

## Key Files to Understand

**Backend:**
- `backend/app/main.py` - FastAPI application entry point, CORS, routers, WebSocket endpoints
- `backend/app/config.py` - Pydantic Settings configuration
- `backend/app/database.py` - SQLAlchemy async engine and session management
- `backend/app/dependencies.py` - FastAPI dependency injection (auth, db sessions)
- `backend/app/core/security.py` - Password hashing and JWT token functions
- `backend/app/models/` - SQLAlchemy ORM models
- `backend/app/schemas/` - Pydantic schemas for validation
- `backend/app/api/v1/` - API endpoint implementations
- `backend/pyproject.toml` - Python dependencies (managed by uv)

**Frontend:**
- `ui/app/(dashboard)/layout.tsx` - Main dashboard layout with navigation and auth
- `ui/app/(dashboard)/page.tsx` - Dashboard home page
- `ui/app/login/page.tsx` - Login page with authentication
- `ui/app/(dashboard)/book/page.tsx` - Customer booking interface
- `ui/app/(dashboard)/trip/[id]/page.tsx` - Trip tracking page
- `ui/app/(dashboard)/driver/page.tsx` - Driver panel
- `ui/lib/store.ts` - Zustand state management
- `ui/lib/api.ts` - API client functions
- `ui/components/map.tsx` - Mapbox vehicle map component
- `ui/package.json` - Frontend dependencies (pnpm)

**Infrastructure:**
- `docker-compose.yml` - Service orchestration (postgres, redis, backend, frontend)
- `backend/Dockerfile` - Backend container image
- `.env` - Environment variables (not in repo, create locally)

## Known Limitations & Future Improvements

- No automated tests configured yet
- WebSocket for GPS tracking not implemented (only video streaming)
- Map requires Mapbox token (set in `.env.local`)
- No AI incident detection (removed for simplicity)
- Frontend runs in Docker with node_modules as volume (slower on Mac)
- No production deployment scripts yet
- Password reset flow not implemented
- Email notifications not configured

## Database Seeding

**Existing data:**
- 1 admin user: `admin` / `Admin123!`
- 8 drivers: `driver1` through `driver8` / `Admin123!`
- 1 customer: `customer1` / `Admin123!`
- 8 vehicles assigned to drivers
- 8 driver profiles with ON_DUTY status
- Sample GPS locations for each vehicle

**To add more test data:**
```sql
docker-compose exec postgres psql -U postgres -d taxiwatch
-- Insert SQL commands here
```

[PLEASE DON'T ADD MARKDOWN FILES]
