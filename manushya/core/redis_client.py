"""
Redis client for Manushya.ai
"""

import redis.asyncio as redis
from manushya.config import settings

# Redis connection
redis_client = None

async def get_redis():
    """Get Redis client instance."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return redis_client

async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None 