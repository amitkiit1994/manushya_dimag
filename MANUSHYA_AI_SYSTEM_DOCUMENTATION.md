# Manushya.ai System Documentation

## 📚 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Features Matrix](#features-matrix)
4. [REST API Endpoint Reference](#rest-api-endpoint-reference)
5. [Core Workflows](#core-workflows)
6. [Security & Compliance](#security--compliance)
7. [Advanced Features](#advanced-features)
8. [SDK Usage Examples](#sdk-usage-examples)
9. [Performance Tuning](#performance-tuning)
10. [Deployment & Infrastructure](#deployment--infrastructure)
11. [Best Practices](#best-practices)

---

## 🎯 System Overview

Manushya.ai is a secure, multi-tenant identity and memory infrastructure for autonomous AI agents and enterprise applications. It provides:
- Robust identity management (multi-role, multi-tenant)
- **Vector-based memory storage with OpenAI embeddings and semantic search**
- JSON Logic policy engine for fine-grained access control
- Comprehensive audit logging and compliance
- API key management, invitation flows, session management
- Real SSO (OAuth2/OIDC) integration
- Webhook system for real-time notifications
- Rate limiting, monitoring, and background tasks
- **Usage metering for billing and analytics**
- **SDK generation for Python and TypeScript**

---

## 🏗️ Architecture

### Core Modules
- **Identity Management**: Multi-role, multi-tenant, JWT auth, claims, SSO
- **Memory Storage**: Vector search with OpenAI embeddings, metadata, TTL, soft/hard delete
- **Policy Engine**: JSON Logic, RBAC, resource/action-level, priority, caching
- **Audit & Compliance**: Full audit trail, before/after state, GDPR, retention
- **API Keys**: Programmatic access, scopes, expiration, revocation
- **Invitations**: Email onboarding, token validation, acceptance, revocation
- **Sessions**: Refresh tokens, device info, session revocation, cleanup
- **Identity Events**: Async event publishing, delivery, retry, stats
- **Webhooks**: Real-time notifications, async delivery, HMAC, retries
- **Rate Limiting**: Role/tenant-aware, Redis caching, admin/monitoring endpoints
- **Monitoring**: Prometheus metrics, health checks, analytics
- **Background Tasks**: Celery for async jobs, cleanup, retries
- **Embedding Service**: OpenAI integration with local fallback
- **Usage Metering**: Billing-ready analytics and aggregation
- **SDK Generation**: Python and TypeScript client libraries

### Data Flow
- All endpoints are tenant-aware and enforce RBAC via the policy engine.
- All actions are logged for audit/compliance.
- Webhooks and events are triggered for all major changes.
- **Memory creation triggers async embedding generation via Celery.**
- **Usage events are tracked for billing.**

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

## 📑 REST API Endpoint Reference

### System & Monitoring
| Endpoint                  | Method | Description                       |
|---------------------------|--------|-----------------------------------|
| `/healthz`                 | GET    | Health check                      |
| `/metrics`                | GET    | Prometheus metrics                |
| `/`                       | GET    | Root info                         |
| `/v1/admin/rate-limits`   | GET    | List all rate limits (admin)      |
| `/v1/admin/rate-limits`   | DELETE | Clear all rate limits (admin)     |
| `/v1/monitoring/rate-limits` | GET | Get current rate limit info       |
| `/v1/monitoring/usage`    | GET    | API usage analytics               |

### Identity & Authentication
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/identity/`                  | POST   | Create identity                   |
| `/v1/identity/`                  | GET    | List identities                   |
| `/v1/identity/{id}`              | GET    | Get identity by ID                |
| `/v1/identity/{id}`              | DELETE | Delete identity (soft/hard)       |
| `/v1/identity/me`                | GET    | Get current identity              |
| `/v1/identity/me`                | PUT    | Update current identity           |
| `/v1/identity/bulk-delete`       | POST   | Bulk delete identities            |

### API Keys
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/api-keys/`                  | POST   | Create API key                    |
| `/v1/api-keys/`                  | GET    | List API keys                     |
| `/v1/api-keys/{id}`              | GET    | Get API key                       |
| `/v1/api-keys/{id}`              | PUT    | Update API key                    |
| `/v1/api-keys/{id}`              | DELETE | Revoke API key                    |
| `/v1/api-keys/test`              | POST   | Test API key endpoint             |

### Invitations
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/invitations/`               | POST   | Create invitation                 |
| `/v1/invitations/`               | GET    | List invitations                  |
| `/v1/invitations/{id}`           | GET    | Get invitation                    |
| `/v1/invitations/{id}`           | DELETE | Revoke invitation                 |
| `/v1/invitations/validate/{token}` | GET  | Validate invitation token         |
| `/v1/invitations/accept/{token}` | POST   | Accept invitation                 |
| `/v1/invitations/resend/{id}`    | POST   | Resend invitation                 |

### Sessions
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/sessions/`                  | GET    | List sessions                     |
| `/v1/sessions/{id}`              | GET    | Get session                       |
| `/v1/sessions/{id}`              | DELETE | Revoke session                    |
| `/v1/sessions/`                  | DELETE | Revoke all sessions               |
| `/v1/sessions/refresh`           | POST   | Refresh token                     |
| `/v1/sessions/cleanup`           | POST   | Cleanup expired sessions          |
| `/v1/sessions/test`              | POST   | Test session authentication       |

### Events
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/events/`                    | GET    | List events                       |
| `/v1/events/{id}`                | GET    | Get event                         |
| `/v1/events/identity/{id}`       | GET    | Get events by identity            |
| `/v1/events/types`               | GET    | List event types                  |
| `/v1/events/stats`               | GET    | Event statistics                  |
| `/v1/events/{id}/retry`          | POST   | Retry event delivery              |
| `/v1/events/cleanup`             | POST   | Cleanup old events                |
| `/v1/events/test`                | POST   | Test event publishing             |

### Policy
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/policy/`                    | POST   | Create policy                     |
| `/v1/policy/`                    | GET    | List policies                     |
| `/v1/policy/{id}`                | GET    | Get policy                        |
| `/v1/policy/{id}`                | PUT    | Update policy                     |
| `/v1/policy/{id}`                | DELETE | Delete policy                     |
| `/v1/policy/bulk-delete`         | POST   | Bulk delete policies              |
| `/v1/policy/test`                | POST   | Test policy evaluation            |

### Memory
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/memory/`                    | POST   | Create memory                     |
| `/v1/memory/`                    | GET    | List memories                     |
| `/v1/memory/{id}`                | GET    | Get memory                        |
| `/v1/memory/{id}`                | PUT    | Update memory                     |
| `/v1/memory/{id}`                | DELETE | Delete memory (soft/hard)         |
| `/v1/memory/search`              | POST   | Search memories                   |
| `/v1/memory/bulk-delete`         | POST   | Bulk delete memories              |

### **Usage Metering**
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/usage/events`               | GET    | Get usage events                  |
| `/v1/usage/daily`                | GET    | Get daily usage aggregation       |
| `/v1/usage/summary`              | GET    | Get usage summary                 |
| `/v1/usage/aggregate`            | POST   | Trigger usage aggregation         |
| `/v1/usage/admin/all-tenants`    | GET    | Get all tenants usage (admin)     |

### SSO
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/sso/login/{provider}`       | GET    | Initiate SSO login                |
| `/v1/sso/callback/{provider}`    | GET    | SSO callback                      |

### Webhooks
| Endpoint                        | Method | Description                       |
|----------------------------------|--------|-----------------------------------|
| `/v1/webhooks/`                  | POST   | Create webhook                    |
| `/v1/webhooks/`                  | GET    | List webhooks                     |
| `/v1/webhooks/{id}`              | GET    | Get webhook                       |
| `/v1/webhooks/{id}`              | PUT    | Update webhook                    |
| `/v1/webhooks/{id}`              | DELETE | Delete webhook                    |
| `/v1/webhooks/{id}/deliveries`   | GET    | List webhook deliveries           |
| `/v1/webhooks/{id}/deliveries/{delivery_id}/retry` | POST | Retry webhook delivery |
| `/v1/webhooks/stats`             | GET    | Webhook statistics                |
| `/v1/webhooks/events`            | GET    | Supported webhook events          |

---

## 🔄 Core Workflows

### Identity Creation & Authentication
1. Create identity (POST /v1/identity/)
2. Receive JWT token
3. Use token for all subsequent requests

### Memory Creation & Search
1. Authenticate and POST /v1/memory/
2. **Memory is stored with OpenAI embedding generation**
3. **Async embedding generation via Celery background task**
4. Search via POST /v1/memory/search with vector similarity
5. **Usage events tracked for billing**

### Policy Evaluation
1. Request arrives with JWT/API key
2. Policy engine loads and evaluates JSON Logic rules
3. Access granted/denied, audit logged

### API Key Flow
1. Admin creates API key (POST /v1/api-keys/)
2. Use X-API-Key header for programmatic access

### Invitation Flow
1. Admin invites user (POST /v1/invitations/)
2. User receives email, accepts via token
3. Identity is provisioned

### Session & Refresh Token Flow
1. Identity creation returns access + refresh tokens
2. Use refresh token to get new access token
3. Revoke sessions as needed

### Event & Webhook Flow
1. Actions trigger events (identity, memory, etc.)
2. Events are delivered to webhooks asynchronously
3. Delivery, retry, and stats tracked

### SSO Flow
1. User initiates SSO login (/v1/sso/login/{provider})
2. Provider redirects to callback
3. System provisions/updates user, returns tokens

### Rate Limiting & Monitoring
1. All requests checked against rate limits
2. Headers returned with rate limit info
3. Admin/monitoring endpoints for analytics

### **Usage Metering Flow**
1. **API calls tracked in usage_events table**
2. **Daily aggregation via Celery beat**
3. **Billing analytics available via /v1/usage/ endpoints**

---

## 🔒 Security & Compliance
- **JWT & API Key Auth**: All endpoints require authentication
- **Role & Policy Engine**: JSON Logic, RBAC, resource/action-level
- **Audit Logging**: All actions logged, before/after state, GDPR
- **Encryption**: Field-level for sensitive data
- **Rate Limiting**: Global, role/tenant-aware, Redis-backed
- **Webhook Security**: HMAC signatures, tenant isolation
- **Compliance**: Retention, tamper-evident logs, GDPR

---

## 🚀 Advanced Features
- **Multi-tenancy**: All data and endpoints are tenant-aware
- **API Keys**: Scopes, expiration, revocation, test endpoint
- **Invitations**: Email onboarding, token validation, acceptance, revocation
- **Sessions**: Refresh tokens, device info, session revocation, cleanup
- **Identity Events**: Async event publishing, delivery, retry, stats
- **Webhooks**: Real-time notifications, async delivery, HMAC, retries
- **Rate Limiting**: Role/tenant-aware, Redis caching, admin/monitoring endpoints
- **Monitoring**: Prometheus metrics, health checks, analytics
- **Background Tasks**: Celery for async jobs, cleanup, retries
- **Production Readiness**: Docker, env config, logging, migrations
- **Embedding Service**: OpenAI integration with local fallback
- **Usage Metering**: Billing-ready analytics and aggregation
- **SDK Generation**: Python and TypeScript client libraries

---

## 📚 SDK Usage Examples

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

# Initialize client with JWT token
const client = new ManushyaClient({
    jwtToken: 'your-jwt-token',
    baseUrl: 'https://api.manushya.ai'
});

# Create memory with embedding
const memory = await client.memory.create({
    text: 'Investment recommendation for high-net-worth client',
    type: 'investment_recommendation',
    metadata: {
        clientId: 'CS002',
        riskLevel: 'high',
        portfolioSize: '$2M+'
    }
});

# Search with vector similarity
const searchResults = await client.memory.search({
    query: 'high net worth investment',
    similarityThreshold: 0.8,
    limit: 5
});

# Get usage analytics
const usage = await client.usage.getSummary({
    days: 30
});

# Create API key
const apiKey = await client.apiKeys.create({
    name: 'Production API Key',
    scopes: ['read', 'write'],
    expiresInDays: 365
});
```

### SDK Features
- **Authentication**: JWT tokens and API keys
- **Memory Management**: CRUD operations with vector search
- **Identity Management**: Multi-role identity system
- **Policy Testing**: JSON Logic policy evaluation
- **Usage Analytics**: Billing and usage tracking
- **Webhook Management**: Real-time notifications
- **Rate Limiting**: Built-in rate limit handling

---

### Note
The generated Python SDK is low-level and does not provide a high-level `ManushyaClient` abstraction. You must use the endpoint modules and models directly as shown above.

---

## ⚡ Performance Tuning

### Database Optimization

#### PostgreSQL Configuration
```sql
-- Optimize for vector operations
ALTER SYSTEM SET shared_preload_libraries = 'pgvector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';

-- Restart PostgreSQL after changes
SELECT pg_reload_conf();
```

#### HNSW Index Optimization
```sql
-- Create optimized HNSW index for 100M+ scale
CREATE INDEX CONCURRENTLY idx_memories_vector_hnsw 
ON memories USING hnsw (vector) 
WITH (m = 16, ef_construction = 64, ef = 40);

-- Monitor index performance
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE indexname = 'idx_memories_vector_hnsw';
```

### Redis Configuration

#### Memory Optimization
```bash
# Redis configuration for high throughput
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Connection Pooling
```python
# Optimize Redis connections
import redis.asyncio as redis

redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50,
    retry_on_timeout=True,
    health_check_interval=30
)
```

### Application Performance

#### Celery Worker Optimization
```python
# Celery configuration for high throughput
CELERY_CONFIG = {
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'broker_connection_retry_on_startup': True,
    'result_expires': 3600,
}
```

#### Rate Limiting Tuning
```python
# Optimize rate limiting for high traffic
RATE_LIMITS = {
    "memory:create": {"limit": 1000, "window": 3600},  # 1000 per hour
    "memory:search": {"limit": 2000, "window": 3600},  # 2000 per hour
    "identity:create": {"limit": 100, "window": 3600},  # 100 per hour
}
```

### Scaling Strategies

#### Horizontal Scaling
```yaml
# docker-compose.yml for production scaling
services:
  api:
    image: manushya-api
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/manushya
      - REDIS_URL=redis://redis:6379/0
  
  celery-worker:
    image: manushya-api
    command: celery -A manushya.tasks.celery_app worker --loglevel=info --concurrency=8
    deploy:
      replicas: 4
```

#### Database Scaling
```sql
-- Read replicas for scaling
-- Primary: Write operations
-- Replica 1: Read operations
-- Replica 2: Analytics and reporting

-- Connection string for read replicas
DATABASE_READ_URL=postgresql://user:pass@replica1:5432/manushya
DATABASE_ANALYTICS_URL=postgresql://user:pass@replica2:5432/manushya
```

### Monitoring & Alerting

#### Performance Metrics
```python
# Custom metrics for monitoring
from prometheus_client import Counter, Histogram, Gauge

# API performance metrics
request_duration = Histogram('api_request_duration_seconds', 'Request duration')
memory_operations = Counter('memory_operations_total', 'Memory operations')
embedding_generation_time = Histogram('embedding_generation_seconds', 'Embedding generation time')
```

#### Alerting Rules
```yaml
# prometheus/alerting.yml
groups:
  - name: manushya_alerts
    rules:
      - alert: HighResponseTime
        expr: api_request_duration_seconds > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time"
      
      - alert: EmbeddingFailure
        expr: embedding_generation_seconds > 30
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Embedding generation failing"
```

### Caching Strategies

#### Redis Caching
```python
# Cache frequently accessed data
import redis.asyncio as redis

async def get_cached_memory(memory_id: str):
    cache_key = f"memory:{memory_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    memory = await get_memory_from_db(memory_id)
    
    # Cache for 1 hour
    await redis.setex(cache_key, 3600, json.dumps(memory))
    return memory
```

#### Vector Search Caching
```python
# Cache vector search results
async def cached_vector_search(query: str, limit: int = 10):
    cache_key = f"search:{hash(query)}:{limit}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Perform vector search
    results = await perform_vector_search(query, limit)
    
    # Cache for 30 minutes
    await redis.setex(cache_key, 1800, json.dumps(results))
    return results
```

---

## 🏭 Deployment & Infrastructure
- **FastAPI** application server
- **PostgreSQL** with pgvector
- **Redis** for caching and sessions
- **Celery** for background tasks
- **Prometheus** for metrics
- **Docker** containerization
- **Health checks** for all services
- **Comprehensive logging**
- **Database migrations** (Alembic)
- **Environment configuration**

---

## 🏆 Best Practices
1. Use JWT or API Key for all requests
2. Always verify webhook signatures
3. Monitor rate limits and analytics endpoints
4. Use role-based policies for least-privilege access
5. Regularly review audit logs and compliance reports
6. Use Docker and environment configs for deployment
7. Keep secrets and credentials secure
8. Test all endpoints with the provided Postman collection
9. **Monitor embedding generation performance**
10. **Track usage metrics for billing**
11. **Use SDKs for consistent client integration**
12. **Optimize HNSW index parameters for your data size**

---

*This documentation is auto-synced with the codebase and Postman collection. For the latest details, always refer to the code and OpenAPI docs.*
