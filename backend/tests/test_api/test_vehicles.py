"""
Tests for vehicle endpoints.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_create_vehicle(client: AsyncClient, admin_user: User, admin_token: str):
    """Test creating a vehicle."""
    response = await client.post(
        "/api/v1/vehicles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "license_plate": "ABC-1234",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2023,
            "color": "White",
            "vin": "12345678901234567",
            "capacity": 4,
            "status": "ACTIVE"
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["license_plate"] == "ABC-1234"
    assert data["make"] == "Toyota"
    assert data["model"] == "Corolla"
    assert data["year"] == 2023


@pytest.mark.asyncio
async def test_create_vehicle_unauthenticated(client: AsyncClient):
    """Test creating vehicle without auth fails."""
    response = await client.post(
        "/api/v1/vehicles",
        json={
            "license_plate": "XYZ-5678",
            "make": "Honda",
            "model": "Civic",
            "year": 2022,
            "color": "Blue",
            "vin": "98765432109876543",
            "capacity": 4,
            "status": "ACTIVE"
        }
    )

    assert response.status_code in [401, 403]  # Unauthorized or Forbidden


@pytest.mark.asyncio
async def test_list_vehicles(client: AsyncClient, admin_user: User, admin_token: str):
    """Test listing vehicles."""
    # First create a vehicle
    await client.post(
        "/api/v1/vehicles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "license_plate": "TEST-001",
            "make": "Ford",
            "model": "Focus",
            "year": 2021,
            "color": "Red",
            "vin": "11111111111111111",
            "capacity": 4,
            "status": "ACTIVE"
        }
    )

    # Then list vehicles
    response = await client.get(
        "/api/v1/vehicles",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["license_plate"] == "TEST-001"


@pytest.mark.asyncio
async def test_get_vehicle_by_id(client: AsyncClient, admin_user: User, admin_token: str):
    """Test getting a vehicle by ID."""
    # Create vehicle
    create_response = await client.post(
        "/api/v1/vehicles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "license_plate": "GET-TEST",
            "make": "Chevrolet",
            "model": "Malibu",
            "year": 2020,
            "color": "Black",
            "vin": "22222222222222222",
            "capacity": 5,
            "status": "ACTIVE"
        }
    )
    vehicle_id = create_response.json()["id"]

    # Get vehicle
    response = await client.get(
        f"/api/v1/vehicles/{vehicle_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == vehicle_id
    assert data["license_plate"] == "GET-TEST"


@pytest.mark.asyncio
async def test_update_vehicle(client: AsyncClient, admin_user: User, admin_token: str):
    """Test updating a vehicle."""
    # Create vehicle
    create_response = await client.post(
        "/api/v1/vehicles",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "license_plate": "UPD-TEST",
            "make": "Nissan",
            "model": "Altima",
            "year": 2019,
            "color": "Silver",
            "vin": "33333333333333333",
            "capacity": 5,
            "status": "ACTIVE"
        }
    )
    vehicle_id = create_response.json()["id"]

    # Update vehicle
    response = await client.put(
        f"/api/v1/vehicles/{vehicle_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "MAINTENANCE",
            "color": "Gray"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "MAINTENANCE"
    assert data["color"] == "Gray"
    assert data["license_plate"] == "UPD-TEST"  # Unchanged fields remain
