"""
GPS Simulator for TaxiWatch
Simulates GPS location updates for vehicles in real-time
"""
import asyncio
import random
import httpx
from datetime import datetime, timezone
import sys

# NYC area coordinates
NYC_CENTER = {"lat": 40.7128, "lng": -74.0060}
RADIUS = 0.05  # roughly 5km

API_URL = "http://backend:8000/api/v1"


def generate_location(vehicle_id: int, base_lat: float, base_lng: float):
    """Generate a random GPS location near the base coordinates"""
    # Add some random movement
    lat_offset = random.uniform(-0.002, 0.002)
    lng_offset = random.uniform(-0.002, 0.002)

    return {
        "vehicle_id": vehicle_id,
        "latitude": base_lat + lat_offset,
        "longitude": base_lng + lng_offset,
        "altitude": random.uniform(0, 100),
        "speed": random.uniform(5, 60),
        "heading": random.uniform(0, 360),
        "accuracy": random.uniform(5, 20)
    }


async def send_location_update(client: httpx.AsyncClient, location: dict):
    """Send location update to the API (no auth required for device endpoint)"""
    try:
        response = await client.post(
            f"{API_URL}/tracking/location",
            json=location
        )
        if response.status_code == 201:
            print(f"  ✓ Vehicle {location['vehicle_id']}: "
                  f"({location['latitude']:.4f}, {location['longitude']:.4f}) "
                  f"Speed: {location['speed']:.1f} km/h")
            return True
        else:
            print(f"  ✗ Vehicle {location['vehicle_id']}: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"  ✗ Vehicle {location['vehicle_id']}: {e}")
        return False


async def wait_for_backend(client: httpx.AsyncClient, max_retries: int = 30):
    """Wait for backend to be ready"""
    for i in range(max_retries):
        try:
            response = await client.get("http://backend:8000/health")
            if response.status_code == 200:
                return True
        except Exception:
            pass
        print(f"  Waiting for backend... ({i+1}/{max_retries})")
        await asyncio.sleep(2)
    return False


async def main():
    """Main simulator loop"""
    print()
    print("=" * 60)
    print("🚕 TaxiWatch GPS Simulator")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Wait for backend
        print("⏳ Waiting for backend to be ready...")
        if not await wait_for_backend(client):
            print("❌ Backend not available. Exiting.")
            return

        print("✓ Backend is ready!")
        print()
        print("🚀 Starting GPS simulation...")
        print(f"📍 Simulating 8 vehicles in NYC area")
        print(f"🔄 Updates every 3 seconds")
        print()

        # Initialize vehicle base positions around NYC
        vehicle_positions = {}
        for vehicle_id in range(1, 9):
            vehicle_positions[vehicle_id] = {
                "lat": NYC_CENTER["lat"] + random.uniform(-RADIUS, RADIUS),
                "lng": NYC_CENTER["lng"] + random.uniform(-RADIUS, RADIUS)
            }

        # Simulation loop
        iteration = 0
        try:
            while True:
                iteration += 1
                now = datetime.now(timezone.utc).strftime('%H:%M:%S')
                print(f"\n📡 Update #{iteration} ({now})")

                success_count = 0
                # Send updates for all vehicles
                for vehicle_id in range(1, 9):
                    base_pos = vehicle_positions[vehicle_id]
                    location = generate_location(
                        vehicle_id,
                        base_pos["lat"],
                        base_pos["lng"]
                    )
                    # Update base position for next iteration (simulate movement)
                    vehicle_positions[vehicle_id] = {
                        "lat": location["latitude"],
                        "lng": location["longitude"]
                    }
                    if await send_location_update(client, location):
                        success_count += 1

                print(f"  📊 {success_count}/8 vehicles updated")

                # Wait before next update
                await asyncio.sleep(3)

        except KeyboardInterrupt:
            print("\n\n⏹️  GPS Simulator stopped")
        except Exception as e:
            print(f"\n\n❌ Simulator error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("Starting GPS Simulator...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
