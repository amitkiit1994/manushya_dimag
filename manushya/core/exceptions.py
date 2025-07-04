"""
Custom exceptions for Manushya.ai
"""

from typing import Any, Dict, Optional


class ManushyaException(Exception):
    """Base exception for Manushya.ai application."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(ManushyaException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(ManushyaException):
    """Raised when authorization fails."""
    pass


class ValidationError(ManushyaException):
    """Raised when data validation fails."""
    pass


class NotFoundError(ManushyaException):
    """Raised when a resource is not found."""
    pass


class ConflictError(ManushyaException):
    """Raised when there's a conflict with existing data."""
    pass


class RateLimitError(ManushyaException):
    """Raised when rate limit is exceeded."""
    pass


class PolicyViolationError(ManushyaException):
    """Raised when a policy rule is violated."""
    pass


class EmbeddingError(ManushyaException):
    """Raised when embedding generation fails."""
    pass


class EncryptionError(ManushyaException):
    """Raised when encryption/decryption fails."""
    pass


class DatabaseError(ManushyaException):
    """Raised when database operations fail."""
    pass


class ExternalServiceError(ManushyaException):
    """Raised when external service calls fail."""
    pass 