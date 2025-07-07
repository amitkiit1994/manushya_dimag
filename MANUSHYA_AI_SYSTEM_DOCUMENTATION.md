# Manushya.ai System Documentation

## 📚 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Features Matrix](#features-matrix)
4. [REST API Endpoint Reference](#rest-api-endpoint-reference)
5. [Core Workflows](#core-workflows)
6. [Security & Compliance](#security--compliance)
7. [Advanced Features](#advanced-features)
8. [Deployment & Infrastructure](#deployment--infrastructure)
9. [Best Practices](#best-practices)

---

## 🎯 System Overview

Manushya.ai is a secure, multi-tenant identity and memory infrastructure for autonomous AI agents and enterprise applications. It provides:
- Robust identity management (multi-role, multi-tenant)
- Vector-based memory storage with semantic search
- JSON Logic policy engine for fine-grained access control
- Comprehensive audit logging and compliance
- API key management, invitation flows, session management
- Real SSO (OAuth2/OIDC) integration
- Webhook system for real-time notifications
- Rate limiting, monitoring, and background tasks

---

## 🏗️ Architecture

### Core Modules
- **Identity Management**: Multi-role, multi-tenant, JWT auth, claims, SSO
- **Memory Storage**: Vector search, metadata, TTL, soft/hard delete
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

### Data Flow
- All endpoints are tenant-aware and enforce RBAC via the policy engine.
- All actions are logged for audit/compliance.
- Webhooks and events are triggered for all major changes.

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
2. Memory is stored, embedding generated async
3. Search via POST /v1/memory/search

### Policy Evaluation
1. Request arrives with JWT/API key
2. Policy engine loads and evaluates rules
3. Access granted/denied, audit logged

### API Key Flow
1. Admin creates API key (POST /v1/api-keys/)
2. Use X-API-Key header for programmatic access

### Invitation Flow
1. Admin invites user (POST /v1/invitations/)
2. User receives email, accepts via token
3. Identity is provisioned

### Session & Refresh Token Flow
1. Login returns access + refresh tokens
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

---

*This documentation is auto-synced with the codebase and Postman collection. For the latest details, always refer to the code and OpenAPI docs.*
