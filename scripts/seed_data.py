#!/usr/bin/env python3
"""
Seed database with test data for TaxiWatch.
Creates users, vehicles, drivers, and sample data for testing.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.vehicle import Driver, Vehicle, VehicleStatus, DriverStatus, Trip, TripStatus
from app.models.tracking import GPSLocation
from app.models.incident import Incident, IncidentType, IncidentSeverity, Alert, AlertPriority
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import random


async def clear_database():
    """Clear all data from database (be careful!)."""
    print("🗑️  Clearing existing data...")

    async with AsyncSessionLocal() as db:
        # Delete in order to respect foreign keys
        await db.execute("DELETE FROM chat_history")
        await db.execute("DELETE FROM alerts")
        await db.execute("DELETE FROM incidents")
        await db.execute("DELETE FROM gps_locations")
        await db.execute("DELETE FROM video_archives")
        await db.execute("DELETE FROM video_streams")
        await db.execute("DELETE FROM trips")
        await db.execute("DELETE FROM vehicles")
        await db.execute("DELETE FROM drivers")
        await db.execute("DELETE FROM users")
        await db.commit()

    print("✅ Database cleared")


async def create_users():
    """Create test users with different roles."""
    print("👥 Creating users...")

    users_data = [
        {
            "username": "admin",
            "email": "admin@taxiwatch.com",
            "password": "Admin123!",
            "first_name": "Admin",
            "last_name": "User",
            "role": UserRole.ADMIN,
            "is_superuser": True,
        },
        {
            "username": "fleet_manager",
            "email": "manager@taxiwatch.com",
            "password": "Manager123!",
            "first_name": "Fleet",
            "last_name": "Manager",
            "role": UserRole.FLEET_MANAGER,
            "is_superuser": False,
        },
        {
            "username": "dispatcher",
            "email": "dispatcher@taxiwatch.com",
            "password": "Dispatcher123!",
            "first_name": "John",
            "last_name": "Dispatcher",
            "role": UserRole.DISPATCHER,
            "is_superuser": False,
        },
        {
            "username": "operator1",
            "email": "operator1@taxiwatch.com",
            "password": "Operator123!",
            "first_name": "Alice",
            "last_name": "Operator",
            "role": UserRole.OPERATOR,
            "is_superuser": False,
        },
        {
            "username": "operator2",
            "email": "operator2@taxiwatch.com",
            "password": "Operator123!",
            "first_name": "Bob",
            "last_name": "Operator",
            "role": UserRole.OPERATOR,
            "is_superuser": False,
        },
    ]

    async with AsyncSessionLocal() as db:
        created_users = []
        for user_data in users_data:
            password = user_data.pop("password")
            user = User(
                **user_data,
                hashed_password=get_password_hash(password),
                is_active=True,
            )
            db.add(user)
            created_users.append(user)

        await db.commit()

        for user in created_users:
            await db.refresh(user)

    print(f"✅ Created {len(created_users)} users")
    return created_users


async def create_drivers(users):
    """Create test drivers linked to users."""
    print("🚗 Creating drivers...")

    # Use some users as drivers
    driver_users = [u for u in users if u.role in [UserRole.OPERATOR, UserRole.DISPATCHER]][:3]

    drivers_data = [
        {
            "user_id": driver_users[0].id,
            "license_number": "DL-12345678",
            "license_expiry": datetime.utcnow() + timedelta(days=365),
            "phone": "+1-555-0001",
            "address": "123 Main St, New York, NY 10001",
            "status": DriverStatus.ON_DUTY,
        },
        {
            "user_id": driver_users[1].id,
            "license_number": "DL-87654321",
            "license_expiry": datetime.utcnow() + timedelta(days=730),
            "phone": "+1-555-0002",
            "address": "456 Park Ave, New York, NY 10002",
            "status": DriverStatus.ON_DUTY,
        },
        {
            "user_id": driver_users[2].id,
            "license_number": "DL-11223344",
            "license_expiry": datetime.utcnow() + timedelta(days=180),
            "phone": "+1-555-0003",
            "address": "789 Broadway, New York, NY 10003",
            "status": DriverStatus.OFF_DUTY,
        },
    ]

    async with AsyncSessionLocal() as db:
        created_drivers = []
        for driver_data in drivers_data:
            driver = Driver(**driver_data)
            db.add(driver)
            created_drivers.append(driver)

        await db.commit()

        for driver in created_drivers:
            await db.refresh(driver)

    print(f"✅ Created {len(created_drivers)} drivers")
    return created_drivers


async def create_vehicles(drivers):
    """Create test vehicles."""
    print("🚕 Creating vehicles...")

    vehicles_data = [
        {
            "license_plate": "NYC-001",
            "make": "Toyota",
            "model": "Camry Hybrid",
            "year": 2023,
            "color": "Yellow",
            "vin": "1HGCM82633A123456",
            "capacity": 4,
            "status": VehicleStatus.ACTIVE,
            "current_driver_id": drivers[0].id,
        },
        {
            "license_plate": "NYC-002",
            "make": "Honda",
            "model": "Accord",
            "year": 2022,
            "color": "Yellow",
            "vin": "1HGCM82633A234567",
            "capacity": 4,
            "status": VehicleStatus.ACTIVE,
            "current_driver_id": drivers[1].id,
        },
        {
            "license_plate": "NYC-003",
            "make": "Ford",
            "model": "Fusion",
            "year": 2021,
            "color": "Yellow",
            "vin": "1HGCM82633A345678",
            "capacity": 4,
            "status": VehicleStatus.MAINTENANCE,
            "current_driver_id": None,
        },
        {
            "license_plate": "NYC-004",
            "make": "Chevrolet",
            "model": "Malibu",
            "year": 2023,
            "color": "Yellow",
            "vin": "1HGCM82633A456789",
            "capacity": 4,
            "status": VehicleStatus.INACTIVE,
            "current_driver_id": None,
        },
    ]

    async with AsyncSessionLocal() as db:
        created_vehicles = []
        for vehicle_data in vehicles_data:
            vehicle = Vehicle(**vehicle_data)
            db.add(vehicle)
            created_vehicles.append(vehicle)

        await db.commit()

        for vehicle in created_vehicles:
            await db.refresh(vehicle)

    print(f"✅ Created {len(created_vehicles)} vehicles")
    return created_vehicles


async def create_gps_locations(vehicles):
    """Create sample GPS locations for vehicles."""
    print("📍 Creating GPS locations...")

    # New York City coordinates (around Manhattan)
    base_lat, base_lng = 40.7580, -73.9855

    locations_count = 0
    async with AsyncSessionLocal() as db:
        for vehicle in vehicles[:2]:  # Only active vehicles
            # Create location history (last 10 positions)
            for i in range(10):
                location = GPSLocation(
                    vehicle_id=vehicle.id,
                    latitude=base_lat + random.uniform(-0.05, 0.05),
                    longitude=base_lng + random.uniform(-0.05, 0.05),
                    speed=random.uniform(0, 60),
                    heading=random.uniform(0, 360),
                    accuracy=random.uniform(5, 15),
                    timestamp=datetime.utcnow() - timedelta(minutes=i*5),
                )
                db.add(location)
                locations_count += 1

        await db.commit()

    print(f"✅ Created {locations_count} GPS locations")


async def create_trips(vehicles, drivers):
    """Create sample trips."""
    print("🛣️  Creating trips...")

    trips_data = [
        {
            "vehicle_id": vehicles[0].id,
            "driver_id": drivers[0].id,
            "start_location": {"lat": 40.7580, "lng": -73.9855, "address": "Times Square, NY"},
            "end_location": {"lat": 40.7489, "lng": -73.9680, "address": "Grand Central, NY"},
            "start_time": datetime.utcnow() - timedelta(hours=2),
            "end_time": datetime.utcnow() - timedelta(hours=1, minutes=45),
            "distance": 3.2,
            "duration": 15,
            "status": TripStatus.COMPLETED,
        },
        {
            "vehicle_id": vehicles[1].id,
            "driver_id": drivers[1].id,
            "start_location": {"lat": 40.7614, "lng": -73.9776, "address": "Central Park South"},
            "end_location": {"lat": 40.7128, "lng": -74.0060, "address": "Wall Street"},
            "start_time": datetime.utcnow() - timedelta(minutes=30),
            "end_time": None,
            "distance": 0,
            "duration": 0,
            "status": TripStatus.IN_PROGRESS,
        },
    ]

    async with AsyncSessionLocal() as db:
        for trip_data in trips_data:
            trip = Trip(**trip_data)
            db.add(trip)

        await db.commit()

    print(f"✅ Created {len(trips_data)} trips")


async def create_incidents(vehicles, drivers):
    """Create sample incidents."""
    print("⚠️  Creating incidents...")

    incidents_data = [
        {
            "vehicle_id": vehicles[0].id,
            "driver_id": drivers[0].id,
            "type": IncidentType.HARSH_BRAKING,
            "severity": IncidentSeverity.MEDIUM,
            "description": "Sudden braking detected on 5th Avenue",
            "ai_summary": "AI detected harsh braking event. Driver may have encountered unexpected obstacle.",
            "location": {"lat": 40.7580, "lng": -73.9855, "address": "5th Ave & 42nd St"},
            "detected_at": datetime.utcnow() - timedelta(hours=1),
        },
        {
            "vehicle_id": vehicles[1].id,
            "driver_id": drivers[1].id,
            "type": IncidentType.SPEEDING,
            "severity": IncidentSeverity.LOW,
            "description": "Speed limit exceeded by 10 mph",
            "ai_summary": "Vehicle exceeded speed limit on FDR Drive.",
            "location": {"lat": 40.7489, "lng": -73.9680, "address": "FDR Drive"},
            "detected_at": datetime.utcnow() - timedelta(minutes=30),
        },
    ]

    async with AsyncSessionLocal() as db:
        created_incidents = []
        for incident_data in incidents_data:
            incident = Incident(**incident_data)
            db.add(incident)
            created_incidents.append(incident)

        await db.commit()

        for incident in created_incidents:
            await db.refresh(incident)

    print(f"✅ Created {len(created_incidents)} incidents")
    return created_incidents


async def create_alerts(incidents):
    """Create alerts for incidents."""
    print("🔔 Creating alerts...")

    alerts_data = [
        {
            "incident_id": incidents[0].id,
            "vehicle_id": incidents[0].vehicle_id,
            "type": "harsh_braking",
            "priority": AlertPriority.MEDIUM,
            "message": "Harsh braking detected on vehicle NYC-001",
            "acknowledged": False,
        },
        {
            "incident_id": incidents[1].id,
            "vehicle_id": incidents[1].vehicle_id,
            "type": "speeding",
            "priority": AlertPriority.LOW,
            "message": "Speed limit exceeded on vehicle NYC-002",
            "acknowledged": True,
        },
    ]

    async with AsyncSessionLocal() as db:
        for alert_data in alerts_data:
            alert = Alert(**alert_data)
            db.add(alert)

        await db.commit()

    print(f"✅ Created {len(alerts_data)} alerts")


async def main():
    """Main function to seed database."""
    print("🌱 Starting database seeding...")
    print()

    # Clear existing data
    await clear_database()
    print()

    # Create data
    users = await create_users()
    drivers = await create_drivers(users)
    vehicles = await create_vehicles(drivers)
    await create_gps_locations(vehicles)
    await create_trips(vehicles, drivers)
    incidents = await create_incidents(vehicles, drivers)
    await create_alerts(incidents)

    print()
    print("=" * 60)
    print("✅ DATABASE SEEDING COMPLETE!")
    print("=" * 60)
    print()
    print("📊 Created:")
    print(f"  - {len(users)} users")
    print(f"  - {len(drivers)} drivers")
    print(f"  - {len(vehicles)} vehicles")
    print(f"  - GPS locations for active vehicles")
    print(f"  - Sample trips")
    print(f"  - {len(incidents)} incidents")
    print(f"  - Alerts")
    print()
    print("🔑 Login credentials:")
    print("  - Username: admin        | Password: Admin123!")
    print("  - Username: fleet_manager | Password: Manager123!")
    print("  - Username: dispatcher    | Password: Dispatcher123!")
    print("  - Username: operator1     | Password: Operator123!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
