# TaxiWatch Backend API

Django REST Framework backend for the TaxiWatch Real-Time Taxi Monitoring System.

## 🚀 Quick Start (Development Mode)

### Installation & Setup

1. **Activate Virtual Environment**
   ```bash
   cd core
   source .venv/bin/activate
   ```

2. **Run Development Server**
   ```bash
   DJANGO_SETTINGS_MODULE=taxiwatch.settings_dev python manage.py runserver
   ```

3. **Access the Application**
   - API Root: http://localhost:8000/api/v1/
   - Admin Panel: http://localhost:8000/admin/
   - Login: username=`admin`, password=`admin123`

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/login/` - Get JWT tokens
- `POST /api/v1/auth/refresh/` - Refresh access token
- `POST /api/v1/users/` - Register new user
- `GET /api/v1/users/me/` - Get current user profile

### Vehicles
- `GET /api/v1/vehicles/` - List all vehicles
- `POST /api/v1/vehicles/` - Create vehicle
- `GET /api/v1/vehicles/{id}/` - Get vehicle details
- `POST /api/v1/vehicles/{id}/assign_driver/` - Assign driver

### Drivers
- `GET /api/v1/drivers/` - List all drivers
- `POST /api/v1/drivers/` - Create driver
- `GET /api/v1/drivers/{id}/performance/` - Get performance metrics

### Trips
- `GET /api/v1/trips/` - List trips (supports filtering)
- `POST /api/v1/trips/` - Create trip

## 🗂️ Project Structure

```
core/
├── accounts/          # User auth & management
├── vehicles/          # Vehicles, drivers, trips
├── tracking/          # GPS location tracking
├── video/             # Video streams & archives
├── incidents/         # Incidents & alerts
├── reports/           # Report generation
└── taxiwatch/         # Main configuration
```

## 🔧 Configuration Files

- `settings.py` - Production settings (PostgreSQL, Redis)
- `settings_dev.py` - Development settings (SQLite, in-memory)
- `.env` - Environment variables
- `docker-compose.yml` - Docker services configuration

## 📊 Database Models

All models created and migrated:
✓ User (with roles: Admin, Fleet Manager, Dispatcher, Operator)
✓ Driver, Vehicle, Trip
✓ GPS_Location
✓ VideoStream, VideoArchive
✓ Incident, Alert
✓ Report

## 🐳 Docker Deployment

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Start all services
docker-compose up -d
```

## 🧪 Testing

```bash
# Check for errors
DJANGO_SETTINGS_MODULE=taxiwatch.settings_dev python manage.py check

# Run tests
DJANGO_SETTINGS_MODULE=taxiwatch.settings_dev python manage.py test
```

## 📝 Next Steps

- [ ] Implement WebSocket consumers for real-time tracking
- [ ] Add Celery tasks for AI processing
- [ ] Create remaining API endpoints (tracking, video, incidents, reports)
- [ ] Add API documentation (Swagger)
- [ ] Write unit tests
- [ ] Implement AI integration with OpenAI

