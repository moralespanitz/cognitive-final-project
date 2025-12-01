"""
Tests for health check endpoint.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint returns 200 OK."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["app"] == "TaxiWatch API"
    assert data["version"] == "2.0.0"
    assert "environment" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns welcome message."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "TaxiWatch" in data["message"]
    assert "version" in data
