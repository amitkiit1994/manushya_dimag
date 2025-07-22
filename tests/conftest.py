"""
Test configuration and fixtures for Manushya.ai
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from manushya.config import settings
from manushya.db.database import Base, get_db
from manushya.db.models import (
    ApiKey,
    Identity,
    Memory,
    Policy,
    Tenant,
    UsageEvent,
    Webhook,
)
from manushya.main import app


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_manushya"
TEST_REDIS_URL = "redis://localhost:6379/1"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create test session
TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_setup():
    """Set up test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(test_db_setup) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client(db_session: AsyncSession) -> Generator:
    """Create a test client with database dependency override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Test data fixtures
@pytest.fixture
def test_tenant() -> dict:
    """Create test tenant data."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Tenant",
        "created_by": str(uuid.uuid4()),
    }


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession, test_tenant: dict) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        id=uuid.UUID(test_tenant["id"]),
        name=test_tenant["name"],
        created_by=uuid.UUID(test_tenant["created_by"]),
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_identity() -> dict:
    """Create test identity data."""
    return {
        "external_id": "test-user-001",
        "role": "user",
        "claims": {"department": "engineering", "level": "senior"},
        "is_active": True,
    }


@pytest_asyncio.fixture
async def identity(db_session: AsyncSession, tenant: Tenant, test_identity: dict) -> Identity:
    """Create a test identity."""
    identity = Identity(
        external_id=test_identity["external_id"],
        role=test_identity["role"],
        claims=test_identity["claims"],
        is_active=test_identity["is_active"],
        tenant_id=tenant.id,
    )
    db_session.add(identity)
    await db_session.commit()
    await db_session.refresh(identity)
    return identity


@pytest.fixture
def test_memory() -> dict:
    """Create test memory data."""
    return {
        "text": "This is a test memory for unit testing",
        "type": "test_memory",
        "metadata": {"test": True, "category": "unit_test"},
        "ttl_days": 30,
    }


@pytest_asyncio.fixture
async def memory(db_session: AsyncSession, identity: Identity, test_memory: dict) -> Memory:
    """Create a test memory."""
    memory = Memory(
        identity_id=identity.id,
        text=test_memory["text"],
        type=test_memory["type"],
        meta_data=test_memory["metadata"],
        ttl_days=test_memory["ttl_days"],
        tenant_id=identity.tenant_id,
    )
    db_session.add(memory)
    await db_session.commit()
    await db_session.refresh(memory)
    return memory


@pytest.fixture
def test_policy() -> dict:
    """Create test policy data."""
    return {
        "role": "user",
        "rule": {
            "and": [
                {"in": [{"var": "action"}, ["read", "write"]]},
                {"==": [{"var": "resource"}, "memory"]},
            ]
        },
        "description": "Test policy for users",
        "priority": 100,
        "is_active": True,
    }


@pytest_asyncio.fixture
async def policy(db_session: AsyncSession, tenant: Tenant, test_policy: dict) -> Policy:
    """Create a test policy."""
    policy = Policy(
        role=test_policy["role"],
        rule=test_policy["rule"],
        description=test_policy["description"],
        priority=test_policy["priority"],
        is_active=test_policy["is_active"],
        tenant_id=tenant.id,
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)
    return policy


@pytest.fixture
def test_api_key() -> dict:
    """Create test API key data."""
    return {
        "name": "Test API Key",
        "scopes": ["read", "write"],
        "is_active": True,
        "expires_at": datetime.utcnow() + timedelta(days=30),
    }


@pytest_asyncio.fixture
async def api_key(db_session: AsyncSession, identity: Identity, test_api_key: dict) -> ApiKey:
    """Create a test API key."""
    api_key = ApiKey(
        name=test_api_key["name"],
        key_hash="test_hash_12345",  # In real tests, this would be hashed
        identity_id=identity.id,
        scopes=test_api_key["scopes"],
        is_active=test_api_key["is_active"],
        expires_at=test_api_key["expires_at"],
        tenant_id=identity.tenant_id,
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    return api_key


@pytest.fixture
def test_webhook() -> dict:
    """Create test webhook data."""
    return {
        "name": "Test Webhook",
        "url": "https://webhook.site/test",
        "events": ["memory.created", "memory.updated"],
        "secret": "test_secret_123",
        "is_active": True,
    }


@pytest_asyncio.fixture
async def webhook(db_session: AsyncSession, identity: Identity, tenant: Tenant, test_webhook: dict) -> Webhook:
    """Create a test webhook."""
    webhook = Webhook(
        name=test_webhook["name"],
        url=test_webhook["url"],
        events=test_webhook["events"],
        secret=test_webhook["secret"],
        is_active=test_webhook["is_active"],
        created_by=identity.id,
        tenant_id=tenant.id,
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)
    return webhook


@pytest.fixture
def test_usage_event() -> dict:
    """Create test usage event data."""
    return {
        "event": "memory.created",
        "units": 1,
        "event_metadata": {"memory_type": "test", "size": 100},
    }


@pytest_asyncio.fixture
async def usage_event(db_session: AsyncSession, tenant: Tenant, test_usage_event: dict) -> UsageEvent:
    """Create a test usage event."""
    usage_event = UsageEvent(
        tenant_id=tenant.id,
        event=test_usage_event["event"],
        units=test_usage_event["units"],
        event_metadata=test_usage_event["event_metadata"],
    )
    db_session.add(usage_event)
    await db_session.commit()
    await db_session.refresh(usage_event)
    return usage_event


# Authentication fixtures
@pytest.fixture
def admin_identity_data() -> dict:
    """Create admin identity data."""
    return {
        "external_id": "admin@test.com",
        "role": "admin",
        "claims": {"department": "it", "level": "admin"},
        "is_active": True,
    }


@pytest_asyncio.fixture
async def admin_identity(db_session: AsyncSession, tenant: Tenant, admin_identity_data: dict) -> Identity:
    """Create an admin identity."""
    identity = Identity(
        external_id=admin_identity_data["external_id"],
        role=admin_identity_data["role"],
        claims=admin_identity_data["claims"],
        is_active=admin_identity_data["is_active"],
        tenant_id=tenant.id,
    )
    db_session.add(identity)
    await db_session.commit()
    await db_session.refresh(identity)
    return identity


@pytest.fixture
def user_identity_data() -> dict:
    """Create user identity data."""
    return {
        "external_id": "user@test.com",
        "role": "user",
        "claims": {"department": "engineering", "level": "junior"},
        "is_active": True,
    }


@pytest_asyncio.fixture
async def user_identity(db_session: AsyncSession, tenant: Tenant, user_identity_data: dict) -> Identity:
    """Create a user identity."""
    identity = Identity(
        external_id=user_identity_data["external_id"],
        role=user_identity_data["role"],
        claims=user_identity_data["claims"],
        is_active=user_identity_data["is_active"],
        tenant_id=tenant.id,
    )
    db_session.add(identity)
    await db_session.commit()
    await db_session.refresh(identity)
    return identity


# JWT token fixtures
@pytest.fixture
def admin_jwt_token(admin_identity: Identity) -> str:
    """Create JWT token for admin."""
    from manushya.core.auth import create_access_token
    return create_access_token({"sub": str(admin_identity.id)})


@pytest.fixture
def user_jwt_token(user_identity: Identity) -> str:
    """Create JWT token for user."""
    from manushya.core.auth import create_access_token
    return create_access_token({"sub": str(user_identity.id)})


# API key fixtures
@pytest.fixture
def admin_api_key_data() -> dict:
    """Create admin API key data."""
    return {
        "name": "Admin API Key",
        "scopes": ["read", "write", "admin"],
        "is_active": True,
        "expires_at": datetime.utcnow() + timedelta(days=365),
    }


@pytest_asyncio.fixture
async def admin_api_key(db_session: AsyncSession, admin_identity: Identity, admin_api_key_data: dict) -> ApiKey:
    """Create an admin API key."""
    api_key = ApiKey(
        name=admin_api_key_data["name"],
        key_hash="admin_hash_12345",
        identity_id=admin_identity.id,
        scopes=admin_api_key_data["scopes"],
        is_active=admin_api_key_data["is_active"],
        expires_at=admin_api_key_data["expires_at"],
        tenant_id=admin_identity.tenant_id,
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    return api_key


@pytest.fixture
def user_api_key_data() -> dict:
    """Create user API key data."""
    return {
        "name": "User API Key",
        "scopes": ["read", "write"],
        "is_active": True,
        "expires_at": datetime.utcnow() + timedelta(days=30),
    }


@pytest_asyncio.fixture
async def user_api_key(db_session: AsyncSession, user_identity: Identity, user_api_key_data: dict) -> ApiKey:
    """Create a user API key."""
    api_key = ApiKey(
        name=user_api_key_data["name"],
        key_hash="user_hash_12345",
        identity_id=user_identity.id,
        scopes=user_api_key_data["scopes"],
        is_active=user_api_key_data["is_active"],
        expires_at=user_api_key_data["expires_at"],
        tenant_id=user_identity.tenant_id,
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    return api_key


# Mock external services
@pytest.fixture
def mock_openai_response():
    """Mock OpenAI embedding response."""
    return {
        "data": [
            {
                "embedding": [0.1] * 1536,  # OpenAI ada-002 dimension
                "index": 0,
                "object": "embedding"
            }
        ],
        "model": "text-embedding-ada-002",
        "object": "list",
        "usage": {
            "prompt_tokens": 5,
            "total_tokens": 5
        }
    }


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    class MockRedis:
        async def ping(self):
            return True
        
        async def get(self, key):
            return None
        
        async def set(self, key, value, ex=None):
            return True
        
        async def incr(self, key):
            return 1
        
        async def expire(self, key, seconds):
            return True
    
    return MockRedis()


# Test utilities
def create_test_memory_data(text: str = "Test memory", memory_type: str = "test") -> dict:
    """Create test memory data."""
    return {
        "text": text,
        "type": memory_type,
        "metadata": {"test": True, "category": "unit_test"},
        "ttl_days": 30,
    }


def create_test_identity_data(external_id: str = "test-user", role: str = "user") -> dict:
    """Create test identity data."""
    return {
        "external_id": external_id,
        "role": role,
        "claims": {"department": "engineering", "level": "senior"},
        "is_active": True,
    }


def create_test_policy_data(role: str = "user", action: str = "read", resource: str = "memory") -> dict:
    """Create test policy data."""
    return {
        "role": role,
        "rule": {
            "and": [
                {"in": [{"var": "action"}, [action]]},
                {"==": [{"var": "resource"}, resource]},
            ]
        },
        "description": f"Test policy for {role}",
        "priority": 100,
        "is_active": True,
    } 