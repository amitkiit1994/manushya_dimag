# Manushya.ai - Secure Identity + Memory Infrastructure

## 📚 Table of Contents
1. [Features](#features)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Quick Start](#quick-start)
5. [API Usage](#api-usage)
6. [SDK Usage](#sdk-usage)
7. [Performance Tuning](#performance-tuning)
8. [Features Matrix](#features-matrix)
9. [Security & Compliance](#security--compliance)
10. [Monitoring & Observability](#monitoring--observability)
11. [Development](#development)
12. [Production Deployment](#production-deployment)
13. [Troubleshooting](#troubleshooting)
14. [Contributing](#contributing)
15. [License & Support](#license--support)
16. [Roadmap](#roadmap)

---

## 🚀 Features

- **🔐 Multi-Tenant Identity Management**: Role-based, tenant-aware, JWT & SSO authentication
- **🧠 Memory Storage**: Vector-based semantic search with OpenAI embeddings, metadata, TTL, soft/hard delete
- **🤖 Embedding Service**: OpenAI integration with local fallback, async generation via Celery
- **📊 Usage Metering**: Billing-ready analytics and daily aggregation
- **📦 SDK Generation**: Python and TypeScript client libraries
- **📋 Policy Engine**: JSON Logic-based, priority, resource/action-level, caching
- **🔑 API Key Management**: Programmatic access, scopes, expiration, revocation, test endpoint
- **✉️ Invitations**: Email onboarding, token validation, acceptance, revocation, resend
- **🗝️ Sessions & Refresh Tokens**: Device info, session revocation, cleanup, refresh flow
- **📣 Identity Events & Audit Logging**: Async event publishing, delivery, retry, stats, GDPR
- **🌐 Real SSO Integration**: OAuth2/OIDC (Google, extensible)
- **🔔 Webhook System**: Real-time notifications, async delivery, HMAC, retries, stats
- **🚦 Rate Limiting**: Role/tenant-aware, Redis caching, admin/monitoring endpoints
- **📈 Monitoring & Analytics**: Prometheus metrics, health checks, admin endpoints
- **⚡ Background Tasks**: Celery for async jobs, retries, cleanup
- **🔒 Field-Level Encryption**: Fernet encryption for sensitive data
- **🐳 Containerized**: Docker Compose for easy deployment
- **🔄 GDPR Compliance**: Soft/hard delete, retention, audit trail
- **⚡ Performance Optimized**: HNSW vector indexing, Redis caching, connection pooling

---

## 🏗️ Architecture

### Core Modules
- **Identity**: Multi-role, multi-tenant, JWT, SSO, API keys, invitations
- **Memory**: Vector search with OpenAI embeddings, metadata, TTL, soft/hard delete
- **Embedding Service**: OpenAI integration with local fallback, async generation
- **Usage Metering**: Billing-ready analytics and daily aggregation
- **SDK Generation**: Python and TypeScript client libraries
- **Policy**: JSON Logic, RBAC, resource/action-level, priority, caching
- **Audit/Events**: Full audit trail, before/after state, GDPR, async events
- **Webhooks**: Register, update, deliveries, retry, stats, HMAC
- **Rate Limiting**: Role/tenant-aware, Redis, admin/monitoring endpoints
- **Monitoring**: Prometheus, health checks, analytics
- **Background Tasks**: Celery for async jobs, retries, cleanup

### Data Flow
- All endpoints are tenant-aware and enforce RBAC via the policy engine.
- All actions are logged for audit/compliance.
- Webhooks and events are triggered for all major changes.
- **Memory creation triggers async embedding generation via Celery.**
- **Usage events are tracked for billing and analytics.**

---

## 🛠️ Tech Stack
- **Language**: Python 3.10
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.x + Alembic
- **Database**: PostgreSQL (pgvector for vector search)
- **Cache/Queue**: Redis + Celery
- **Auth**: JWT, SSO (OAuth2/OIDC), API Keys
- **Policy Engine**: JSON Logic
- **Embedding**: OpenAI API + sentence-transformers fallback
- **Vector Search**: pgvector HNSW index
- **Monitoring**: Prometheus + Structlog
- **Containerization**: Docker + Docker Compose

---

## 📦 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.10
- Git
- OpenAI API key (optional, for embedding service)

### 1. Clone the Repository
```bash
git clone https://github.com/manushya-ai/dimag.git
cd dimag
```

### 2. Environment Setup
```bash
cp env.example .env
# Generate secure keys for production
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
# Optional: Add OpenAI API key for embedding service
OPENAI_API_KEY=your-openai-api-key
# Update .env with your generated keys
```

### 3. Start Services
```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f api
```

### 4. Verify Installation
```bash
curl http://localhost:8000/healthz
open http://localhost:8000/v1/docs
```

### 5. Create Your First Identity
```bash
curl -X POST "http://localhost:8000/v1/identity/" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "test-user",
    "role": "user"
  }'
```

---

## 🔌 API Usage

### Authentication Methods
- **JWT Tokens**: Bearer token authentication for user sessions
- **API Keys**: Programmatic access with scopes and expiration
- **Password Authentication**: Username/password with bcrypt hashing
- **Multi-Factor Authentication (MFA)**: TOTP-based with backup codes
- **SSO Integration**: OAuth2/OIDC (Google, extensible)

### Authentication Examples

#### Identity Creation and Authentication
```bash
# Create identity and get JWT token
curl -X POST "http://localhost:8000/v1/identity/" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "user@example.com",
    "role": "user",
    "claims": {
      "name": "John Doe",
      "department": "engineering"
    }
  }'

# Refresh JWT token
curl -X POST "http://localhost:8000/v1/sessions/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

#### Multi-Factor Authentication (MFA)
```bash
# Setup MFA (returns QR code and backup codes)
curl -X POST "http://localhost:8000/v1/auth/mfa/setup" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Verify MFA token
curl -X POST "http://localhost:8000/v1/auth/mfa/verify" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "123456"
  }'

# Disable MFA
curl -X DELETE "http://localhost:8000/v1/auth/mfa/disable" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Major Endpoint Groups
- **Identity**: `/v1/identity/` (CRUD, bulk, self, JWT, SSO)
- **API Keys**: `/v1/api-keys/` (CRUD, test)
- **Invitations**: `/v1/invitations/` (CRUD, validate, accept, resend)
- **Sessions**: `/v1/sessions/` (CRUD, refresh, cleanup, test)
- **Events**: `/v1/events/` (CRUD, by identity, types, stats, retry, cleanup, test)
- **Policy**: `/v1/policy/` (CRUD, bulk, test)
- **Memory**: `/v1/memory/` (CRUD, search, bulk)
- **Usage**: `/v1/usage/` (events, daily, summary, aggregate)
- **Webhooks**: `/v1/webhooks/` (CRUD, deliveries, retry, stats, events)
- **SSO**: `/v1/sso/` (login, callback)
- **Admin/Monitoring**: `/v1/admin/rate-limits`, `/v1/monitoring/`

### Example: Create Memory with Embedding
```bash
curl -X POST "http://localhost:8000/v1/memory/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Client meeting notes: Discussed retirement planning",
    "type": "meeting_note",
    "metadata": {
      "client_id": "CS001",
      "advisor": "advisor_001"
    }
  }'
```

**Note**: The embedding service automatically:
- Uses OpenAI API if `OPENAI_API_KEY` is configured
- Falls back to local sentence-transformers if OpenAI fails or is not configured
- Falls back to hash-based embeddings if sentence-transformers is not available
- Handles errors gracefully and continues without embedding if all methods fail

### Example: Search Memories with Vector Similarity
```bash
curl -X POST "http://localhost:8000/v1/memory/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "retirement planning",
    "similarity_threshold": 0.7,
    "limit": 10
  }'
```

### Example: Get Usage Analytics
```bash
curl -X GET "http://localhost:8000/v1/usage/summary?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example: Create API Key
```bash
curl -X POST "http://localhost:8000/v1/api-keys/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key",
    "scopes": ["read", "write"],
    "expires_in_days": 365
  }'
```

### Example: Initiate SSO Login
```bash
curl -X GET "http://localhost:8000/v1/sso/login/google"
# This will redirect to Google's OAuth2 authorization page
```

### Example: Register Webhook
```bash
curl -X POST "http://localhost:8000/v1/webhooks/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Identity Events Webhook",
    "url": "https://webhook.site/your-url",
    "events": ["identity.created", "identity.updated"]
  }'
```

---

## 📦 SDK Usage

### Python SDK

```python
from sdk.python.client import Client
from sdk.python.api.identity.create_identity_v1_identity_post import sync_detailed as create_identity
from sdk.python.models.identity_create import IdentityCreate
from sdk.python.models.identity_create_claims import IdentityCreateClaims

# Create an unauthenticated client for identity creation
client = Client(base_url="http://localhost:8000")
claims = IdentityCreateClaims()
claims["email"] = "user@example.com"
identity_data = IdentityCreate(external_id="user-123", role="user", claims=claims)
identity_resp = create_identity(client=client, body=identity_data)
access_token = identity_resp.parsed.access_token

# Use the access token for authenticated requests
client = Client(base_url="http://localhost:8000", headers={"Authorization": f"Bearer {access_token}"})

# Create a memory
from sdk.python.api.memory.create_memory_v1_memory_post import sync_detailed as create_memory
from sdk.python.models.memory_create import MemoryCreate
from sdk.python.models.memory_create_metadata import MemoryCreateMetadata

metadata = MemoryCreateMetadata()
metadata["source"] = "sdk-test"
memory_data = MemoryCreate(text="Test memory", type_="note", metadata=metadata)
response = create_memory(client=client, body=memory_data)
print(response.status_code, response.parsed)
```

### TypeScript SDK
```typescript
import { ManushyaClient } from '@manushya/sdk';

const client = new ManushyaClient({
    apiKey: 'your-api-key',
    baseUrl: 'https://api.manushya.ai'
});

// Create memory with embedding
const memory = await client.memory.create({
    text: 'Investment recommendation for high-net-worth client',
    type: 'investment_recommendation',
    metadata: { clientId: 'CS002' }
});

// Search with vector similarity
const searchResults = await client.memory.search({
    query: 'high net worth investment',
    similarityThreshold: 0.8,
    limit: 5
});

// Get usage analytics
const usage = await client.usage.getSummary({ days: 30 });
```

### SDK Installation
```bash
# Python SDK
pip install -e sdk/python

# TypeScript SDK
npm install @manushya/sdk
```

---

**Note:** The generated Python SDK is low-level and does not provide a high-level `ManushyaClient` abstraction. You must use the endpoint modules and models directly as shown above.

---

## ⚡ Performance Tuning

### Database Optimization
```sql
-- Optimize for vector operations
ALTER SYSTEM SET shared_preload_libraries = 'pgvector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Create optimized HNSW index
CREATE INDEX CONCURRENTLY idx_memories_vector_hnsw 
ON memories USING hnsw (vector) 
WITH (m = 16, ef_construction = 64, ef = 40);
```

### Redis Configuration
```bash
# Redis configuration for high throughput
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Application Performance
```python
# Celery configuration for high throughput
CELERY_CONFIG = {
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
    'task_acks_late': True,
    'worker_concurrency': 8,
}
```

### Scaling Strategies
```yaml
# docker-compose.yml for production scaling
services:
  api:
    image: manushya-api
    deploy:
      replicas: 3
  celery-worker:
    image: manushya-api
    command: celery -A manushya.tasks.celery_app worker --concurrency=8
    deploy:
      replicas: 4
```

For detailed performance tuning guidance, see [PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md).

---

## 🗂️ Features Matrix

| Feature                | Description                                      | Status |
|------------------------|--------------------------------------------------|--------|
| Multi-tenancy          | Tenant isolation, tenant_id on all models        | ✅     |
| API Keys               | Create, list, update, revoke, test, scopes       | ✅     |
| Invitations            | Email, accept, validate, revoke, resend          | ✅     |
| Sessions               | Refresh tokens, revoke, cleanup, test            | ✅     |
| Identity Events        | Publish, retry, stats, types, by identity        | ✅     |
| Rate Limiting          | Role/tenant-aware, Redis, admin/monitoring       | ✅     |
| SSO Integration        | OAuth2/OIDC (Google), extensible                 | ✅     |
| Webhooks               | Register, update, deliveries, retry, stats       | ✅     |
| Policy Engine          | JSON Logic, priority, caching, test endpoint     | ✅     |
| Memory System          | Vector search, metadata, TTL, soft/hard delete   | ✅     |
| **Embedding Service**  | **OpenAI integration with local fallback**       | ✅     |
| **Usage Metering**     | **Billing-ready analytics and aggregation**      | ✅     |
| **SDK Generation**     | **Python and TypeScript client libraries**       | ✅     |
| Audit Logging          | Full trail, before/after, GDPR, retention        | ✅     |
| Monitoring             | Prometheus metrics, health checks, analytics     | ✅     |
| Background Tasks       | Celery for async jobs, retries, cleanup         | ✅     |

---

## 🔒 Security & Compliance
- **JWT, SSO, API Key Auth**: All endpoints require authentication
- **Role & Policy Engine**: JSON Logic, RBAC, resource/action-level
- **Audit Logging**: All actions logged, before/after state, GDPR
- **Encryption**: Field-level for sensitive data
- **Rate Limiting**: Global, role/tenant-aware, Redis-backed
- **Webhook Security**: HMAC signatures, tenant isolation
- **Compliance**: Retention, tamper-evident logs, GDPR

## 🛡️ Error Handling & Resilience
- **Circuit Breakers**: Automatic failure detection and recovery
- **Retry Mechanisms**: Exponential backoff for transient failures
- **Graceful Degradation**: Service continues with reduced functionality
- **Health Checks**: Comprehensive system health monitoring
- **Error Tracking**: Centralized error handling and logging
- **Fallback Strategies**: Multiple embedding backends and authentication methods

---

## 📈 Monitoring & Observability
- **Health Checks**: `/healthz`
- **Prometheus Metrics**: `/metrics`
- **Admin/Monitoring Endpoints**: `/v1/admin/rate-limits`, `/v1/monitoring/`
- **Usage Analytics**: `/v1/usage/` endpoints
- **Performance Monitoring**: Custom metrics for embedding and vector search

---

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn manushya.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker
celery -A manushya.tasks.celery_app worker --loglevel=info

# Start Celery beat
celery -A manushya.tasks.celery_app beat --loglevel=info
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=manushya

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/performance/   # Performance tests

# Run specific test
pytest tests/unit/test_memory.py::test_create_memory

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Test Coverage
- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: End-to-end API testing with real database
- **Performance Tests**: Load testing and performance benchmarks
- **Security Tests**: Authentication, authorization, and security validation
- **Error Handling Tests**: Circuit breakers, retries, and fallback scenarios

### Code Quality
```bash
# Format code
black manushya/

# Lint code
flake8 manushya/

# Type checking
mypy manushya/
```

### CI/CD Pipeline
The project includes a comprehensive CI/CD pipeline with:
- **Automated Testing**: Unit, integration, and performance tests
- **Code Quality**: Linting, formatting, and type checking
- **Security Scanning**: Bandit, Safety, Trivy, and OWASP ZAP
- **Docker Builds**: Multi-stage production builds
- **Deployment**: Automated staging and production deployments
- **Monitoring**: Slack notifications for build status

See `.github/workflows/ci.yml` for the complete pipeline configuration.

---

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build and deploy with production Dockerfile
docker build -f Dockerfile.prod -t manushya-api:latest .

# Run with production settings
docker run -d \
  --name manushya-api \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e JWT_SECRET_KEY=your-jwt-secret \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379/0 \
  manushya-api:latest

# Or use docker-compose for production
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### Environment Variables
```bash
# Required for production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# Optional for embedding service
OPENAI_API_KEY=your-openai-api-key

# Optional for SSO
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Performance Optimization
- Enable HNSW vector indexing
- Configure Redis for caching
- Set up Celery workers for background tasks
- Monitor with Prometheus and Grafana
- Use load balancer for horizontal scaling

For detailed deployment guidance, see [PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md).

---

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec api python -c "
from manushya.db.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT 1'))
        print('Database connection successful')
asyncio.run(test())
"
```

#### Redis Connection Issues
```bash
# Check Redis connectivity
docker-compose exec api python -c "
from manushya.core.redis_client import get_redis
import asyncio
async def test():
    redis = get_redis()
    await redis.ping()
    print('Redis connection successful')
asyncio.run(test())
"
```

#### Embedding Service Issues
```bash
# Check OpenAI API key
curl -H "Authorization: Bearer YOUR_OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Test local embedding fallback
docker-compose exec api python -c "
from manushya.services.embedding import generate_embedding
result = generate_embedding('test', backend='local')
print(f'Local embedding generated: {len(result)} dimensions')
"
```

### Performance Issues

#### Slow Vector Search
```sql
-- Check HNSW index performance
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE indexname = 'idx_memories_vector_hnsw';

-- Analyze table statistics
ANALYZE memories;
```

#### High Memory Usage
```bash
# Check Redis memory usage
docker-compose exec redis redis-cli info memory

# Check application memory
docker-compose exec api ps aux
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Add tests for new features
- Update documentation
- Ensure all tests pass
- Add type hints where appropriate

---

## 📄 License & Support

- **License**: MIT License
- **Support**: GitHub Issues
- **Documentation**: [MANUSHYA_AI_SYSTEM_DOCUMENTATION.md](MANUSHYA_AI_SYSTEM_DOCUMENTATION.md)
- **SDK Documentation**: [SDK_README.md](SDK_README.md)
- **Performance Guide**: [PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md)

---

## 🗺️ Roadmap

### Completed ✅
- Multi-tenant identity system
- Vector-based memory storage
- OpenAI embedding integration
- Usage metering and billing
- SDK generation (Python & TypeScript)
- Policy engine with JSON Logic
- Comprehensive audit logging
- Webhook system
- Rate limiting
- SSO integration
- Background task processing

### Planned 🚧
- Advanced analytics dashboard
- Machine learning model integration
- Real-time collaboration features
- Advanced security features
- Multi-region deployment
- Advanced caching strategies
- Performance optimization tools
- Developer portal
- Advanced webhook features
- Integration marketplace

---

*For detailed API documentation, see the OpenAPI docs at `/v1/docs` when running the server.* 