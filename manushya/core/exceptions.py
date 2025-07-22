"""
Custom exceptions for Manushya.ai
"""

from typing import Any

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


class ManushyaException(Exception):
    """Base exception for Manushya.ai application."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(ManushyaException):
    """Raised when authentication fails."""


class AuthorizationError(ManushyaException):
    """Raised when authorization fails."""


class ValidationError(ManushyaException):
    """Raised when data validation fails."""


class NotFoundError(ManushyaException):
    """Raised when a resource is not found."""


class ConflictError(ManushyaException):
    """Raised when there's a conflict with existing data."""


class RateLimitError(ManushyaException):
    """Raised when rate limit is exceeded."""


class PolicyViolationError(ManushyaException):
    """Raised when a policy rule is violated."""


class AccessDeniedError(ManushyaException):
    """Raised when access is denied."""


class PolicyError(ManushyaException):
    """Raised when there's an error with policy operations."""


class EmbeddingError(ManushyaException):
    """Raised when embedding generation fails."""


class EncryptionError(ManushyaException):
    """Raised when encryption/decryption fails."""


class DatabaseError(ManushyaException):
    """Raised when database operations fail."""


class ExternalServiceError(ManushyaException):
    """Raised when external service calls fail."""


class ErrorHandler:
    @staticmethod
    async def handle_exception(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), url=str(request.url))
        request_id = getattr(request.state, "request_id", None)
        if request_id is None:
            request_id = ""
        request_id = str(request_id)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "details": str(exc),
                "request_id": request_id,
            },
        )

    @staticmethod
    def format_error(message: str, details: str | None = None, code: int = 400):
        return {"error": message, "details": details, "code": code}
