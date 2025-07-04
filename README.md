# Manushya.ai - Secure Identity + Memory Infrastructure

A production-ready, enterprise-grade backend for secure identity and memory infrastructure for autonomous AI agents.

## 🚀 Features

- **🔐 Secure Identity Management**: JWT-based authentication with role-based access control
- **🧠 Memory Storage**: PostgreSQL with text-based memory search (vector search available with pgvector extension)
- **📋 Policy Engine**: JSON Logic-based policy enforcement for fine-grained access control
- **🔒 Field-Level Encryption**: Fernet encryption for sensitive data
- **📊 Audit Logging**: Comprehensive audit trail with immutable logs
- **⚡ Background Processing**: Celery with Redis for async embedding generation
- **📈 Monitoring**: Prometheus metrics and structured logging
- **🐳 Containerized**: Docker Compose for easy deployment
- **🔍 Text-Based Memory Search**: Simple text search with scoring (vector similarity available with pgvector)
- **🔄 GDPR Compliance**: Soft/hard delete with TTL support

## 🏗️ Architecture

```
┌──────────────┐     REST API    ┌──────────────┐
│  Manushya SDK│ ──────────────▶ │  API Gateway │ ──┐
└──────────────┘                 └──────────────┘  │
                                                   ▼
┌──────────────┐   Policy   ┌──────────────┐
│ Policy Engine│◀──────────▶│ Identity DB  │
└──────┬───────┘  Check     └──────────────┘
       │ allow/deny
       ▼
┌──────────────┐
│ Memory Store │  (PostgreSQL + Redis + Celery)
└──────────────┘
```

## 🛠️ Tech Stack

- **Language**: Python 3.10 (downgraded for json_logic compatibility)
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.x with Alembic
- **Database**: PostgreSQL (pgvector extension optional)
- **Cache/Queue**: Redis + Celery
- **Auth**: JWT with python-jose
- **Policy Engine**: JSON Logic (patched for Python 3.10 compatibility)
- **Monitoring**: Prometheus + Structlog
- **Containerization**: Docker + Docker Compose

## 📦 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/manushya-ai/backend.git
cd manushya-ai-backend
```

### 2. Environment Setup

Create a `.env` file based on `env.example`:

```bash
# Copy the example environment file
cp env.example .env

# Generate secure keys (recommended for production)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Update .env with your generated keys
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/healthz

# Access API documentation
open http://localhost:8000/v1/docs
```

### 5. Create Your First Identity

```bash
curl -X POST "http://localhost:8000/v1/identity/" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "test-user",
    "role": "user",
    "name": "Test User",
    "description": "Test identity for endpoint testing"
  }'
```

## 🔌 API Usage

### 1. Create Identity

```bash
curl -X POST "http://localhost:8000/v1/identity/" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "agent-001",
    "role": "agent",
    "name": "Test Agent",
    "description": "Test agent for API testing"
  }'
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "identity": {
    "id": "uuid",
    "external_id": "agent-001",
    "role": "agent",
    "claims": {},
    "is_active": true,
    "created_at": "2025-07-04T10:37:04.546173Z",
    "updated_at": "2025-07-04T10:37:04.546173Z"
  }
}
```

### 2. Create Memory

```bash
curl -X POST "http://localhost:8000/v1/memory/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The user prefers dark mode interfaces",
    "type": "text",
    "meta_data": {"category": "ui", "priority": "high"}
  }'
```

### 3. Search Memories

```bash
curl -X POST "http://localhost:8000/v1/memory/search" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user interface preferences",
    "limit": 5
  }'
```

**Note:** Currently uses text-based search with scoring (0.8 for exact matches, 0.3 for others). Vector similarity search requires pgvector extension setup.

### 4. Create Policy

```bash
curl -X POST "http://localhost:8000/v1/policy/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "agent",
    "rule": {
      "and": [
        {"==": [{"var": "action"}, "read"]},
        {"==": [{"var": "resource"}, "memory"]}
      ]
    },
    "description": "Agents can read memories",
    "priority": 100,
    "is_active": true
  }'
```

### 5. Test Policy

```bash
curl -X POST "http://localhost:8000/v1/policy/test?role=agent&action=read&resource=memory" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "identity": {"role": "agent"}
  }'
```

## 🔧 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black manushya/
ruff check manushya/

# Run linting
ruff check .
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=manushya --cov-report=html

# Run specific test
pytest tests/test_memory.py::test_create_memory
```

## 📊 Monitoring

### Health Checks

```bash
curl http://localhost:8000/healthz
```

### Metrics

```bash
curl http://localhost:8000/metrics
```

### Logs

```bash
# View application logs
docker-compose logs -f api

# View Celery worker logs
docker-compose logs -f celery-worker

# View database logs
docker-compose logs -f postgres
```

### Celery Monitoring

Access Flower dashboard at: http://localhost:5555
- Username: admin
- Password: admin

## 🔒 Security Features

### Authentication

- JWT-based authentication with configurable expiration
- Role-based access control (RBAC)
- Secure token storage and validation

### Authorization

- JSON Logic-based policy engine (patched for Python 3.10 compatibility)
- Fine-grained access control
- Policy caching for performance

### Data Protection

- Field-level encryption using Fernet
- Secure key management
- GDPR-compliant data handling

### Audit & Compliance

- Immutable audit logs
- Request/response logging
- Compliance-ready audit trails

## ⚠️ Current Limitations

### Known Issues

1. **Python Version**: Downgraded to Python 3.10 for json_logic compatibility
2. **Vector Search**: Requires pgvector extension setup for full vector similarity search
3. **Health Check**: Docker health checks may show as unhealthy but API functions correctly
4. **Memory Search**: Currently uses text-based search with simple scoring
5. **Flower Dashboard**: May restart occasionally but doesn't affect core functionality

### Workarounds

- **Policy Creation**: Works with patched json_logic library
- **Memory Search**: Uses text-based search with scoring (0.8 for exact matches, 0.3 for others)
- **Vector Search**: Can be enabled by installing pgvector extension in PostgreSQL
- **Health Checks**: API endpoints work correctly despite Docker health check status

## 🚀 Production Deployment

### Environment Variables

Set production environment variables:

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
# Scale API instances
docker-compose up -d --scale api=3

# Scale Celery workers
docker-compose up -d --scale celery-worker=4
```

### Backup

```bash
# Database backup
docker-compose exec postgres pg_dump -U manushya manushya > backup.sql

# Restore database
docker-compose exec -T postgres psql -U manushya manushya < backup.sql
```

## 🔧 Troubleshooting

### Common Issues

1. **API Container Unhealthy**: Check logs with `docker-compose logs api` - API may still be functional
2. **Database Connection Issues**: Verify PostgreSQL is running and credentials are correct
3. **Redis Connection Issues**: Check Redis container status and password configuration
4. **Memory Search Not Working**: Ensure memories exist and query matches text content
5. **JSON Logic Errors**: Ensure Python 3.10 is used and json_logic patch is applied

### Debug Commands

```bash
# Check all container status
docker-compose ps

# View specific service logs
docker-compose logs -f [service-name]

# Restart specific service
docker-compose restart [service-name]

# Rebuild and restart all services
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Test API endpoints
curl http://localhost:8000/healthz
curl http://localhost:8000/v1/docs
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests: `ruff check .`
6. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.manushya.ai](https://docs.manushya.ai)
- **Issues**: [GitHub Issues](https://github.com/manushya-ai/backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/manushya-ai/backend/discussions)

## 🔮 Roadmap

- [x] Basic API endpoints (Identity, Memory, Policy)
- [x] Docker containerization
- [x] JWT authentication
- [x] Text-based memory search
- [x] JSON Logic policy engine (patched for Python 3.10)
- [x] Comprehensive monitoring and metrics
- [x] Audit logging
- [ ] pgvector extension setup
- [ ] gRPC interface
- [ ] GraphQL API
- [ ] Multi-tenant support
- [ ] Advanced vector search algorithms
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Kubernetes deployment manifests
- [ ] Terraform infrastructure as code 