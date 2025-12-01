#!/usr/bin/env python3
"""
Create test vehicles in the database for GPS simulation.
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1"

# First, create a user and login to get token
def get_auth_token():
    """Register and login to get access token."""
    # Try to register
    register_data = {
        "username": "testadmin",
        "email": "testadmin@taxiwatch.com",
        "password": "Admin123!",
        "first_name": "Test",
        "last_name": "Admin",
        "role": "ADMIN"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/register", json=register_data)
        print(f"Register: {response.status_code}")
    except:
        pass  # User might already exist
    
    # Login
    login_data = {
        "username": "testadmin",
        "password": "Admin123!"
    }
    
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None


def create_vehicles(token):
    """Create 5 test vehicles."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    vehicles = [
        {
            "license_plate": "NYC-001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2022,
            "color": "Yellow",
            "vin": "1HGCM82633A123456",
            "capacity": 4,
            "status": "ACTIVE"
        },
        {
            "license_plate": "NYC-002",
            "make": "Honda",
            "model": "Accord",
            "year": 2023,
            "color": "Yellow",
            "vin": "1HGCM82633A123457",
            "capacity": 4,
            "status": "ACTIVE"
        },
        {
            "license_plate": "NYC-003",
            "make": "Ford",
            "model": "Fusion",
            "year": 2021,
            "color": "Yellow",
            "vin": "1HGCM82633A123458",
            "capacity": 4,
            "status": "ACTIVE"
        },
        {
            "license_plate": "NYC-004",
            "make": "Chevrolet",
            "model": "Malibu",
            "year": 2022,
            "color": "Yellow",
            "vin": "1HGCM82633A123459",
            "capacity": 4,
            "status": "ACTIVE"
        },
        {
            "license_plate": "NYC-005",
            "make": "Nissan",
            "model": "Altima",
            "year": 2023,
            "color": "Yellow",
            "vin": "1HGCM82633A123460",
            "capacity": 4,
            "status": "ACTIVE"
        }
    ]
    
    print("\nCreating test vehicles...")
    print("=" * 60)
    
    for vehicle in vehicles:
        try:
            response = requests.post(f"{API_URL}/vehicles", json=vehicle, headers=headers)
            if response.status_code == 201:
                data = response.json()
                print(f"✓ Created: {vehicle['license_plate']} (ID: {data['id']})")
            else:
                print(f"✗ Failed: {vehicle['license_plate']} - {response.text}")
        except Exception as e:
            print(f"✗ Error creating {vehicle['license_plate']}: {e}")
    
    print("=" * 60)
    print("\nDone! You can now run the GPS simulator.")
    print("Run: python3 hardware/gps_simulator.py")


if __name__ == "__main__":
    print("TaxiWatch - Create Test Vehicles")
    print("=" * 60)
    
    token = get_auth_token()
    if token:
        print(f"✓ Authenticated successfully")
        create_vehicles(token)
    else:
        print("✗ Failed to authenticate")
