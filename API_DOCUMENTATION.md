# Manushya.ai API Documentation

## 📚 Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [Memory & Embeddings](#memory--embeddings)
5. [Monitoring & Health](#monitoring--health)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Webhooks](#webhooks)
9. [SDK Examples](#sdk-examples)

---

## 🎯 Overview

The Manushya.ai API provides a comprehensive identity and memory management system with:
- **Multi-tenant identity management** with role-based access control
- **Vector-based memory storage** with semantic search capabilities
- **Multiple authentication methods** (JWT, API Keys, Password, MFA, SSO)
- **Real-time embedding generation** with OpenAI integration and local fallbacks
- **Comprehensive monitoring** and health checks
- **Webhook system** for real-time notifications
- **Rate limiting** and security features

**Base URL**: `https://api.manushya.ai` (production) or `http://localhost:8000` (development)

---

## 🔐 Authentication

### Authentication Methods

#### 1. Identity Creation with JWT Token
```bash
# Create identity and get JWT token
curl -X POST "https://api.manushya.ai/v1/identity/" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "user@example.com",
    "role": "user",
    "claims": {
      "name": "John Doe",
      "department": "engineering"
    }
  }'

# Use JWT token in requests
curl -X GET "https://api.manushya.ai/v1/identity/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 2. API Key Authentication
```bash
# Use API key in requests
curl -X GET "https://api.manushya.ai/v1/identity/me" \
  -H "X-API-Key: YOUR_API_KEY"
```

#### 3. Session Management
```bash
# Refresh JWT token
curl -X POST "https://api.manushya.ai/v1/sessions/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'

# Get session info
curl -X GET "https://api.manushya.ai/v1/sessions/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 4. Multi-Factor Authentication (MFA)
```bash
# Setup MFA (returns QR code and backup codes)
curl -X POST "https://api.manushya.ai/v1/auth/mfa/setup" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Verify MFA token
curl -X POST "https://api.manushya.ai/v1/auth/mfa/verify" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "123456"
  }'

# Disable MFA
curl -X DELETE "https://api.manushya.ai/v1/auth/mfa/disable" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 5. SSO Authentication
```bash
# Initiate SSO login
curl -X GET "https://api.manushya.ai/v1/sso/login/google"

# SSO callback (handled by browser)
GET "https://api.manushya.ai/v1/sso/callback/google?code=AUTHORIZATION_CODE"
```

---

## 🔧 Core Endpoints

### Identity Management

#### Create Identity
```bash
curl -X POST "https://api.manushya.ai/v1/identity/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "user_123",
    "role": "user",
    "metadata": {
      "department": "engineering",
      "location": "san-francisco"
    }
  }'
```

#### Get Identity
```bash
curl -X GET "https://api.manushya.ai/v1/identity/USER_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Update Identity
```bash
curl -X PUT "https://api.manushya.ai/v1/identity/USER_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin",
    "metadata": {
      "department": "management"
    }
  }'
```

### API Key Management

#### Create API Key
```bash
curl -X POST "https://api.manushya.ai/v1/api-keys/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "scopes": ["read", "write"],
    "expires_in_days": 365
  }'
```

#### List API Keys
```bash
curl -X GET "https://api.manushya.ai/v1/api-keys/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Revoke API Key
```bash
curl -X DELETE "https://api.manushya.ai/v1/api-keys/KEY_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🧠 Memory & Embeddings

### Create Memory with Embedding
```bash
curl -X POST "https://api.manushya.ai/v1/memory/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Client meeting notes: Discussed retirement planning and investment strategies",
    "type": "meeting_note",
    "metadata": {
      "client_id": "CS001",
      "advisor": "advisor_001",
      "meeting_date": "2024-01-15"
    },
    "ttl_days": 365
  }'
```

**Embedding Service Behavior:**
- **OpenAI Integration**: Uses OpenAI API if `OPENAI_API_KEY` is configured
- **Local Fallback**: Falls back to sentence-transformers if OpenAI fails
- **Hash Fallback**: Uses hash-based embeddings if sentence-transformers unavailable
- **Graceful Degradation**: Continues without embedding if all methods fail

### Search Memories with Vector Similarity
```bash
curl -X POST "https://api.manushya.ai/v1/memory/search" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "retirement planning",
    "similarity_threshold": 0.7,
    "limit": 10,
    "memory_types": ["meeting_note", "investment_recommendation"]
  }'
```

### Get Memory
```bash
curl -X GET "https://api.manushya.ai/v1/memory/MEMORY_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Memory
```bash
curl -X PUT "https://api.manushya.ai/v1/memory/MEMORY_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Updated meeting notes with additional context",
    "metadata": {
      "client_id": "CS001",
      "advisor": "advisor_001",
      "updated": true
    }
  }'
```

### Delete Memory
```bash
# Soft delete (default)
curl -X DELETE "https://api.manushya.ai/v1/memory/MEMORY_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Hard delete
curl -X DELETE "https://api.manushya.ai/v1/memory/MEMORY_ID?hard=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📊 Monitoring & Health

### Health Check
```bash
curl -X GET "https://api.manushya.ai/healthz"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "embedding_service": "healthy"
  }
}
```

### Prometheus Metrics
```bash
curl -X GET "https://api.manushya.ai/metrics"
```

### Usage Analytics
```bash
# Get usage summary
curl -X GET "https://api.manushya.ai/v1/usage/summary?days=30" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get daily usage
curl -X GET "https://api.manushya.ai/v1/usage/daily?date=2024-01-15" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Rate Limit Information
```bash
curl -X GET "https://api.manushya.ai/v1/monitoring/rate-limits" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## ⚠️ Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "text",
      "issue": "Text cannot be empty"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes
- `AUTHENTICATION_ERROR`: Invalid or missing authentication
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `VALIDATION_ERROR`: Invalid input data
- `NOT_FOUND_ERROR`: Resource not found
- `RATE_LIMIT_ERROR`: Too many requests
- `EMBEDDING_ERROR`: Embedding service failure
- `DATABASE_ERROR`: Database connection issues

### Circuit Breaker Status
```bash
curl -X GET "https://api.manushya.ai/v1/monitoring/circuit-breakers" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🚦 Rate Limiting

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642233600
```

### Rate Limit by Role
- **Admin**: 10,000 requests/hour
- **User**: 1,000 requests/hour
- **API Key**: 5,000 requests/hour

### Rate Limit by Endpoint
- **Authentication endpoints**: 10 requests/minute
- **Memory search**: 100 requests/minute
- **Embedding generation**: 50 requests/minute

---

## 🔔 Webhooks

### Register Webhook
```bash
curl -X POST "https://api.manushya.ai/v1/webhooks/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Identity Events Webhook",
    "url": "https://webhook.site/your-url",
    "events": ["identity.created", "identity.updated", "memory.created"],
    "secret": "webhook_secret_123"
  }'
```

### Webhook Events
- `identity.created`: New identity created
- `identity.updated`: Identity updated
- `identity.deleted`: Identity deleted
- `memory.created`: New memory created
- `memory.updated`: Memory updated
- `memory.deleted`: Memory deleted
- `api_key.created`: New API key created
- `api_key.revoked`: API key revoked

### Webhook Delivery
```json
{
  "event": "memory.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "memory_id": "mem_123",
    "identity_id": "id_456",
    "text": "Client meeting notes",
    "type": "meeting_note"
  },
  "signature": "sha256=abc123..."
}
```

---

## 📦 SDK Examples

### Python SDK
```python
from manushya_sdk import ManushyaClient

# Initialize client
client = ManushyaClient(
    api_key="your-api-key",
    base_url="https://api.manushya.ai"
)

# Create memory with automatic embedding
memory = client.memory.create(
    text="Client meeting notes: Discussed retirement planning",
    type="meeting_note",
    metadata={"client_id": "CS001"}
)

# Search with vector similarity
results = client.memory.search(
    query="retirement planning",
    similarity_threshold=0.7,
    limit=10
)

# Get usage analytics
usage = client.usage.get_summary(days=30)
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

---

## 🔧 Development

### Local Development
```bash
# Start development server
uvicorn manushya.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker
celery -A manushya.tasks.celery_app worker --loglevel=info

# Run tests
pytest

# Check API documentation
open http://localhost:8000/v1/docs
```

### Environment Variables
```bash
# Required
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://user:pass@localhost:5432/manushya
REDIS_URL=redis://localhost:6379/0

# Optional
OPENAI_API_KEY=your-openai-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

---

*For interactive API documentation, visit `/v1/docs` when running the server.* 