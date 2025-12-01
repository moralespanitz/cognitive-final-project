"""
Seed script to populate database with test data.
Run with: python -m app.scripts.seed_data
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import AsyncSessionLocal
from app.models import *
from app.models.device import DeviceType, DeviceStatus
from app.models.faq import FAQCategory
from sqlalchemy import select
from datetime import datetime, timedelta
import random


async def seed_all():
    """Seed all test data."""
    async with AsyncSessionLocal() as db:
        print("🌱 Starting database seeding...")

        # Check if data already exists
        result = await db.execute(select(User))
        if result.scalars().first():
            print("⚠️  Database already has data. Skipping seed.")
            print("   Run with --force to reset and reseed")
            return

        try:
            # 1. Create Users
            print("\n👥 Creating users...")
            users = await seed_users(db)

            # 2. Create Drivers
            print("🚗 Creating drivers...")
            drivers = await seed_drivers(db, users)

            # 3. Create Vehicles
            print("🚕 Creating vehicles...")
            vehicles = await seed_vehicles(db, drivers)

            # 4. Create Devices
            print("📱 Creating devices...")
            devices = await seed_devices(db, vehicles)

            # 5. Create GPS Locations
            print("📍 Creating GPS locations...")
            await seed_gps_locations(db, vehicles)

            # 6. Create FAQs
            print("❓ Creating FAQs...")
            await seed_faqs(db)

            # 7. Create Trips
            print("🛣️  Creating trips...")
            await seed_trips(db, vehicles, drivers)

            # 8. Create Incidents
            print("⚠️  Creating incidents...")
            await seed_incidents(db, vehicles, drivers)

            await db.commit()
            print("\n✅ Database seeding completed successfully!")

            # Print summary
            print("\n📊 Summary:")
            print(f"   Users: {len(users)}")
            print(f"   Drivers: {len(drivers)}")
            print(f"   Vehicles: {len(vehicles)}")
            print(f"   Devices: {len(devices)}")
            print(f"   FAQs: 10+")
            print(f"   GPS Locations: ~50")
            print(f"   Trips: 10")
            print(f"   Incidents: 5")

        except Exception as e:
            print(f"\n❌ Error seeding database: {e}")
            await db.rollback()
            raise


async def seed_users(db):
    """Create test users."""
    users_data = [
        {
            "username": "admin",
            "email": "admin@taxiwatch.com",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS0MKNDTe",  # Admin123!
            "first_name": "Admin",
            "last_name": "User",
            "role": "ADMIN",
            "is_superuser": True
        },
        {
            "username": "manager1",
            "email": "manager1@taxiwatch.com",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS0MKNDTe",
            "first_name": "John",
            "last_name": "Manager",
            "role": "FLEET_MANAGER"
        },
        {
            "username": "dispatcher1",
            "email": "dispatcher1@taxiwatch.com",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS0MKNDTe",
            "first_name": "Sarah",
            "last_name": "Dispatcher",
            "role": "DISPATCHER"
        },
        {
            "username": "driver1",
            "email": "driver1@taxiwatch.com",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS0MKNDTe",
            "first_name": "Mike",
            "last_name": "Driver",
            "role": "OPERATOR"
        },
        {
            "username": "driver2",
            "email": "driver2@taxiwatch.com",
            "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS0MKNDTe",
            "first_name": "Emma",
            "last_name": "Rodriguez",
            "role": "OPERATOR"
        }
    ]

    users = []
    for user_data in users_data:
        user = User(**user_data)
        db.add(user)
        users.append(user)

    await db.flush()
    return users


async def seed_drivers(db, users):
    """Create test drivers."""
    drivers = []

    # Only create drivers for operator users
    operator_users = [u for u in users if u.role == "OPERATOR"]

    for idx, user in enumerate(operator_users, 1):
        driver = Driver(
            user_id=user.id,
            license_number=f"DL{1000 + idx}",
            license_expiry=datetime.now().date() + timedelta(days=365 * 2),
            status="ON_DUTY" if idx % 2 == 0 else "OFF_DUTY",
            rating=round(random.uniform(4.0, 5.0), 2),
            total_trips=random.randint(50, 500)
        )
        db.add(driver)
        drivers.append(driver)

    await db.flush()
    return drivers


async def seed_vehicles(db, drivers):
    """Create test vehicles."""
    vehicles_data = [
        {"license_plate": "NYC-001", "make": "Toyota", "model": "Camry", "year": 2022, "color": "Yellow", "vin": "1HGCM82633A001001"},
        {"license_plate": "NYC-002", "make": "Honda", "model": "Accord", "year": 2023, "color": "Yellow", "vin": "1HGCM82633A001002"},
        {"license_plate": "NYC-003", "make": "Ford", "model": "Fusion", "year": 2021, "color": "Yellow", "vin": "1HGCM82633A001003"},
        {"license_plate": "NYC-004", "make": "Chevrolet", "model": "Malibu", "year": 2022, "color": "Yellow", "vin": "1HGCM82633A001004"},
        {"license_plate": "NYC-005", "make": "Nissan", "model": "Altima", "year": 2023, "color": "Yellow", "vin": "1HGCM82633A001005"},
        {"license_plate": "NYC-006", "make": "Hyundai", "model": "Sonata", "year": 2022, "color": "Yellow", "vin": "1HGCM82633A001006"},
        {"license_plate": "NYC-007", "make": "Toyota", "model": "Corolla", "year": 2021, "color": "Yellow", "vin": "1HGCM82633A001007"},
        {"license_plate": "NYC-008", "make": "Honda", "model": "Civic", "year": 2023, "color": "Yellow", "vin": "1HGCM82633A001008"},
    ]

    vehicles = []
    for idx, vehicle_data in enumerate(vehicles_data):
        status_choice = random.choice(["ACTIVE", "ACTIVE", "ACTIVE", "MAINTENANCE", "OUT_OF_SERVICE"])

        vehicle = Vehicle(
            **vehicle_data,
            capacity=4,
            status=status_choice,
            current_driver_id=drivers[idx % len(drivers)].id if idx < len(drivers) and status_choice == "ACTIVE" else None
        )
        db.add(vehicle)
        vehicles.append(vehicle)

    await db.flush()
    return vehicles


async def seed_devices(db, vehicles):
    """Create test devices."""
    devices = []

    for vehicle in vehicles:
        # GPS device
        gps_device = Device(
            vehicle_id=vehicle.id,
            device_type=DeviceType.GPS,
            serial_number=f"GPS{vehicle.id:04d}",
            model="NEO-6M",
            manufacturer="U-blox",
            firmware_version="1.2.3",
            status=DeviceStatus.ONLINE if vehicle.status == "ACTIVE" else DeviceStatus.OFFLINE,
            last_ping=datetime.utcnow() if vehicle.status == "ACTIVE" else None,
            config={"update_interval": 5, "accuracy": "high"}
        )
        db.add(gps_device)
        devices.append(gps_device)

        # Camera device (50% of vehicles)
        if vehicle.id % 2 == 0:
            camera_device = Device(
                vehicle_id=vehicle.id,
                device_type=DeviceType.CAMERA,
                serial_number=f"CAM{vehicle.id:04d}",
                model="ESP32-CAM",
                manufacturer="Espressif",
                firmware_version="2.0.1",
                status=DeviceStatus.ONLINE if vehicle.status == "ACTIVE" else DeviceStatus.OFFLINE,
                last_ping=datetime.utcnow() if vehicle.status == "ACTIVE" else None,
                config={"resolution": "1280x720", "fps": 15}
            )
            db.add(camera_device)
            devices.append(camera_device)

    await db.flush()
    return devices


async def seed_gps_locations(db, vehicles):
    """Create test GPS locations."""
    # NYC center coordinates
    base_lat = 40.7128
    base_lng = -74.0060

    for vehicle in vehicles[:5]:  # Only first 5 vehicles
        for i in range(10):
            location = GPSLocation(
                vehicle_id=vehicle.id,
                latitude=base_lat + random.uniform(-0.05, 0.05),
                longitude=base_lng + random.uniform(-0.05, 0.05),
                speed=random.uniform(0, 60),
                heading=random.uniform(0, 360),
                accuracy=random.uniform(5, 15),
                altitude=random.uniform(10, 50),
                device_id=f"GPS{vehicle.id:04d}",
                timestamp=datetime.utcnow() - timedelta(minutes=i * 5)
            )
            db.add(location)

    await db.flush()


async def seed_faqs(db):
    """Create test FAQs."""
    faqs_data = [
        {
            "question": "How do I track my fleet in real-time?",
            "answer": "Navigate to the Dashboard or Live Map to see all vehicles with their current locations, speed, and status updated in real-time via GPS tracking.",
            "category": FAQCategory.GENERAL,
            "keywords": "track, real-time, map, location",
            "priority": 10
        },
        {
            "question": "How do I add a new vehicle to the system?",
            "answer": "Go to Vehicles page and click 'Add Vehicle'. Fill in the vehicle details including license plate, VIN, make, model, and year.",
            "category": FAQCategory.VEHICLES,
            "keywords": "add, new, vehicle, create",
            "priority": 9
        },
        {
            "question": "What do the vehicle status colors mean?",
            "answer": "Green indicates ACTIVE vehicles ready for service, Yellow indicates MAINTENANCE, and Red indicates OUT_OF_SERVICE vehicles.",
            "category": FAQCategory.VEHICLES,
            "keywords": "status, color, meaning, active",
            "priority": 8
        },
        {
            "question": "How do I assign a driver to a vehicle?",
            "answer": "In the vehicle details page, select the driver from the dropdown menu. Only available drivers will be shown.",
            "category": FAQCategory.DRIVERS,
            "keywords": "assign, driver, vehicle",
            "priority": 7
        },
        {
            "question": "How does the AI incident detection work?",
            "answer": "Our AI analyzes camera footage using computer vision to detect accidents, harsh braking, driver drowsiness, phone usage, and other safety incidents in real-time.",
            "category": FAQCategory.INCIDENTS,
            "keywords": "AI, incident, detection, camera, vision",
            "priority": 9
        },
        {
            "question": "How can I view trip history?",
            "answer": "Go to the vehicle details page and scroll to the Trip History section. You can filter by date range and see detailed information for each trip.",
            "category": FAQCategory.TRIPS,
            "keywords": "trip, history, past, records",
            "priority": 6
        },
        {
            "question": "What should I do if a device goes offline?",
            "answer": "Check the Devices page in Admin Panel. If a device shows OFFLINE status, verify the vehicle's power connection and network connectivity. You can also remotely reboot devices from the admin panel.",
            "category": FAQCategory.SYSTEM,
            "keywords": "offline, device, troubleshoot, connection",
            "priority": 8
        },
        {
            "question": "How do I manage user permissions?",
            "answer": "As an Admin, go to Admin Panel > Manage Users. You can assign roles (Admin, Fleet Manager, Dispatcher, Operator) to control access levels.",
            "category": FAQCategory.SYSTEM,
            "keywords": "permissions, roles, users, access",
            "priority": 7
        },
        {
            "question": "Can I export trip data?",
            "answer": "Yes, use the Reports section to generate and export trip data in CSV or PDF format. You can filter by vehicle, driver, date range, and more.",
            "category": FAQCategory.TRIPS,
            "keywords": "export, data, report, CSV, PDF",
            "priority": 5
        },
        {
            "question": "How accurate is the GPS tracking?",
            "answer": "GPS accuracy is typically 5-15 meters depending on device quality and satellite visibility. Real-time location updates every 5-10 seconds.",
            "category": FAQCategory.GENERAL,
            "keywords": "GPS, accuracy, tracking, precision",
            "priority": 6
        }
    ]

    for faq_data in faqs_data:
        faq = FAQ(**faq_data)
        db.add(faq)

    await db.flush()


async def seed_trips(db, vehicles, drivers):
    """Create test trips."""
    for i in range(10):
        vehicle = random.choice(vehicles)
        driver = random.choice(drivers)

        start_time = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        duration = random.randint(15, 120)

        trip = Trip(
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration),
            start_location={"lat": 40.7128, "lng": -74.0060, "address": "NYC Center"},
            end_location={"lat": 40.7580, "lng": -73.9855, "address": "Times Square"},
            distance=random.uniform(5, 30),
            duration=duration,
            status="COMPLETED",
            fare=random.uniform(15, 75)
        )
        db.add(trip)

    await db.flush()


async def seed_incidents(db, vehicles, drivers):
    """Create test incidents."""
    incident_types = ["ACCIDENT", "HARSH_BRAKING", "SPEEDING", "AGGRESSIVE_DRIVING", "DROWSINESS"]
    severities = ["LOW", "MEDIUM", "HIGH"]

    for i in range(5):
        vehicle = random.choice(vehicles)
        driver = random.choice(drivers)

        incident = Incident(
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            type=random.choice(incident_types),
            severity=random.choice(severities),
            description=f"Test incident #{i+1} for demonstration purposes",
            ai_summary="AI-detected safety concern requiring review",
            ai_confidence=random.randint(70, 95),
            location={"lat": 40.7128, "lng": -74.0060, "address": "NYC"},
            detected_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
        )
        db.add(incident)

    await db.flush()


if __name__ == "__main__":
    print("🚀 TaxiWatch Database Seeder")
    print("=" * 60)
    asyncio.run(seed_all())
