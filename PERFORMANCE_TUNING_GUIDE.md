# Manushya.ai Performance Tuning Guide

## 📚 Table of Contents
1. [Overview](#overview)
2. [Database Optimization](#database-optimization)
3. [Redis Configuration](#redis-configuration)
4. [Application Performance](#application-performance)
5. [Scaling Strategies](#scaling-strategies)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Caching Strategies](#caching-strategies)
8. [Production Checklist](#production-checklist)

---

## 🎯 Overview

This guide provides comprehensive performance tuning recommendations for Manushya.ai at scale, from development to production environments handling 100M+ memories.

### Performance Targets
- **API Response Time**: < 200ms for 95% of requests
- **Vector Search**: < 100ms for similarity queries
- **Memory Throughput**: 10,000+ memories/second
- **Concurrent Users**: 1,000+ simultaneous users
- **Database**: Handle 100M+ memories efficiently

---

## 🗄️ Database Optimization

### PostgreSQL Configuration

#### Production Settings
```sql
-- Optimize for vector operations and high throughput
ALTER SYSTEM SET shared_preload_libraries = 'pgvector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Restart PostgreSQL after changes
SELECT pg_reload_conf();
```

#### Memory-Specific Optimizations
```sql
-- Optimize for vector operations
ALTER SYSTEM SET shared_buffers = '512MB';  -- 25% of RAM
ALTER SYSTEM SET effective_cache_size = '2GB';  -- 75% of RAM
ALTER SYSTEM SET work_mem = '32MB';  -- For complex vector queries
ALTER SYSTEM SET maintenance_work_mem = '512MB';  -- For index creation

-- Vector-specific settings
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET parallel_tuple_cost = 0.1;
ALTER SYSTEM SET parallel_setup_cost = 1000.0;
```

### HNSW Index Optimization

#### Index Creation for 100M+ Scale
```sql
-- Create optimized HNSW index for large datasets
CREATE INDEX CONCURRENTLY idx_memories_vector_hnsw 
ON memories USING hnsw (vector) 
WITH (
    m = 16,           -- Number of connections per layer
    ef_construction = 64,  -- Search depth during construction
    ef = 40           -- Search depth during queries
);

-- Monitor index performance
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes 
WHERE indexname = 'idx_memories_vector_hnsw';
```

#### Index Maintenance
```sql
-- Regular index maintenance
REINDEX INDEX CONCURRENTLY idx_memories_vector_hnsw;

-- Analyze table statistics
ANALYZE memories;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'memories';
```

### Query Optimization

#### Optimized Memory Search
```sql
-- Use prepared statements for repeated queries
PREPARE memory_search (text, float, int) AS
SELECT 
    id,
    text,
    type,
    meta_data,
    vector,
    created_at,
    similarity(vector, $1::vector) as score
FROM memories 
WHERE 
    is_deleted = false 
    AND similarity(vector, $1::vector) > $2
ORDER BY score DESC
LIMIT $3;

-- Execute with parameters
EXECUTE memory_search('query_vector', 0.7, 10);
```

#### Partitioning for Large Datasets
```sql
-- Partition memories by tenant for better performance
CREATE TABLE memories_partitioned (
    LIKE memories INCLUDING ALL
) PARTITION BY HASH (tenant_id);

-- Create partitions
CREATE TABLE memories_part_0 PARTITION OF memories_partitioned
FOR VALUES WITH (modulus 4, remainder 0);

CREATE TABLE memories_part_1 PARTITION OF memories_partitioned
FOR VALUES WITH (modulus 4, remainder 1);

CREATE TABLE memories_part_2 PARTITION OF memories_partitioned
FOR VALUES WITH (modulus 4, remainder 2);

CREATE TABLE memories_part_3 PARTITION OF memories_partitioned
FOR VALUES WITH (modulus 4, remainder 3);
```

---

## 🔴 Redis Configuration

### Memory Optimization
```bash
# Redis configuration for high throughput
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 300
timeout 0
tcp-backlog 511
```

### Connection Pooling
```python
# Optimize Redis connections
import redis.asyncio as redis

redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50,
    retry_on_timeout=True,
    health_check_interval=30,
    socket_connect_timeout=5,
    socket_timeout=5
)

# Use connection pool
redis_client = redis.Redis(connection_pool=redis_pool)
```

### Rate Limiting Optimization
```python
# Optimize rate limiting for high traffic
RATE_LIMITS = {
    "memory:create": {"limit": 1000, "window": 3600},  # 1000 per hour
    "memory:search": {"limit": 2000, "window": 3600},  # 2000 per hour
    "identity:create": {"limit": 100, "window": 3600},  # 100 per hour
    "policy:test": {"limit": 500, "window": 3600},     # 500 per hour
    "webhook:create": {"limit": 50, "window": 3600},   # 50 per hour
}

# Redis key patterns for efficient lookups
RATE_LIMIT_KEY_PATTERN = "ratelimit:{tenant_id}:{endpoint}:{window}"
```

---

## ⚡ Application Performance

### Celery Worker Optimization
```python
# Celery configuration for high throughput
CELERY_CONFIG = {
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'broker_connection_retry_on_startup': True,
    'result_expires': 3600,
    'task_soft_time_limit': 300,  # 5 minutes
    'task_time_limit': 600,       # 10 minutes
    'worker_concurrency': 8,      # Adjust based on CPU cores
    'worker_max_memory_per_child': 200000,  # 200MB
}

# Task routing for better performance
TASK_ROUTES = {
    'manushya.tasks.memory_tasks.*': {'queue': 'memory'},
    'manushya.tasks.webhook_tasks.*': {'queue': 'webhooks'},
    'manushya.tasks.cleanup_tasks.*': {'queue': 'cleanup'},
    'manushya.tasks.monitoring_tasks.*': {'queue': 'monitoring'},
}
```

### Embedding Service Optimization
```python
# Optimize embedding generation
EMBEDDING_CONFIG = {
    'batch_size': 100,           # Process embeddings in batches
    'max_retries': 3,           # Retry failed embeddings
    'timeout': 30,              # 30 second timeout
    'cache_embeddings': True,   # Cache generated embeddings
    'parallel_workers': 4,      # Parallel embedding generation
}

# Async embedding generation
async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts efficiently."""
    if len(texts) > EMBEDDING_CONFIG['batch_size']:
        # Process in batches
        batches = [texts[i:i + EMBEDDING_CONFIG['batch_size']] 
                  for i in range(0, len(texts), EMBEDDING_CONFIG['batch_size'])]
        
        all_embeddings = []
        for batch in batches:
            embeddings = await generate_embeddings_batch(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings
    
    # Generate embeddings for single batch
    return await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
        encoding_format="float"
    )
```

### API Response Optimization
```python
# Optimize API responses
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

---

## 📈 Scaling Strategies

### Horizontal Scaling
```yaml
# docker-compose.yml for production scaling
version: '3.8'
services:
  api:
    image: manushya-api:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/manushya
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  celery-worker:
    image: manushya-api:latest
    command: celery -A manushya.tasks.celery_app worker --loglevel=info --concurrency=8
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '4'
          memory: 4G
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/manushya
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
  
  celery-beat:
    image: manushya-api:latest
    command: celery -A manushya.tasks.celery_app beat --loglevel=info
    deploy:
      replicas: 1
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/manushya
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
```

### Database Scaling
```sql
-- Read replicas for scaling
-- Primary: Write operations
-- Replica 1: Read operations
-- Replica 2: Analytics and reporting

-- Connection strings
DATABASE_WRITE_URL=postgresql://user:pass@primary:5432/manushya
DATABASE_READ_URL=postgresql://user:pass@replica1:5432/manushya
DATABASE_ANALYTICS_URL=postgresql://user:pass@replica2:5432/manushya

-- Application configuration
DATABASE_CONFIG = {
    'write_url': os.getenv('DATABASE_WRITE_URL'),
    'read_url': os.getenv('DATABASE_READ_URL'),
    'analytics_url': os.getenv('DATABASE_ANALYTICS_URL'),
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600,
}
```

### Load Balancing
```nginx
# nginx.conf for load balancing
upstream manushya_api {
    least_conn;
    server api1:8000 max_fails=3 fail_timeout=30s;
    server api2:8000 max_fails=3 fail_timeout=30s;
    server api3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.manushya.ai;
    
    location / {
        proxy_pass http://manushya_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}
```

---

## 📊 Monitoring & Alerting

### Performance Metrics
```python
# Custom metrics for monitoring
from prometheus_client import Counter, Histogram, Gauge, Summary

# API performance metrics
request_duration = Histogram('api_request_duration_seconds', 'Request duration', ['endpoint', 'method'])
memory_operations = Counter('memory_operations_total', 'Memory operations', ['operation', 'status'])
embedding_generation_time = Histogram('embedding_generation_seconds', 'Embedding generation time')
vector_search_duration = Histogram('vector_search_duration_seconds', 'Vector search duration')

# System metrics
active_connections = Gauge('database_active_connections', 'Active database connections')
redis_memory_usage = Gauge('redis_memory_bytes', 'Redis memory usage in bytes')
celery_queue_size = Gauge('celery_queue_size', 'Celery queue size', ['queue'])

# Business metrics
daily_memory_creations = Counter('daily_memory_creations_total', 'Daily memory creations')
daily_searches = Counter('daily_searches_total', 'Daily searches')
active_tenants = Gauge('active_tenants', 'Number of active tenants')
```

### Alerting Rules
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
          description: "API response time is above 2 seconds"
      
      - alert: EmbeddingFailure
        expr: embedding_generation_seconds > 30
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Embedding generation failing"
          description: "Embedding generation is taking too long"
      
      - alert: DatabaseConnections
        expr: database_active_connections > 150
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Too many active database connections"
      
      - alert: RedisMemoryUsage
        expr: redis_memory_bytes > 1.5e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Redis memory usage"
          description: "Redis memory usage is above 1.5GB"
      
      - alert: CeleryQueueBacklog
        expr: celery_queue_size > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue backlog"
          description: "Too many tasks in Celery queue"
```

### Health Checks
```python
# Comprehensive health checks
async def health_check():
    """Comprehensive health check for all services."""
    checks = {}
    
    # Database health
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            checks['database'] = True
    except Exception as e:
        checks['database'] = False
        checks['database_error'] = str(e)
    
    # Redis health
    try:
        redis_client = get_redis()
        await redis_client.ping()
        checks['redis'] = True
    except Exception as e:
        checks['redis'] = False
        checks['redis_error'] = str(e)
    
    # Celery health
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        checks['celery'] = len(active_workers) > 0
        checks['celery_workers'] = len(active_workers)
    except Exception as e:
        checks['celery'] = False
        checks['celery_error'] = str(e)
    
    # Embedding service health
    try:
        # Test embedding generation
        test_embedding = await generate_embedding("test")
        checks['embedding'] = len(test_embedding) > 0
    except Exception as e:
        checks['embedding'] = False
        checks['embedding_error'] = str(e)
    
    return checks
```

---

## 💾 Caching Strategies

### Redis Caching
```python
# Cache frequently accessed data
import redis.asyncio as redis
import json

async def get_cached_memory(memory_id: str):
    """Get memory with caching."""
    cache_key = f"memory:{memory_id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    memory = await get_memory_from_db(memory_id)
    
    # Cache for 1 hour
    await redis_client.setex(cache_key, 3600, json.dumps(memory))
    return memory

async def get_cached_identity(identity_id: str):
    """Get identity with caching."""
    cache_key = f"identity:{identity_id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    identity = await get_identity_from_db(identity_id)
    
    # Cache for 30 minutes
    await redis_client.setex(cache_key, 1800, json.dumps(identity))
    return identity
```

### Vector Search Caching
```python
# Cache vector search results
async def cached_vector_search(query: str, limit: int = 10, similarity_threshold: float = 0.7):
    """Perform vector search with caching."""
    cache_key = f"search:{hash(query)}:{limit}:{similarity_threshold}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Perform vector search
    results = await perform_vector_search(query, limit, similarity_threshold)
    
    # Cache for 30 minutes
    await redis_client.setex(cache_key, 1800, json.dumps(results))
    return results

async def invalidate_search_cache():
    """Invalidate search cache when new memories are added."""
    pattern = "search:*"
    keys = await redis_client.keys(pattern)
    if keys:
        await redis_client.delete(*keys)
```

### Policy Caching
```python
# Cache policy evaluation results
async def cached_policy_evaluation(identity_id: str, action: str, resource: str, context: dict):
    """Evaluate policy with caching."""
    cache_key = f"policy:{identity_id}:{action}:{resource}:{hash(json.dumps(context))}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Evaluate policy
    result = await evaluate_policy(identity_id, action, resource, context)
    
    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(result))
    return result
```

---

## ✅ Production Checklist

### Before Deployment
- [ ] **Database**: Optimized PostgreSQL configuration applied
- [ ] **Redis**: Memory limits and connection pooling configured
- [ ] **Celery**: Worker configuration optimized for your workload
- [ ] **Monitoring**: Prometheus metrics and alerting rules configured
- [ ] **Caching**: Redis caching strategies implemented
- [ ] **Load Balancing**: Nginx or similar configured
- [ ] **SSL/TLS**: HTTPS certificates installed
- [ ] **Backup**: Database backup strategy implemented
- [ ] **Logging**: Structured logging configured
- [ ] **Rate Limiting**: Appropriate limits set for your use case

### Performance Testing
- [ ] **Load Testing**: Test with expected concurrent users
- [ ] **Stress Testing**: Test system limits and failure modes
- [ ] **Vector Search**: Test with realistic query volumes
- [ ] **Embedding Generation**: Test OpenAI API limits
- [ ] **Database**: Test with expected data volumes
- [ ] **Memory Usage**: Monitor memory usage under load

### Monitoring Setup
- [ ] **Metrics**: Prometheus metrics collection configured
- [ ] **Alerting**: Alert rules for critical issues
- [ ] **Logging**: Centralized logging with proper levels
- [ ] **Health Checks**: Comprehensive health check endpoints
- [ ] **Dashboard**: Grafana dashboard for monitoring

### Security Checklist
- [ ] **Authentication**: JWT and API key security verified
- [ ] **Rate Limiting**: Appropriate limits to prevent abuse
- [ ] **Input Validation**: All inputs properly validated
- [ ] **SQL Injection**: Database queries properly parameterized
- [ ] **CORS**: Cross-origin requests properly configured
- [ ] **HTTPS**: All traffic encrypted in transit

---

## 🚀 Quick Performance Wins

### Immediate Optimizations
1. **Enable Redis Caching**: Cache frequently accessed data
2. **Optimize Database Queries**: Use proper indexes and prepared statements
3. **Implement Connection Pooling**: Reuse database and Redis connections
4. **Add Response Compression**: Enable gzip compression
5. **Use Background Tasks**: Move heavy operations to Celery

### Medium-term Optimizations
1. **Database Partitioning**: Partition large tables by tenant
2. **Read Replicas**: Add database read replicas for scaling
3. **CDN Integration**: Use CDN for static assets
4. **Microservices**: Split into smaller services if needed
5. **Advanced Caching**: Implement more sophisticated caching strategies

### Long-term Optimizations
1. **Database Sharding**: Shard by tenant for very large scale
2. **Event Sourcing**: Implement event sourcing for audit trails
3. **CQRS**: Separate read and write models
4. **Kubernetes**: Move to Kubernetes for better orchestration
5. **Service Mesh**: Implement service mesh for microservices

---

*This guide should be updated regularly as the system evolves and new performance optimizations are discovered.* 