"""
API Key authentication service for Manushya.ai
"""

import hashlib
import secrets
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.database import get_db
from manushya.db.models import ApiKey, Identity

security = HTTPBearer()


class ApiKeyAuth:
    """API Key authentication service."""

    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key."""
        return f"mk_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    async def validate_api_key(
        api_key: str,
        db: AsyncSession,
        required_scopes: list[str] | None = None
    ) -> Identity | None:
        """Validate an API key and return the associated identity."""
        if not api_key:
            return None

        # Hash the provided API key
        key_hash = ApiKeyAuth.hash_api_key(api_key)

        # Find the API key in the database
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await db.execute(stmt)
        api_key_obj = result.scalar_one_or_none()

        if not api_key_obj or not api_key_obj.is_valid:
            return None

        # Check scopes if required
        if required_scopes:
            if not all(scope in api_key_obj.scopes for scope in required_scopes):
                return None

        # Update last used timestamp
        api_key_obj.last_used_at = datetime.utcnow()
        await db.commit()

        # Get the associated identity
        stmt = select(Identity).where(Identity.id == api_key_obj.identity_id)
        result = await db.execute(stmt)
        identity = result.scalar_one_or_none()

        if not identity or not identity.is_active:
            return None

        return identity


async def get_current_identity_from_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Identity | None:
    """Get current identity from API key authentication."""
    try:
        # Check if it's an API key (starts with 'mk_')
        if credentials.credentials.startswith('mk_'):
            identity = await ApiKeyAuth.validate_api_key(credentials.credentials, db)
            if identity:
                return identity

        # If not an API key or invalid, return None (fallback to JWT)
        return None

    except Exception:
        return None


async def require_api_key_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Identity:
    """Require API key authentication and return the identity."""
    if not credentials.credentials.startswith('mk_'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required (must start with 'mk_')",
            headers={"WWW-Authenticate": "Bearer"},
        )

    identity = await ApiKeyAuth.validate_api_key(credentials.credentials, db)
    if not identity:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return identity


async def require_api_key_scopes(
    required_scopes: list[str],
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Identity:
    """Require API key authentication with specific scopes."""
    if not credentials.credentials.startswith('mk_'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required (must start with 'mk_')",
            headers={"WWW-Authenticate": "Bearer"},
        )

    identity = await ApiKeyAuth.validate_api_key(
        credentials.credentials,
        db,
        required_scopes=required_scopes
    )
    if not identity:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient API key scopes",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return identity
