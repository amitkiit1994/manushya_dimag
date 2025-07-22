"""
Comprehensive error handling with retry mechanisms and circuit breakers
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar
from datetime import datetime, timedelta

from manushya.core.exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    EmbeddingError,
    DatabaseError,
    RedisError,
    WebhookError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        
        return True  # HALF_OPEN
    
    def on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class RetryHandler:
    """Retry mechanism with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result
            
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) exceeded for {func.__name__}: {e}")
                    raise
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                
                if self.jitter:
                    import random
                    delay *= (0.5 + random.random() * 0.5)
                
                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception


def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for retry logic."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_handler = RetryHandler(max_retries, base_delay)
            return await retry_handler.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    exceptions: tuple = (Exception,)
):
    """Decorator for circuit breaker pattern."""
    def decorator(func: Callable) -> Callable:
        breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not breaker.can_execute():
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                breaker.on_success()
                return result
            except exceptions as e:
                breaker.on_failure()
                raise
        return wrapper
    return decorator


class GracefulDegradation:
    """Graceful degradation handler."""
    
    def __init__(self, fallback_func: Optional[Callable] = None):
        self.fallback_func = fallback_func
    
    async def execute_with_fallback(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with fallback."""
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.warning(f"Primary function failed, using fallback: {e}")
            
            if self.fallback_func:
                try:
                    if asyncio.iscoroutinefunction(self.fallback_func):
                        return await self.fallback_func(*args, **kwargs)
                    else:
                        return self.fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback function also failed: {fallback_error}")
                    raise
            
            raise


def graceful_degradation(fallback_func: Optional[Callable] = None):
    """Decorator for graceful degradation."""
    def decorator(func: Callable) -> Callable:
        degradation = GracefulDegradation(fallback_func)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await degradation.execute_with_fallback(func, *args, **kwargs)
        return wrapper
    return decorator


class ErrorHandler:
    """Centralized error handling."""
    
    @staticmethod
    def handle_database_error(error: Exception) -> DatabaseError:
        """Handle database errors."""
        logger.error(f"Database error: {error}")
        return DatabaseError(f"Database operation failed: {str(error)}")
    
    @staticmethod
    def handle_redis_error(error: Exception) -> RedisError:
        """Handle Redis errors."""
        logger.error(f"Redis error: {error}")
        return RedisError(f"Redis operation failed: {str(error)}")
    
    @staticmethod
    def handle_embedding_error(error: Exception) -> EmbeddingError:
        """Handle embedding service errors."""
        logger.error(f"Embedding error: {error}")
        return EmbeddingError(f"Embedding generation failed: {str(error)}")
    
    @staticmethod
    def handle_webhook_error(error: Exception) -> WebhookError:
        """Handle webhook errors."""
        logger.error(f"Webhook error: {error}")
        return WebhookError(f"Webhook delivery failed: {str(error)}")
    
    @staticmethod
    def handle_authentication_error(error: Exception) -> AuthenticationError:
        """Handle authentication errors."""
        logger.error(f"Authentication error: {error}")
        return AuthenticationError(f"Authentication failed: {str(error)}")
    
    @staticmethod
    def handle_validation_error(error: Exception) -> ValidationError:
        """Handle validation errors."""
        logger.error(f"Validation error: {error}")
        return ValidationError(f"Validation failed: {str(error)}")
    
    @staticmethod
    def handle_rate_limit_error(error: Exception) -> RateLimitError:
        """Handle rate limit errors."""
        logger.error(f"Rate limit error: {error}")
        return RateLimitError(f"Rate limit exceeded: {str(error)}")
    
    @staticmethod
    def handle_not_found_error(error: Exception) -> NotFoundError:
        """Handle not found errors."""
        logger.error(f"Not found error: {error}")
        return NotFoundError(f"Resource not found: {str(error)}")


class AsyncErrorHandler:
    """Async error handling utilities."""
    
    @staticmethod
    async def handle_async_operation(
        operation: Callable,
        *args,
        error_handler: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """Handle async operations with error handling."""
        try:
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            return result
        except Exception as e:
            if error_handler:
                return await error_handler(e)
            raise
    
    @staticmethod
    async def handle_external_api_call(
        api_call: Callable,
        *args,
        timeout: float = 30.0,
        **kwargs
    ) -> Any:
        """Handle external API calls with timeout and retry."""
        try:
            return await asyncio.wait_for(api_call(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"API call timed out after {timeout} seconds")
            raise TimeoutError(f"API call timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise


class ErrorMetrics:
    """Error tracking and metrics."""
    
    def __init__(self):
        self.error_counts = {}
        self.error_timestamps = []
    
    def record_error(self, error_type: str, error: Exception):
        """Record an error for metrics."""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        self.error_timestamps.append({
            'type': error_type,
            'timestamp': datetime.utcnow(),
            'message': str(error)
        })
        
        # Keep only last 1000 errors
        if len(self.error_timestamps) > 1000:
            self.error_timestamps = self.error_timestamps[-1000:]
    
    def get_error_stats(self, hours: int = 24) -> dict:
        """Get error statistics for the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            e for e in self.error_timestamps 
            if e['timestamp'] >= cutoff
        ]
        
        error_types = {}
        for error in recent_errors:
            error_type = error['type']
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        return {
            'total_errors': len(recent_errors),
            'error_types': error_types,
            'error_rate_per_hour': len(recent_errors) / hours
        }


# Global error metrics instance
error_metrics = ErrorMetrics()


def track_errors(func: Callable) -> Callable:
    """Decorator to track errors in functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_metrics.record_error(type(e).__name__, e)
            raise
    return wrapper


class HealthCheck:
    """Health check utilities."""
    
    @staticmethod
    async def check_database_health(db_session) -> bool:
        """Check database health."""
        try:
            from sqlalchemy import text
            await db_session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @staticmethod
    async def check_redis_health(redis_client) -> bool:
        """Check Redis health."""
        try:
            await redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    @staticmethod
    async def check_embedding_service_health() -> bool:
        """Check embedding service health."""
        try:
            from manushya.services.embedding_service import generate_embedding
            await generate_embedding("health check")
            return True
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return False
    
    @staticmethod
    async def comprehensive_health_check(
        db_session,
        redis_client
    ) -> dict:
        """Perform comprehensive health check."""
        checks = {
            'database': await HealthCheck.check_database_health(db_session),
            'redis': await HealthCheck.check_redis_health(redis_client),
            'embedding_service': await HealthCheck.check_embedding_service_health(),
        }
        
        overall_health = all(checks.values())
        
        return {
            'healthy': overall_health,
            'checks': checks,
            'timestamp': datetime.utcnow().isoformat()
        } 