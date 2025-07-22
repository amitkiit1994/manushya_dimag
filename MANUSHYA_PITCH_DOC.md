# Product Requirement & MVP Document (Investor Deck)

---

## **1. Executive Summary**

Manushya.ai is building the **secure, programmable identity‑and‑memory layer for autonomous AI agents**. Today's agents are stateless and forgetful—as soon as a context window is exceeded, knowledge disappears. Manushya.ai persists the long‑term context, preferences, and institutional knowledge that agents need to act reliably, safely, and in alignment with human goals.

---

## **2. Problem & Opportunity**

| **Challenge** | **Business Impact** |
| --- | --- |
| Agents lose context once prompts overflow | Re‑work, hallucinations, broken workflows |
| Fragmented identities and ad‑hoc permission models | Security, compliance, and auditing blind spots |
| Existing memory libraries lack enterprise‑grade governance, encryption, and multi‑tenant scale | Slows adoption in regulated industries |
| Rapid growth of agent frameworks (LangGraph, OpenAI Assistants, ReAct, MCPs) | Huge greenfield for foundational infrastructure |

**TAM (2025 – 2029):** Estimated $8.6 B, growing at >34 % CAGR for agent orchestration & memory infrastructure.

---

## **3. Solution Overview**

> Identity Graph × Memory Graph × Policy Engine × DX‑Centric APIs
> 
1. **Identity Graph** – canonical *Agent, User, Role* objects with OAuth/SAML, RBAC, and per‑tool capability scopes.
2. **Memory Graph** – vector‑plus‑relational store capturing events, skills, errors, and preferences with TTL, versioning, and lineage.
3. **Policy Engine** – programmable guardrails (allow/deny, masking, redaction) enforced at every memory read/write.
4. **Developer‑First SDKs & APIs** – REST, gRPC, and plug‑ins for LangChain/LangGraph and MCP servers.
5. **Observability Console** – timelines, diff view, rollback, and "why‑did‑I‑say‑that?" auditing for every agent action.

---

## **4. Product Vision**

| **Phase** | **Value Proposition** | **Primary User** |
| --- | --- | --- |
| **MVP (6 months)** | Persist & recall structured memory with single‑tenant security | AI platform teams at mid‑market SaaS |
| **v1.0 (12 months)** | Multi‑tenant SaaS, realtime streaming memories, fine‑grained policy, dashboard | Regulated‑industry enterprises |
| **v2.0 (24 months)** | Marketplace of memory skills, profile portability, federated edge caches | Developer ecosystem & consumer AI apps |

---

## **5. Minimum Viable Product Scope**

### **5.1 Functional Requirements**

| **FR‑ID** | **Description** | **Priority** |
| --- | --- | --- |
| FR‑1 | Create/Update Identity (POST /identity) with OIDC claim mapping | P0 |
| FR‑2 | Store Memory (POST /memory) with JSON/text payload | P0 |
| FR‑3 | Retrieve Memory (GET /memory?query=) using hybrid search (vector + keyword) | P0 |
| FR‑4 | Delete/Purge Memory (soft‑delete & GDPR hard‑delete) | P0 |
| FR‑5 | List Memories by identity, time, or type | P1 |
| FR‑6 | Policy Enforcement on read/write | P1 |
| FR‑7 | Webhooks for memory‑saved & policy‑violation events | P1 |
| FR‑8 | Admin UI for audit trail, diff, and rollback | P2 |
| FR‑9 | API Key Management (create, revoke, scopes) | P1 |
| FR‑10 | Invitation System (email, accept, validate) | P1 |
| FR‑11 | Session Management (refresh tokens, device info) | P1 |
| FR‑12 | Usage Metering & Analytics | P1 |
| FR‑13 | SSO Integration (OAuth2/OIDC) | P1 |
| FR‑14 | Rate Limiting (role/tenant-aware) | P1 |
| FR‑15 | Embedding Service (OpenAI + local fallback) | P1 |

### **5.2 Non‑Functional Requirements**

- **Latency:** < 150 ms p95 for read/write (≤1 KB embedding)
- **Scale:** 10 K TPS sustained; horizontal shards
- **Security:** AES‑256 at rest, TLS 1.3, SOC 2 Type II, GDPR/HIPAA‑ready
- **Availability:** 99.9 % SLA
- **Cost:** ≤ $0.10 per 1 M embeddings via compression & eviction policies
- **Multi-tenancy:** Tenant isolation on all endpoints and data
- **Rate Limiting:** Role/tenant-aware with Redis caching
- **Audit Logging:** Full trail with before/after state for compliance
- **Background Tasks:** Celery for async embedding generation and cleanup

---

## **6. High‑Level Architecture**

```
          ┌──────────────┐     gRPC/REST   ┌──────────────┐
 Agents → │  Manushya SDK│ ──────────────▶ │  API Gateway │ ──┐
          └──────────────┘                 └──────────────┘  │
                                                             ▼
                           ┌──────────────┐   JSON Logic   ┌──────────────┐
                           │ Policy Engine│◀──────────────▶│ Identity DB  │
                           └──────┬───────┘                └──────────────┘
                                  │ allow/deny
                                  ▼
                           ┌──────────────┐
                           │ Memory Graph │  (PostgreSQL + pgvector + Redis)
                           └──────┬───────┘
                                  │
                                  ▼
                           ┌──────────────┐
                           │ Usage Metering│ (Celery + Analytics)
                           └──────────────┘
```

---

## **7. API Surface (excerpt)**

| **Method** | **Path** | **Auth** | **Body / Params** | **Returns** |
| --- | --- | --- | --- | --- |
| POST | /v1/identity | Bearer + JWT | {external_id, role, claims} | identity_id |
| POST | /v1/memory | Bearer + JWT | {identity_id, type, data, ttl} | memory_id |
| GET | /v1/memory | Bearer + JWT | query, filters | [memory] |
| DELETE | /v1/memory/{id} | Bearer + JWT |  | status |
| POST | /v1/api-keys | Bearer + JWT | {name, scopes, expires_in_days} | api_key |
| POST | /v1/invitations | Bearer + JWT | {email, role} | invitation_id |
| GET | /v1/usage/summary | Bearer + JWT | days | usage_analytics |

SDKs: TypeScript, Python.

---

## **8. Data Model (Core Tables)**

| **Table** | **Key Columns** | **Notes** |
| --- | --- | --- |
| **identities** | id, external_id, role, claims JSONB | human/agent/system |
| **memories** | id, identity_id, vector, text, type, score, created_at, expiry | pgvector index |
| **policies** | id, role, rule JSONB | OPA‑style |
| **api_keys** | id, identity_id, name, scopes, expires_at | programmatic access |
| **invitations** | id, email, token, status, expires_at | user onboarding |
| **sessions** | id, identity_id, refresh_token, device_info | JWT management |
| **audit_logs** | id, event_type, actor_id, before_state, after_state | compliance |
| **webhooks** | id, url, events, secret, status | real-time notifications |
| **usage_events** | id, tenant_id, event, units, metadata | billing analytics |
| **tenants** | id, name, created_at | multi-tenancy |

---

## **9. Security & Compliance**

- Zero‑trust network; mutual TLS between micro‑services
- Field‑level encryption for PII memories
- Bring‑Your‑Own‑Key (AWS KMS) for enterprise customers
- Immutable audit logs (e.g., AWS QLDB)
- Multi-tenant isolation with role-based access control
- Rate limiting with tenant-aware quotas
- Comprehensive audit trail with before/after state tracking

---

## **10. Competitive Landscape**

| **Competitor / OSS** | **Focus** | **Gap Manushya Covers** |
| --- | --- | --- |
| **Mem0.ai** | Dev‑tooling memory | Limited identity & policy, no enterprise RBAC |
| **LangChain Memory** | Library only | Not hosted, no SLA |
| **DIY Redis/Pinecone** | Custom build | High TCO, security review burden |
| **Replit Ghostwriter Memory** | IDE‑specific | Not externalised as a service |
| **Vector DBs (Pinecone, Weaviate)** | Vector storage only | No identity, policy, or enterprise features |
| **Auth providers (Auth0, Okta)** | Identity only | No memory or AI-specific features |

---

## **11. Go‑to‑Market Strategy**

1. **Design Partner Program (Q4 '25)** – 5–8 mid‑market SaaS teams receive free credits for feedback.
2. **Open‑Source SDK + Hosted SaaS (Usage‑Based)** – frictionless adoption; pay‑as‑you‑grow.
3. **Enterprise Tier** – VPC deploy, compliance add‑ons, premium support.
4. **Marketplace Integration** – revenue‑share with agent marketplaces and AI‑testing ecosystems.

---

## **12. Revenue Model (Years 1 – 3)**

| **Stream** | **Model** | **Year 1** | **Year 2** | **Year 3** |
| --- | --- | --- | --- | --- |
| Usage‑Based API | $0.50 per 1 K vector ops | $0.6 M | $2.4 M | $5.2 M |
| Enterprise License | $60 K/yr base + overage | 2 logos | 8 logos | 20 logos |
| Marketplace Rev‑Share | 20 % of skill sales | – | $0.4 M | $1.2 M |

---

## **13. Roadmap & Milestones**

| **Quarter** | **Milestone** | **KPI** |
| --- | --- | --- |
| **Q3 '25** | MVP GA | 50 req/s, SOC‑2 audit start |
| **Q4 '25** | Policy Engine + Admin UI | 5 design partners live |
| **Q1 '26** | Multi‑tenant SaaS, region replicas | 100 M stored memories |
| **Q2 '26** | Marketplace & edge caches | $1 M ARR run rate |

---

## **14. Team & Roles**

| **Name** | **Role** | **Expertise** |
| --- | --- | --- |
| Amit K. Das | Founder & CEO | Agent orchestration, product strategy |
| **CTO (hiring)** | Platform | Large‑scale data infra, security |
| 3 Founding Engineers | Backend, Security, DevEx | Go/Python, pgvector, Rust, LangGraph |
| Head of DevRel | Community & OSS | Open‑source traction |

---

## **15. Funding Ask & Use of Proceeds**

**Seed Round:** **US $2.5 M** (SAFE, $15 M cap) – 18‑month runway

| **Area** | **Allocation** |
| --- | --- |
| Engineering & Security hires | 50 % |
| Cloud infra & compliance | 20 % |
| GTM / DevRel / community grants | 20 % |
| Legal & Operations | 10 % |

Projected break‑even: Q3 '27 at $6 M ARR.

---

## **16. Key Risks & Mitigation**

| **Risk** | **Mitigation** |
| --- | --- |
| Vector DB commoditisation | Moat = identity + policy engine |
| LLM cost volatility | Pluggable embeddings (OpenAI, Cohere, local) |
| Compliance complexity | Early SOC‑2 & ISO; BYO‑cloud option |
| Big‑tech entrants | OSS SDK + community lock‑in; vertical focus |

---

## **17. Why Now**

1. **Agent Explosion** – Dozens of VC‑backed companies building agentic workflows create immediate demand for robust memory infrastructure.
2. **Regulatory Pressure** – EU AI Act and US Executive Order require auditability and data provenance in AI systems.
3. **Technology Readiness** – pgvector, open‑source vector databases, and streaming architectures make scalable hybrid memory feasible today.

---

### **Call to Action**

Help us give AI agents a **soul**—a secure memory that makes them trustworthy, efficient, and truly human‑aligned. Join Manushya.ai's seed round and shape the core infrastructure layer powering the next generation of autonomous software. 