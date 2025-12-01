"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "NewUser123!",
            "first_name": "New",
            "last_name": "User",
            "role": "OPERATOR"
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["username"] == "newuser"
    assert data["email"] == "newuser@test.com"
    assert "hashed_password" not in data  # Don't expose password
    assert data["role"] == "OPERATOR"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, admin_user: User):
    """Test registering with duplicate username fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin_test",  # Already exists
            "email": "different@test.com",
            "password": "Test123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "OPERATOR"
        }
    )

    assert response.status_code in [400, 409]  # Bad request or conflict


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user: User):
    """Test successful login returns JWT tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin_test",
            "password": "Admin123!"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user: User):
    """Test login with wrong password fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin_test",
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent user fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "doesnotexist",
            "password": "Test123!"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, admin_user: User):
    """Test refresh token endpoint."""
    # First login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin_test",
            "password": "Admin123!"
        }
    )
    refresh_token = login_response.json()["refresh_token"]

    # Then refresh
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert len(data["access_token"]) > 0
