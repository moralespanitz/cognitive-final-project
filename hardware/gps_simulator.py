#!/usr/bin/env python3
"""
GPS Simulator for TaxiWatch
Simulates GPS data from multiple vehicles and sends it to the backend API.
"""
import requests
import time
import random
import math
from datetime import datetime
from typing import List, Tuple

# Configuration
API_URL = "http://localhost:8000/api/v1/tracking/location"
NUM_VEHICLES = 5
UPDATE_INTERVAL = 5  # seconds

# NYC coordinates (approx area)
CENTER_LAT = 40.7128
CENTER_LNG = -74.0060
RADIUS = 0.05  # degrees (~5km)


class Vehicle:
    """Represents a simulated vehicle with GPS tracking."""
    
    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id
        self.device_id = f"SIM_GPS_{vehicle_id:03d}"
        
        # Random starting position near center
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, RADIUS)
        self.lat = CENTER_LAT + distance * math.cos(angle)
        self.lng = CENTER_LNG + distance * math.sin(angle)
        
        # Random movement direction and speed
        self.heading = random.uniform(0, 360)
        self.speed = random.uniform(20, 60)  # km/h
        
    def update_position(self):
        """Update vehicle position based on speed and heading."""
        # Convert speed from km/h to degrees per second (approximate)
        # 1 degree latitude ≈ 111 km
        speed_deg_per_sec = (self.speed / 111000) * (UPDATE_INTERVAL)
        
        # Calculate new position
        heading_rad = math.radians(self.heading)
        self.lat += speed_deg_per_sec * math.cos(heading_rad)
        self.lng += speed_deg_per_sec * math.sin(heading_rad) / math.cos(math.radians(self.lat))
        
        # Randomly adjust heading (simulate turns)
        if random.random() < 0.3:  # 30% chance to turn
            self.heading += random.uniform(-30, 30)
            self.heading = self.heading % 360
        
        # Randomly adjust speed
        if random.random() < 0.2:  # 20% chance to change speed
            self.speed += random.uniform(-10, 10)
            self.speed = max(10, min(80, self.speed))  # Clamp between 10-80 km/h
        
        # Keep within bounds (bounce back if out of area)
        if abs(self.lat - CENTER_LAT) > RADIUS:
            self.heading = (self.heading + 180) % 360
            self.lat = CENTER_LAT + (RADIUS * 0.9) * (1 if self.lat > CENTER_LAT else -1)
        
        if abs(self.lng - CENTER_LNG) > RADIUS:
            self.heading = (self.heading + 180) % 360
            self.lng = CENTER_LNG + (RADIUS * 0.9) * (1 if self.lng > CENTER_LNG else -1)
    
    def get_gps_data(self) -> dict:
        """Get current GPS data in API format."""
        return {
            "vehicle_id": self.vehicle_id,
            "latitude": round(self.lat, 6),
            "longitude": round(self.lng, 6),
            "speed": round(self.speed, 1),
            "heading": round(self.heading, 1),
            "accuracy": round(random.uniform(5, 15), 1),
            "altitude": round(random.uniform(10, 50), 1),
            "device_id": self.device_id
        }


def send_gps_data(vehicle: Vehicle) -> bool:
    """Send GPS data to backend API."""
    data = vehicle.get_gps_data()
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        if response.status_code == 201:
            print(f"✓ Vehicle {vehicle.vehicle_id}: {data['latitude']:.4f}, {data['longitude']:.4f} @ {data['speed']:.1f} km/h")
            return True
        else:
            print(f"✗ Vehicle {vehicle.vehicle_id}: Error {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Vehicle {vehicle.vehicle_id}: Connection error - {e}")
        return False


def main():
    """Main simulation loop."""
    print("=" * 60)
    print("TaxiWatch GPS Simulator")
    print("=" * 60)
    print(f"Simulating {NUM_VEHICLES} vehicles")
    print(f"Update interval: {UPDATE_INTERVAL} seconds")
    print(f"API endpoint: {API_URL}")
    print(f"Center: {CENTER_LAT}, {CENTER_LNG}")
    print("=" * 60)
    print()
    
    # Create vehicles
    vehicles = [Vehicle(i + 1) for i in range(NUM_VEHICLES)]
    
    print(f"Created {len(vehicles)} vehicles")
    print("Press Ctrl+C to stop\n")
    
    iteration = 0
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] Iteration {iteration}")
            print("-" * 60)
            
            # Update and send data for each vehicle
            for vehicle in vehicles:
                vehicle.update_position()
                send_gps_data(vehicle)
            
            # Wait before next update
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user")
        print(f"Total iterations: {iteration}")
        print(f"Total updates sent: {iteration * len(vehicles)}")


if __name__ == "__main__":
    main()
