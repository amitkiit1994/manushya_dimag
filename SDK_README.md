# Manushya.ai SDK Documentation

## 📚 Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Authentication](#authentication)
4. [Python SDK](#python-sdk)
5. [TypeScript SDK](#typescript-sdk)
6. [Advanced Features](#advanced-features)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## 🎯 Overview

The Manushya.ai SDKs provide high-level client libraries for Python and TypeScript, making it easy to integrate with the Manushya.ai API. Both SDKs support:

- **Authentication**: JWT tokens and API keys
- **Memory Management**: CRUD operations with vector search
- **Identity Management**: Multi-role identity system
- **Policy Testing**: JSON Logic policy evaluation
- **Usage Analytics**: Billing and usage tracking
- **Webhook Management**: Real-time notifications
- **Rate Limiting**: Built-in rate limit handling

---

## 📦 Installation

### Python SDK
```bash
pip install -e sdk/python
```

### TypeScript SDK
```bash
npm install @manushya/sdk
# or
yarn add @manushya/sdk
```

---

## 🔐 Authentication

### API Key Authentication
```python
# Python
from manushya_sdk import ManushyaClient

client = ManushyaClient(
    api_key="your-api-key",
    base_url="https://api.manushya.ai"
)
```

```typescript
// TypeScript
import { ManushyaClient } from '@manushya/sdk';

const client = new ManushyaClient({
    apiKey: 'your-api-key',
    baseUrl: 'https://api.manushya.ai'
});
```

### JWT Token Authentication
```python
# Python
client = ManushyaClient(
    jwt_token="your-jwt-token",
    base_url="https://api.manushya.ai"
)
```

```typescript
// TypeScript
const client = new ManushyaClient({
    jwtToken: 'your-jwt-token',
    baseUrl: 'https://api.manushya.ai'
});
```

---

## 🐍 Python SDK

### Installation
```bash
pip install -e sdk/python
```

### Authentication
The generated SDK uses Bearer (JWT) authentication. You must pass the access token in the `Authorization` header:

```python
from sdk.python.client import Client
client = Client(base_url="http://localhost:8000", headers={"Authorization": "Bearer <your-access-token>"})
```

### Basic Usage Example

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
```

### Endpoint Usage
The generated SDK exposes each endpoint as a function in the `api/` submodules. You must import the correct function and model for each operation. For example:

```python
from sdk.python.api.memory.create_memory_v1_memory_post import sync_detailed as create_memory
from sdk.python.models.memory_create import MemoryCreate
from sdk.python.models.memory_create_metadata import MemoryCreateMetadata

metadata = MemoryCreateMetadata()
metadata["source"] = "sdk-test"
memory_data = MemoryCreate(text="Test memory", type_="note", metadata=metadata)
response = create_memory(client=client, body=memory_data)
print(response.status_code, response.parsed)
```

### Regenerating the SDK
To regenerate the SDK from the latest OpenAPI spec:

1. Ensure your FastAPI app is running and serving the OpenAPI spec at `http://localhost:8000/v1/openapi.json`.
2. Run the SDK generation script from the project root:

```bash
python scripts/generate_sdk.py
```

This will:
- Fetch the latest OpenAPI spec
- Patch it for SDK generation
- Generate the Python SDK in `sdk/python/`

If you want to distribute the SDK to others:
- Zip the `sdk/python/` directory or publish it to a package index.
- Provide this README for installation and usage instructions.

### Advanced Usage
- See the generated `client.py` and `api/` submodules for all available endpoints.
- Use the models in `models/` for request/response payloads.
- For business logic flows, see `test_sdk_business_logic.py` for end-to-end examples.

### Note
The generated SDK is low-level and does not provide a high-level `ManushyaClient` abstraction. You must use the endpoint modules and models directly as shown above.

### Memory Management

#### Create Memory
```python
# Create a memory with automatic embedding
memory = client.memory.create(
    text="Client meeting notes: Discussed retirement planning with John Smith",
    type="meeting_note",
    metadata={
        "client_id": "CS001",
        "advisor": "advisor_001",
        "tags": ["retirement", "planning"]
    },
    ttl_days=365
)

print(f"Created memory: {memory['id']}")
```

#### Search Memories
```python
# Search with vector similarity
results = client.memory.search(
    query="retirement planning",
    similarity_threshold=0.7,
    limit=10,
    type="meeting_note"
)

for memory in results:
    print(f"Memory: {memory['text'][:100]}... (Score: {memory['score']})")
```

#### List Memories
```python
# List all memories
memories = client.memory.list(
    skip=0,
    limit=50,
    memory_type="meeting_note"
)

for memory in memories:
    print(f"Memory ID: {memory['id']}, Type: {memory['type']}")
```

#### Update Memory
```python
# Update memory
updated_memory = client.memory.update(
    memory_id="memory-uuid",
    text="Updated meeting notes with additional client preferences",
    metadata={
        "updated_by": "advisor_001",
        "update_reason": "client_preferences_added"
    }
)
```

#### Delete Memory
```python
# Soft delete (default)
client.memory.delete(memory_id="memory-uuid")

# Hard delete
client.memory.delete(memory_id="memory-uuid", hard_delete=True)
```

### Identity Management

#### Create Identity
```python
# Create a new identity
identity = client.identity.create(
    external_id="new_user_001",
    role="advisor",
    claims={
        "department": "investment",
        "region": "north"
    }
)

print(f"Created identity: {identity['id']}")
```

#### Get Current Identity
```python
# Get current user information
current_user = client.identity.get_current()
print(f"Current user: {current_user['external_id']}, Role: {current_user['role']}")
```

#### Update Identity
```python
# Update current identity
updated_identity = client.identity.update_current(
    role="senior_advisor",
    claims={
        "department": "investment",
        "seniority": "senior"
    }
)
```

### Policy Testing

#### Test Policy Evaluation
```python
# Test if an action is allowed
policy_result = client.policy.test(
    role="advisor",
    action="read",
    resource="memory",
    context={
        "memory_type": "meeting_note",
        "client_id": "CS001"
    }
)

print(f"Policy result: {policy_result['allowed']}")
```

#### Create Policy
```python
# Create a new policy
policy = client.policy.create(
    role="advisor",
    rule={
        "and": [
            {"in": [{"var": "action"}, ["read", "write"]]},
            {"==": [{"var": "resource"}, "memory"]},
            {"!=": [{"var": "action"}, "delete"]}
        ]
    },
    description="Advisors can read and write memories but not delete them",
    priority=80,
    is_active=True
)
```

### Usage Analytics

#### Get Usage Summary
```python
# Get usage summary for the last 30 days
usage_summary = client.usage.get_summary(days=30)

print(f"Total memory operations: {usage_summary['totals']['memory.write']}")
print(f"Total search operations: {usage_summary['totals']['memory.search']}")
```

#### Get Daily Usage
```python
# Get daily usage breakdown
daily_usage = client.usage.get_daily(
    start_date="2024-01-01",
    end_date="2024-01-31",
    event_type="memory.write"
)

for record in daily_usage:
    print(f"Date: {record['date']}, Units: {record['units']}")
```

### API Key Management

#### Create API Key
```python
# Create a new API key
api_key = client.api_keys.create(
    name="Production API Key",
    scopes=["read", "write"],
    expires_in_days=365
)

print(f"API Key: {api_key['key']}")
```

#### List API Keys
```python
# List all API keys
api_keys = client.api_keys.list()

for key in api_keys:
    print(f"Key: {key['name']}, Scopes: {key['scopes']}")
```

### Webhook Management

#### Create Webhook
```python
# Create a webhook for memory events
webhook = client.webhooks.create(
    name="Memory Events Webhook",
    url="https://your-webhook-endpoint.com/webhook",
    events=["memory.created", "memory.updated", "memory.deleted"]
)
```

#### List Webhooks
```python
# List all webhooks
webhooks = client.webhooks.list()

for webhook in webhooks:
    print(f"Webhook: {webhook['name']}, Events: {webhook['events']}")
```

---

## 🔷 TypeScript SDK

### Basic Setup
```typescript
import { ManushyaClient } from '@manushya/sdk';

// Initialize client
const client = new ManushyaClient({
    apiKey: 'your-api-key',
    baseUrl: 'https://api.manushya.ai'
});

// Check health
const health = await client.healthCheck();
console.log(`System status: ${health.status}`);
```

### Memory Management

#### Create Memory
```typescript
// Create a memory with automatic embedding
const memory = await client.memory.create({
    text: 'Investment recommendation for high-net-worth client',
    type: 'investment_recommendation',
    metadata: {
        clientId: 'CS002',
        riskLevel: 'high',
        portfolioSize: '$2M+',
        advisor: 'advisor_001'
    },
    ttlDays: 365
});

console.log(`Created memory: ${memory.id}`);
```

#### Search Memories
```typescript
// Search with vector similarity
const searchResults = await client.memory.search({
    query: 'high net worth investment',
    similarityThreshold: 0.8,
    limit: 5,
    type: 'investment_recommendation'
});

searchResults.forEach(memory => {
    console.log(`Memory: ${memory.text.substring(0, 100)}... (Score: ${memory.score})`);
});
```

#### List Memories
```typescript
// List all memories
const memories = await client.memory.list({
    skip: 0,
    limit: 50,
    memoryType: 'investment_recommendation'
});

memories.forEach(memory => {
    console.log(`Memory ID: ${memory.id}, Type: ${memory.type}`);
});
```

#### Update Memory
```typescript
// Update memory
const updatedMemory = await client.memory.update('memory-uuid', {
    text: 'Updated investment recommendation with new risk assessment',
    metadata: {
        updatedBy: 'advisor_001',
        updateReason: 'risk_assessment_updated'
    }
});
```

#### Delete Memory
```typescript
// Soft delete (default)
await client.memory.delete('memory-uuid');

// Hard delete
await client.memory.delete('memory-uuid', { hardDelete: true });
```

### Identity Management

#### Create Identity
```typescript
// Create a new identity
const identity = await client.identity.create({
    externalId: 'new_user_001',
    role: 'advisor',
    claims: {
        department: 'investment',
        region: 'north'
    }
});

console.log(`Created identity: ${identity.id}`);
```

#### Get Current Identity
```typescript
// Get current user information
const currentUser = await client.identity.getCurrent();
console.log(`Current user: ${currentUser.externalId}, Role: ${currentUser.role}`);
```

#### Update Identity
```typescript
// Update current identity
const updatedIdentity = await client.identity.updateCurrent({
    role: 'senior_advisor',
    claims: {
        department: 'investment',
        seniority: 'senior'
    }
});
```

### Policy Testing

#### Test Policy Evaluation
```typescript
// Test if an action is allowed
const policyResult = await client.policy.test({
    role: 'advisor',
    action: 'read',
    resource: 'memory',
    context: {
        memoryType: 'investment_recommendation',
        clientId: 'CS002'
    }
});

console.log(`Policy result: ${policyResult.allowed}`);
```

#### Create Policy
```typescript
// Create a new policy
const policy = await client.policy.create({
    role: 'advisor',
    rule: {
        and: [
            { in: [{ var: 'action' }, ['read', 'write']] },
            { '==': [{ var: 'resource' }, 'memory'] },
            { '!=': [{ var: 'action' }, 'delete'] }
        ]
    },
    description: 'Advisors can read and write memories but not delete them',
    priority: 80,
    isActive: true
});
```

### Usage Analytics

#### Get Usage Summary
```typescript
// Get usage summary for the last 30 days
const usageSummary = await client.usage.getSummary({ days: 30 });

console.log(`Total memory operations: ${usageSummary.totals['memory.write']}`);
console.log(`Total search operations: ${usageSummary.totals['memory.search']}`);
```

#### Get Daily Usage
```typescript
// Get daily usage breakdown
const dailyUsage = await client.usage.getDaily({
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    eventType: 'memory.write'
});

dailyUsage.forEach(record => {
    console.log(`Date: ${record.date}, Units: ${record.units}`);
});
```

### API Key Management

#### Create API Key
```typescript
// Create a new API key
const apiKey = await client.apiKeys.create({
    name: 'Production API Key',
    scopes: ['read', 'write'],
    expiresInDays: 365
});

console.log(`API Key: ${apiKey.key}`);
```

#### List API Keys
```typescript
// List all API keys
const apiKeys = await client.apiKeys.list();

apiKeys.forEach(key => {
    console.log(`Key: ${key.name}, Scopes: ${key.scopes.join(', ')}`);
});
```

### Webhook Management

#### Create Webhook
```typescript
// Create a webhook for memory events
const webhook = await client.webhooks.create({
    name: 'Memory Events Webhook',
    url: 'https://your-webhook-endpoint.com/webhook',
    events: ['memory.created', 'memory.updated', 'memory.deleted']
});
```

#### List Webhooks
```typescript
// List all webhooks
const webhooks = await client.webhooks.list();

webhooks.forEach(webhook => {
    console.log(`Webhook: ${webhook.name}, Events: ${webhook.events.join(', ')}`);
});
```

---

## 🚀 Advanced Features

### Batch Operations

#### Python
```python
# Batch create memories
memories_data = [
    {
        "text": "First memory",
        "type": "note",
        "metadata": {"batch": "batch_1"}
    },
    {
        "text": "Second memory", 
        "type": "note",
        "metadata": {"batch": "batch_1"}
    }
]

# Note: SDK handles batching automatically
for memory_data in memories_data:
    memory = client.memory.create(**memory_data)
    print(f"Created: {memory['id']}")
```

#### TypeScript
```typescript
// Batch create memories
const memoriesData = [
    {
        text: 'First memory',
        type: 'note',
        metadata: { batch: 'batch_1' }
    },
    {
        text: 'Second memory',
        type: 'note', 
        metadata: { batch: 'batch_1' }
    }
];

// Note: SDK handles batching automatically
for (const memoryData of memoriesData) {
    const memory = await client.memory.create(memoryData);
    console.log(`Created: ${memory.id}`);
}
```

### Error Handling

#### Python
```python
from manushya_sdk import ManushyaError, RateLimitError

try:
    memory = client.memory.create(text="Test memory")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Wait and retry
    import time
    time.sleep(e.retry_after)
except ManushyaError as e:
    print(f"API error: {e.message}")
    print(f"Error code: {e.error_code}")
```

#### TypeScript
```typescript
import { ManushyaError, RateLimitError } from '@manushya/sdk';

try {
    const memory = await client.memory.create({ text: 'Test memory' });
} catch (error) {
    if (error instanceof RateLimitError) {
        console.log(`Rate limit exceeded: ${error.message}`);
        // Wait and retry
        await new Promise(resolve => setTimeout(resolve, error.retryAfter * 1000));
    } else if (error instanceof ManushyaError) {
        console.log(`API error: ${error.message}`);
        console.log(`Error code: ${error.errorCode}`);
    }
}
```

### Retry Logic

#### Python
```python
from manushya_sdk import ManushyaClient
import time

class RetryClient(ManushyaClient):
    def __init__(self, max_retries=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
    
    def memory_create_with_retry(self, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return self.memory.create(**kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

# Usage
client = RetryClient(max_retries=3, api_key="your-key")
memory = client.memory_create_with_retry(text="Test memory")
```

#### TypeScript
```typescript
import { ManushyaClient } from '@manushya/sdk';

class RetryClient extends ManushyaClient {
    private maxRetries: number;

    constructor(maxRetries = 3, options: any) {
        super(options);
        this.maxRetries = maxRetries;
    }

    async memoryCreateWithRetry(data: any) {
        for (let attempt = 0; attempt < this.maxRetries; attempt++) {
            try {
                return await this.memory.create(data);
            } catch (error) {
                if (attempt === this.maxRetries - 1) {
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
            }
        }
    }
}

// Usage
const client = new RetryClient(3, { apiKey: 'your-key' });
const memory = await client.memoryCreateWithRetry({ text: 'Test memory' });
```

---

## 🛠️ Best Practices

### 1. Authentication
```python
# Use environment variables for credentials
import os
from manushya_sdk import ManushyaClient

client = ManushyaClient(
    api_key=os.getenv('MANUSHYA_API_KEY'),
    base_url=os.getenv('MANUSHYA_BASE_URL', 'https://api.manushya.ai')
)
```

### 2. Error Handling
```python
# Always handle errors gracefully
try:
    result = client.memory.create(text="Important memory")
except Exception as e:
    logger.error(f"Failed to create memory: {e}")
    # Implement fallback logic
```

### 3. Rate Limiting
```python
# SDK handles rate limiting automatically
# But you can check limits
rate_limit_info = client.get_rate_limit_info()
print(f"Remaining requests: {rate_limit_info['remaining']}")
```

### 4. Caching
```python
# Cache frequently accessed data
import redis

redis_client = redis.Redis()

def get_cached_memory(memory_id):
    cached = redis_client.get(f"memory:{memory_id}")
    if cached:
        return json.loads(cached)
    
    memory = client.memory.get(memory_id)
    redis_client.setex(f"memory:{memory_id}", 3600, json.dumps(memory))
    return memory
```

### 5. Batch Operations
```python
# Use batch operations for efficiency
def create_memories_batch(memories_data):
    results = []
    for data in memories_data:
        try:
            memory = client.memory.create(**data)
            results.append(memory)
        except Exception as e:
            logger.error(f"Failed to create memory: {e}")
            results.append(None)
    return results
```

---

## 📊 Monitoring

### SDK Metrics
```python
# Enable SDK metrics
client.enable_metrics()

# Get SDK performance metrics
metrics = client.get_metrics()
print(f"Total requests: {metrics['total_requests']}")
print(f"Average response time: {metrics['avg_response_time']}ms")
```

### Custom Logging
```python
import logging

# Configure SDK logging
logging.getLogger('manushya_sdk').setLevel(logging.INFO)

# Custom logger for your application
logger = logging.getLogger(__name__)
logger.info("Using Manushya.ai SDK")
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Errors
```python
# Check your API key
try:
    client.identity.get_current()
except Exception as e:
    if "401" in str(e):
        print("Invalid API key or JWT token")
```

#### 2. Rate Limiting
```python
# Handle rate limiting
try:
    result = client.memory.create(text="Test")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
```

#### 3. Network Issues
```python
# Handle network timeouts
import time

def create_memory_with_timeout(text, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            return client.memory.create(text=text)
        except Exception as e:
            if "timeout" in str(e).lower():
                time.sleep(1)
                continue
            raise
    raise TimeoutError("Operation timed out")
```

---

## 📚 Additional Resources

- [API Documentation](https://docs.manushya.ai)
- [Postman Collection](Manushya_AI_API_Collection.json)
- [System Documentation](MANUSHYA_AI_SYSTEM_DOCUMENTATION.md)
- [GitHub Repository](https://github.com/manushya-ai/backend)

---

*For support and questions, please refer to the main documentation or create an issue on GitHub.* 