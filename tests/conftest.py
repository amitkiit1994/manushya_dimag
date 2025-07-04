"""
Pytest configuration and fixtures for Manushya.ai
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from manushya.main import app
from manushya.db.database import get_db
from manushya.db.models import Base
from manushya.config import settings


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_manushya"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_session):
    """Create test client with database dependency override."""
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_identity_data():
    """Sample identity data for testing."""
    return {
        "external_id": "test-agent-001",
        "role": "agent",
        "claims": {"organization": "test-org", "environment": "test"}
    }


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing."""
    return {
        "text": "This is a test memory for unit testing",
        "type": "test",
        "metadata": {"category": "test", "priority": "low"},
        "ttl_days": 30
    }


@pytest.fixture
def sample_policy_data():
    """Sample policy data for testing."""
    return {
        "role": "test_role",
        "rule": {
            "and": [
                {"==": [{"var": "action"}, "read"]},
                {"==": [{"var": "resource"}, "memory"]}
            ]
        },
        "description": "Test policy for unit testing",
        "priority": 100,
        "is_active": True
    } 