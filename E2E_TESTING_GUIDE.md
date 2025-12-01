# TaxiWatch - End-to-End Testing Guide

Complete guide for testing all functionalities of the TaxiWatch fleet management system.

## Quick Start

### 1. Configure Environment Variables

**Backend** (`backend/.env`):
```
OPENAI_API_KEY=sk-your-actual-openai-api-key
ENVIRONMENT=development
DEBUG=True
```

**Frontend** (`ui/.env.local`):
```
NEXT_PUBLIC_MAPBOX_TOKEN=pk-your-actual-mapbox-token
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 2. Start Services

```bash
# Start backend, database, redis
docker-compose up -d

# Start frontend (separate terminal)
cd ui && pnpm dev

# Start GPS simulator (separate terminal)
python3 hardware/gps_simulator.py
```

**Available at:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Seed Test Data (One-time)

```bash
docker-compose exec backend python -m app.scripts.seed_data
```

Creates:
- 5 test users (admin, managers, drivers)
- 8 test vehicles (NYC-001 to NYC-008)
- 16 devices (GPS + Camera)
- 50 GPS locations
- 10 FAQs
- 10 trips
- 5 incidents

### 4. Run E2E Tests

```bash
./scripts/e2e-test.sh
```

---

## Manual Testing Checklist

### Authentication
- [ ] Login with admin/Admin123!
- [ ] Verify JWT token received
- [ ] Try invalid credentials (should fail)
- [ ] Test token refresh

### Dashboard
- [ ] View live map with vehicles
- [ ] Check real-time GPS updates
- [ ] Verify fleet statistics
- [ ] View recent incidents

### Live Map (/map)
- [ ] Full-screen map displays
- [ ] Filter by vehicle status
- [ ] Focus on specific vehicle
- [ ] View vehicle telemetry (speed, heading)
- [ ] Check WebSocket updates every 5 seconds

### Vehicles (/vehicles)
- [ ] Search by license plate/make/model
- [ ] Filter by status
- [ ] View vehicle details
- [ ] Check GPS history
- [ ] Delete vehicle (admin only)

### Admin - Users (/admin/users)
- [ ] List all users
- [ ] Search users
- [ ] Filter by role
- [ ] Activate/deactivate user
- [ ] Edit user details
- [ ] Delete user

### Admin - Devices (/admin/devices)
- [ ] List all devices
- [ ] Filter by type (GPS, Camera, Sensor, OBD)
- [ ] Filter by status (Online, Offline, Error)
- [ ] Ping device
- [ ] Create new device
- [ ] Edit device
- [ ] Delete device

### Admin - FAQs (/admin/faqs)
- [ ] List all FAQs
- [ ] Search FAQs
- [ ] Filter by category
- [ ] Create new FAQ
- [ ] Edit FAQ
- [ ] Toggle active status
- [ ] Delete FAQ

### Chat (/chat)
- [ ] Send message to AI
- [ ] Receive response
- [ ] Ask follow-up questions
- [ ] Check FAQ integration
- [ ] Verify conversation history

---

## Test Data Summary

### Users
```
admin / Admin123! (ADMIN)
manager1 / Manager123! (FLEET_MANAGER)
dispatcher1 / Dispatcher123! (DISPATCHER)
driver1 / Driver123! (OPERATOR)
driver2 / Driver123! (OPERATOR)
```

### Vehicles
- NYC-001 to NYC-008
- Status: Mix of ACTIVE, MAINTENANCE, OUT_OF_SERVICE
- Locations: NYC area

### Devices
- 8 GPS devices (U-blox NEO-6M)
- 8 Camera devices (Espressif ESP32-CAM)
- Status: Online/Offline

### FAQs (10)
- General topics (2)
- Vehicles (2)
- Drivers (1)
- Trips (2)
- Incidents (1)
- System (2)

---

## API Endpoints Testing

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}'
```

### Get Vehicles
```bash
curl http://localhost:8000/api/v1/vehicles \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Live Locations
```bash
curl http://localhost:8000/api/v1/tracking/live \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Devices
```bash
curl http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get FAQs
```bash
curl http://localhost:8000/api/v1/faqs
```

### Send Chat Message
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message":"How many vehicles?"}'
```

---

## Troubleshooting

### Backend Issues
```bash
docker-compose ps              # Check status
docker-compose logs backend    # View logs
docker-compose restart backend # Restart
```

### No Data Showing
```bash
# Re-seed database
docker-compose exec backend python -m app.scripts.seed_data

# Verify data exists
curl http://localhost:8000/api/v1/vehicles
```

### GPS Not Updating
```bash
# Check simulator
ps aux | grep gps_simulator

# Start manually
python3 hardware/gps_simulator.py
```

### Map Not Showing
```bash
# Verify Mapbox token
cat ui/.env.local | grep MAPBOX_TOKEN

# Check browser console (F12)
```

### Chat Not Working
```bash
# Verify OpenAI key
echo $OPENAI_API_KEY

# Check logs
docker-compose logs backend | grep -i openai
```

---

## Performance Metrics to Check

- Page load time < 3 seconds
- Map updates < 1 second latency
- Chat response < 5 seconds
- API response < 500ms
- WebSocket ping < 100ms

---

## All Tests Passing? 

Your TaxiWatch system is **100% functional and ready for deployment**! 🚀
