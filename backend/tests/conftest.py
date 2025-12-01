"""
Pytest configuration and fixtures for testing.
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash


# Test database URL - use postgres container name when inside Docker, localhost otherwise
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
TEST_DATABASE_URL = f"postgresql+asyncpg://postgres:postgres@{DB_HOST}:5432/taxiwatch_test"

# Create async engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

# Create async session maker
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    Creates tables before each test and drops them after.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Yield session
    async with TestAsyncSessionLocal() as session:
        yield session

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client with database override.
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user = User(
        username="admin_test",
        email="admin@test.com",
        hashed_password=get_password_hash("Admin123!"),
        first_name="Admin",
        last_name="Test",
        role=UserRole.ADMIN,
        is_superuser=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def operator_user(db_session: AsyncSession) -> User:
    """Create an operator user for testing."""
    user = User(
        username="operator_test",
        email="operator@test.com",
        hashed_password=get_password_hash("Operator123!"),
        first_name="Operator",
        last_name="Test",
        role=UserRole.OPERATOR,
        is_superuser=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def admin_token(client: AsyncClient) -> str:
    """Get admin JWT token for authenticated requests."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin_test",
            "password": "Admin123!"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def operator_token(client: AsyncClient) -> str:
    """Get operator JWT token for authenticated requests."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "operator_test",
            "password": "Operator123!"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]
