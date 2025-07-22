# Manushya.ai Investor Pitch Deck
## Secure Memory & Identity Infrastructure for AI Agents

---

## Slide 1: Cover Slide

<div style="text-align: center; padding: 60px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px;">

# 🧠 Manushya.ai

### Give agents a soul. Secure memory for autonomous AI.

**The Soul of Your Agents**

---

**Founder:** Amit K. Das  
**Contact:** amit@manushya.ai  
**Website:** [https://www.manushya.ai/](https://www.manushya.ai/)

*Seed Stage • Q4 2025 Launch*

</div>

---

## Slide 2: Executive Summary

<div style="background: #f8fafc; padding: 40px; border-radius: 12px; border-left: 4px solid #667eea;">

### 🎯 **One-Liner**
**Manushya.ai is building the secure, programmable identity‑and‑memory layer for autonomous AI agents.**

### 💡 **Key Insight**
Agents today are **stateless and forgetful**—as soon as a context window is exceeded, knowledge disappears. We fix that.

### 🚀 **Value Proposition**
- **Persistent Context:** Long-term memory that survives context window limits
- **Enterprise Security:** SOC 2 Type II, GDPR-ready, multi-tenant isolation
- **Programmable Policies:** Fine-grained access control and compliance
- **Developer-First:** TypeScript & Python SDKs with seamless integration

</div>

---

## Slide 3: Problem & Opportunity

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">

### 🔥 **The Problem**

| **Challenge** | **Business Impact** |
|---------------|-------------------|
| 🧠 Agents lose context once prompts overflow | Re‑work, hallucinations, broken workflows |
| 🔐 Fragmented identities and ad‑hoc permissions | Security, compliance, and auditing blind spots |
| 🏢 Existing memory libraries lack enterprise features | Slows adoption in regulated industries |
| 📈 Rapid growth of agent frameworks | Huge greenfield for foundational infrastructure |

### 💰 **The Opportunity**

**TAM (2025 – 2029):**  
**$8.6B** growing at **>34% CAGR**  
for agent orchestration & memory infrastructure

*Source: Market research on AI infrastructure growth*

</div>

---

## Slide 4: Solution Overview

<div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 12px;">

### 🏗️ **Our Architecture**

> **Identity Graph × Memory Graph × Policy Engine × DX‑Centric APIs**

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 30px;">

**🔐 Identity Graph**  
Canonical Agent, User, Role objects with OAuth/SAML, RBAC, and per‑tool capability scopes

**🧠 Memory Graph**  
Vector‑plus‑relational store capturing events, skills, errors, and preferences with TTL, versioning, and lineage

**⚡ Policy Engine**  
Programmable guardrails (allow/deny, masking, redaction) enforced at every memory read/write

**🛠️ DevEx APIs**  
REST, gRPC, and plug‑ins for LangChain/LangGraph and MCP servers

</div>

</div>

---

## Slide 5: Product Vision

<div style="background: #f8fafc; padding: 40px; border-radius: 12px;">

### 📅 **3-Phase Roadmap**

| **Phase** | **Timeline** | **Value Proposition** | **Primary User** |
|-----------|-------------|---------------------|------------------|
| **🎯 MVP** | 6 months | Persist & recall structured memory with single‑tenant security | AI platform teams at mid‑market SaaS |
| **🚀 v1.0** | 12 months | Multi‑tenant SaaS, realtime streaming memories, fine‑grained policy, dashboard | Regulated‑industry enterprises |
| **🌟 v2.0** | 24 months | Marketplace of memory skills, profile portability, federated edge caches | Developer ecosystem & consumer AI apps |

*Progressive feature rollout with clear market positioning*

</div>

---

## Slide 6: MVP Scope

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">

### 📋 **Functional Requirements**

| **FR‑ID** | **Description** | **Priority** |
|-----------|----------------|-------------|
| FR‑1 | Create/Update Identity (POST /identity) with OIDC claim mapping | P0 |
| FR‑2 | Store Memory (POST /memory) with JSON/text payload | P0 |
| FR‑3 | Retrieve Memory (GET /memory?query=) using hybrid search | P0 |
| FR‑4 | Delete/Purge Memory (soft‑delete & GDPR hard‑delete) | P0 |
| FR‑5 | List Memories by identity, time, or type | P1 |
| FR‑6 | Policy Enforcement on read/write | P1 |
| FR‑7 | Webhooks for memory‑saved & policy‑violation events | P1 |
| FR‑8 | Admin UI for audit trail, diff, and rollback | P2 |

### ⚡ **Non-Functional Requirements**

- **⚡ Latency:** < 150 ms p95 for read/write
- **📈 Scale:** 10 K TPS sustained; horizontal shards
- **🔒 Security:** AES‑256 at rest, TLS 1.3, SOC 2 Type II
- **📊 Availability:** 99.9 % SLA
- **💰 Cost:** ≤ $0.10 per 1 M embeddings
- **🏢 Multi-tenancy:** Tenant isolation on all endpoints
- **🚦 Rate Limiting:** Role/tenant-aware with Redis caching
- **📝 Audit Logging:** Full trail with before/after state

</div>

---

## Slide 7: Architecture Diagram

<div style="text-align: center; padding: 40px; background: #1a202c; color: white; border-radius: 12px; font-family: 'Courier New', monospace;">

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

**🔧 Technical Stack:**
- **Database:** PostgreSQL + pgvector (HNSW indexing)
- **Cache:** Redis for session & rate limiting
- **Queue:** Celery for async embedding generation
- **Auth:** JWT + OAuth2/OIDC
- **Monitoring:** Prometheus + Structlog

</div>

---

## Slide 8: API Surface & SDKs

<div style="background: #f8fafc; padding: 40px; border-radius: 12px;">

### 🔌 **Core API Endpoints**

| **Method** | **Path** | **Auth** | **Body / Params** | **Returns** |
|------------|----------|----------|-------------------|-------------|
| POST | /v1/identity | Bearer + JWT | {external_id, role, claims} | identity_id |
| POST | /v1/memory | Bearer + JWT | {identity_id, type, data, ttl} | memory_id |
| GET | /v1/memory | Bearer + JWT | query, filters | [memory] |
| DELETE | /v1/memory/{id} | Bearer + JWT |  | status |
| POST | /v1/api-keys | Bearer + JWT | {name, scopes, expires_in_days} | api_key |
| POST | /v1/invitations | Bearer + JWT | {email, role} | invitation_id |
| GET | /v1/usage/summary | Bearer + JWT | days | usage_analytics |

### 📦 **SDK Support**

<div style="display: flex; justify-content: center; gap: 40px; margin-top: 20px;">

**🐍 Python SDK**  
`pip install manushya-sdk`

**🔷 TypeScript SDK**  
`npm install @manushya/sdk`

</div>

</div>

---

## Slide 9: Data Model

<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">

### 🔐 **Identities Table**
```sql
identities {
  id: UUID (PK)
  external_id: String
  role: String
  claims: JSONB
  tenant_id: UUID (FK)
  created_at: Timestamp
}
```

### 🧠 **Memories Table**
```sql
memories {
  id: UUID (PK)
  identity_id: UUID (FK)
  text: Text
  vector: Vector(1536)  -- pgvector
  type: String
  score: Float
  meta_data: JSONB
  ttl_days: Integer
  created_at: Timestamp
}
```

### ⚡ **Policies Table**
```sql
policies {
  id: UUID (PK)
  role: String
  rule: JSONB  -- OPA-style
  priority: Integer
  tenant_id: UUID (FK)
  created_at: Timestamp
}
```

**🔍 Key Features:**
- **pgvector HNSW indexing** for fast similarity search
- **JSONB** for flexible metadata storage
- **OPA-style policies** for fine-grained access control
- **Multi-tenant isolation** on all tables

</div>

---

## Slide 10: Security & Compliance

<div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 40px; border-radius: 12px;">

### 🛡️ **Zero-Trust Security Architecture**

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; margin-top: 30px;">

**🔐 Authentication & Authorization**
- JWT tokens with configurable expiration
- OAuth2/OIDC integration (Google, extensible)
- API key management with scopes
- Role-based access control (RBAC)

**🔒 Data Protection**
- AES-256 encryption at rest
- TLS 1.3 for data in transit
- Field-level encryption for PII
- Bring-Your-Own-Key (AWS KMS)

**📋 Compliance & Audit**
- SOC 2 Type II ready
- GDPR/HIPAA compliance
- Immutable audit logs
- Comprehensive audit trail

**🏢 Enterprise Features**
- Multi-tenant isolation
- Rate limiting with tenant-aware quotas
- Session management with device tracking
- Webhook security with HMAC signatures

</div>

</div>

---

## Slide 11: Competitive Landscape

<div style="background: #f8fafc; padding: 40px; border-radius: 12px;">

### 🏆 **Competitive Analysis**

| **Competitor / OSS** | **Focus** | **Gap Manushya Covers** |
|----------------------|-----------|-------------------------|
| **Mem0.ai** | Dev‑tooling memory | Limited identity & policy, no enterprise RBAC |
| **LangChain Memory** | Library only | Not hosted, no SLA |
| **DIY Redis/Pinecone** | Custom build | High TCO, security review burden |
| **Replit Ghostwriter Memory** | IDE‑specific | Not externalised as a service |
| **Vector DBs (Pinecone, Weaviate)** | Vector storage only | No identity, policy, or enterprise features |
| **Auth providers (Auth0, Okta)** | Identity only | No memory or AI-specific features |

### 🎯 **Our Unique Position**

**"Only player combining memory, identity, and programmable policy."**

*Comprehensive solution vs. point solutions*

</div>

---

## Slide 12: Go-To-Market Strategy

<div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); border-radius: 12px;">

### 🚀 **4-Step GTM Funnel**

<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 30px;">

**1️⃣ Design Partners**  
Q4 '25: 5-8 mid‑market SaaS teams receive free credits for feedback

**2️⃣ OSS SDK + SaaS**  
Usage‑based pricing with frictionless adoption; pay‑as‑you‑grow

**3️⃣ Enterprise Tier**  
VPC deploy, compliance add‑ons, premium support

**4️⃣ Marketplace Integration**  
Revenue‑share with agent marketplaces and AI‑testing ecosystems

</div>

*Progressive market penetration strategy*

</div>

---

## Slide 13: Revenue Model

<div style="background: #f8fafc; padding: 40px; border-radius: 12px;">

### 💰 **Revenue Projections (Years 1 – 3)**

| **Stream** | **Model** | **Year 1** | **Year 2** | **Year 3** |
|------------|-----------|------------|------------|------------|
| **Usage‑Based API** | $0.50 per 1 K vector ops | $0.6 M | $2.4 M | $5.2 M |
| **Enterprise License** | $60 K/yr base + overage | 2 logos | 8 logos | 20 logos |
| **Marketplace Rev‑Share** | 20 % of skill sales | – | $0.4 M | $1.2 M |

### 📈 **Growth Trajectory**

```
Revenue ($M)
   6 ┤                    ╭───
   5 ┤                ╭───╯
   4 ┤            ╭───╯
   3 ┤        ╭───╯
   2 ┤    ╭───╯
   1 ┤╭───╯
   0 ┼┴─────────────────────────
      Y1   Y2   Y3   Y4   Y5
```

*Projected $6.8M ARR by Year 3*

</div>

---

## Slide 14: Roadmap & KPIs

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">

### 📅 **Quarterly Roadmap**

| **Quarter** | **Milestone** | **KPI** |
|-------------|---------------|---------|
| **Q3 '25** | MVP GA | 50 req/s, SOC‑2 audit start |
| **Q4 '25** | Policy Engine + Admin UI | 5 design partners live |
| **Q1 '26** | Multi‑tenant SaaS, region replicas | 100 M stored memories |
| **Q2 '26** | Marketplace & edge caches | $1 M ARR run rate |

### 🎯 **Key Performance Indicators**

**Technical KPIs:**
- API response time < 150ms p95
- 99.9% uptime SLA
- 10K TPS sustained throughput
- 100M+ stored memories

**Business KPIs:**
- 5 design partners by Q4 '25
- $1M ARR run rate by Q2 '26
- 20 enterprise logos by Year 3
- 50%+ gross margin

</div>

---

## Slide 15: Team

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 12px;">

### 👥 **Founding Team**

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px;">

**👨‍💼 Amit K. Das**  
*Founder & CEO*  
Expertise: Agent orchestration, product strategy

**🔧 CTO (Hiring)**  
*Platform Engineering*  
Expertise: Large‑scale data infra, security

**👨‍💻 3 Founding Engineers**  
*Backend, Security, DevEx*  
Expertise: Python, pgvector, Rust, LangGraph

**🌐 Head of DevRel**  
*Community & OSS*  
Expertise: Open‑source traction

</div>

*Building the team to scale from MVP to enterprise*

</div>

---

## Slide 16: Ask & Use of Funds

<div style="background: #f8fafc; padding: 40px; border-radius: 12px;">

### 💰 **Funding Ask**

**Seed Round: $2.5M**  
*(SAFE, $15M cap) – 18‑month runway*

### 📊 **Use of Proceeds**

<div style="display: flex; justify-content: center; margin: 30px 0;">

**🍕 Pie Chart:**
- **Engineering & Security hires (50%)** - $1.25M
- **Cloud infra & compliance (20%)** - $0.5M  
- **GTM / DevRel / community grants (20%)** - $0.5M
- **Legal & Operations (10%)** - $0.25M

</div>

### 🎯 **Financial Targets**

- **Projected break‑even:** Q3 '27 at $6M ARR
- **Runway:** 18 months to Series A
- **Valuation cap:** $15M (reasonable for seed stage)

</div>

---

## Slide 17: Risks & Mitigations

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">

### ⚠️ **Key Risks**

| **Risk** | **Mitigation** |
|----------|----------------|
| **Vector DB commoditisation** | Moat = identity + policy engine |
| **LLM cost volatility** | Pluggable embeddings (OpenAI, Cohere, local) |
| **Compliance complexity** | Early SOC‑2 & ISO; BYO‑cloud option |
| **Big‑tech entrants** | OSS SDK + community lock‑in; vertical focus |

### 🏰 **Competitive Moats**

**1. Identity + Policy Engine**
- Sticky even if vectors commoditize
- Enterprise-grade RBAC and compliance
- Complex to replicate from scratch

**2. Developer Community**
- Open-source SDKs create lock-in
- Early design partner relationships
- Strong developer experience

**3. Enterprise Security**
- SOC 2 Type II certification
- Multi-tenant isolation
- Compliance-ready architecture

</div>

---

## Slide 18: Why Now

<div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 40px; border-radius: 12px;">

### ⏰ **Perfect Timing**

<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; margin-top: 30px;">

**🤖 Agent Explosion**  
Dozens of VC‑backed companies building agentic workflows create immediate demand for robust memory infrastructure

**📋 Regulatory Pressure**  
EU AI Act and US Executive Order require auditability and data provenance in AI systems

**🔧 Technology Readiness**  
pgvector, open‑source vector databases, and streaming architectures make scalable hybrid memory feasible today

</div>

### 📈 **Market Momentum**

- **Agent frameworks:** LangGraph, OpenAI Assistants, ReAct, MCPs
- **Vector databases:** pgvector, Pinecone, Weaviate maturing
- **Enterprise adoption:** Growing demand for AI infrastructure
- **Regulatory clarity:** Clear compliance requirements emerging

</div>

---

## Slide 19: Call to Action

<div style="text-align: center; padding: 60px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px;">

### 🚀 **Join the Future of AI Agents**

# Give AI agents a **soul**—a secure memory that makes them trustworthy, efficient, and truly human‑aligned.

---

**🎯 Investment Opportunity**
- **$2.5M seed round** (SAFE, $15M cap)
- **18-month runway** to Series A
- **$6M ARR target** by Q3 '27
- **$8.6B TAM** growing at 34%+ CAGR

**📞 Next Steps**
- **Contact:** amit@manushya.ai
- **Website:** [https://www.manushya.ai/](https://www.manushya.ai/)
- **Deck:** QR code for full presentation
- **Calendly:** Schedule a meeting

---

*Join Manushya.ai's seed round and shape the core infrastructure layer powering the next generation of autonomous software.*

</div>

---

## Design Notes

**🎨 Visual Theme:**
- **Primary Colors:** Purple gradient (#667eea to #764ba2) matching manushya.ai
- **Secondary Colors:** Blue gradient (#4facfe to #00f2fe) for technical slides
- **Accent Colors:** Pink gradient (#fa709a to #fee140) for GTM slides
- **Typography:** Clean, modern fonts with proper hierarchy
- **Layout:** Grid-based layouts with consistent spacing
- **Icons:** Emoji icons for visual appeal and quick recognition

**📱 Responsive Design:**
- Works well on both desktop and mobile
- Clean, readable typography
- Proper contrast ratios for accessibility
- Consistent visual hierarchy throughout

**🎯 Investor-Focused:**
- Clear value propositions
- Quantified market opportunity
- Specific financial projections
- Risk mitigation strategies
- Strong competitive positioning 