# Manushya.ai - Secure Identity + Memory Infrastructure

## 📚 Table of Contents
1. [Features](#features)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Quick Start](#quick-start)
5. [API Usage](#api-usage)
6. [Features Matrix](#features-matrix)
7. [Security & Compliance](#security--compliance)
8. [Monitoring & Observability](#monitoring--observability)
9. [Development](#development)
10. [Production Deployment](#production-deployment)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)
13. [License & Support](#license--support)
14. [Roadmap](#roadmap)

---

## 🚀 Features

- **🔐 Multi-Tenant Identity Management**: Role-based, tenant-aware, JWT & SSO authentication
- **🧠 Memory Storage**: Vector-based semantic search, metadata, TTL, soft/hard delete
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

---

## 🏗️ Architecture

### Core Modules
- **Identity**: Multi-role, multi-tenant, JWT, SSO, API keys, invitations
- **Memory**: Vector search, metadata, TTL, soft/hard delete
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

---

## 🛠️ Tech Stack
- **Language**: Python 3.10
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.x + Alembic
- **Database**: PostgreSQL (pgvector for vector search)
- **Cache/Queue**: Redis + Celery
- **Auth**: JWT, SSO (OAuth2/OIDC), API Keys
- **Policy Engine**: JSON Logic
- **Monitoring**: Prometheus + Structlog
- **Containerization**: Docker + Docker Compose

---

## 📦 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.10
- Git

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

### Major Endpoint Groups
- **Identity**: `/v1/identity/` (CRUD, bulk, self, JWT, SSO)
- **API Keys**: `/v1/api-keys/` (CRUD, test)
- **Invitations**: `/v1/invitations/` (CRUD, validate, accept, resend)
- **Sessions**: `/v1/sessions/` (CRUD, refresh, cleanup, test)
- **Events**: `/v1/events/` (CRUD, by identity, types, stats, retry, cleanup, test)
- **Policy**: `/v1/policy/` (CRUD, bulk, test)
- **Memory**: `/v1/memory/` (CRUD, search, bulk)
- **Webhooks**: `/v1/webhooks/` (CRUD, deliveries, retry, stats, events)
- **SSO**: `/v1/sso/` (login, callback)
- **Admin/Monitoring**: `/v1/admin/rate-limits`, `/v1/monitoring/`

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
| Audit Logging          | Full trail, before/after, GDPR, retention        | ✅     |
| Monitoring             | Prometheus, health, analytics, admin endpoints   | ✅     |
| Background Tasks       | Celery, async jobs, retries, cleanup             | ✅     |

---

## 🔒 Security & Compliance
- **JWT, SSO, API Key Auth**: All endpoints require authentication
- **Role & Policy Engine**: JSON Logic, RBAC, resource/action-level
- **Audit Logging**: All actions logged, before/after state, GDPR
- **Encryption**: Field-level for sensitive data
- **Rate Limiting**: Global, role/tenant-aware, Redis-backed
- **Webhook Security**: HMAC signatures, tenant isolation
- **Compliance**: Retention, tamper-evident logs, GDPR

---

## 📈 Monitoring & Observability
- **Health Checks**: `/health`
- **Prometheus Metrics**: `/metrics`
- **Admin/Monitoring Endpoints**: `/v1/admin/rate-limits`, `/v1/monitoring/`
- **Structured Logging**: Request IDs, error tracking
- **Celery Monitoring**: Flower dashboard at `http://localhost:5555`

---

## 🔧 Development

### Local Development Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
black manushya/
ruff check manushya/
```

### Database Migrations
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1
```

### Running Tests
```bash
pytest
pytest --cov=manushya --cov-report=html
```

---

## 🚀 Production Deployment

### Environment Variables
Set production environment variables in `.env`:
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-production-jwt-key
ENCRYPTION_KEY=your-production-encryption-key
```

### Scaling
```bash
docker-compose up -d --scale api=3
docker-compose up -d --scale celery-worker=4
```

### Backup
```bash
docker-compose exec postgres pg_dump -U manushya manushya > backup.sql
docker-compose exec -T postgres psql -U manushya manushya < backup.sql
```

---

## 🛠️ Troubleshooting
- **API Container Unhealthy**: Check logs with `docker-compose logs api`
- **Database/Redis Issues**: Check container status and credentials
- **Memory Search Not Working**: Ensure memories exist and query matches text content
- **JSON Logic Errors**: Ensure Python 3.10 is used and json_logic patch is applied
- **Health Checks**: API endpoints work even if Docker health check is unhealthy

---

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests: `ruff check .`
6. Submit a pull request

---

## 📄 License & Support
- **License**: MIT License - see [LICENSE](LICENSE)
- **Docs**: [docs.manushya.ai](https://docs.manushya.ai)
- **Issues**: [GitHub Issues](https://github.com/manushya-ai/backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/manushya-ai/backend/discussions)

---

## 🔮 Roadmap
- [x] Multi-tenant support
- [x] API key management
- [x] Invitation system
- [x] Session management & refresh tokens
- [x] Identity events & audit logging
- [x] Rate limiting (role/tenant-aware)
- [x] Real SSO provider integration (OAuth2/OIDC)
- [x] Webhook system for real-time notifications
- [x] Advanced policy engine features
- [x] Background tasks & cleanup jobs
- [x] Monitoring & analytics endpoints
- [x] Production-ready error handling
- [x] Docker containerization
- [x] Redis caching
- [x] Celery background tasks
- [x] Health checks & Prometheus metrics
- [x] Complete Postman collection
- [ ] gRPC interface
- [ ] GraphQL API
- [ ] Advanced analytics dashboard
- [ ] Kubernetes deployment manifests
- [ ] Terraform infrastructure as code 