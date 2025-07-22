"""
JWT and API Key Authentication utilities for Manushya.ai
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.config import settings
from manushya.core.api_key_auth import get_current_identity_from_api_key
from manushya.core.exceptions import AuthenticationError
from manushya.core.session_service import SessionService
from manushya.db.database import get_db
from manushya.db.models import Identity

# Security scheme
security = HTTPBearer()


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}") from e


async def get_current_identity_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Identity:
    """Get current authenticated identity from JWT token."""
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        identity_id = payload.get("sub")
        if identity_id is None:
            raise AuthenticationError("Token missing identity ID")
        # Get identity from database
        stmt = select(Identity).where(
            Identity.id == uuid.UUID(identity_id), Identity.is_active
        )
        result = await db.execute(stmt)
        identity = result.scalar_one_or_none()
        if identity is None:
            raise AuthenticationError("Identity not found or inactive")
        return identity
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


async def get_current_identity(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Identity:
    """Get current authenticated identity from JWT token or API key."""
    try:
        # First try API key authentication
        if credentials.credentials.startswith("mk_"):
            identity = await get_current_identity_from_api_key(credentials, db)
            if identity:
                return identity
        # Fallback to JWT authentication
        return await get_current_identity_jwt(credentials, db)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


async def get_optional_identity(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Identity | None:
    """Get current identity if authenticated, otherwise None."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        # Try API key first
        if token.startswith("mk_"):
            from manushya.core.api_key_auth import ApiKeyAuth

            identity = await ApiKeyAuth.validate_api_key(token, db)
            if identity:
                return identity
        # Fallback to JWT
        payload = verify_token(token)
        identity_id = payload.get("sub")
        if identity_id is None:
            return None
        stmt = select(Identity).where(
            Identity.id == uuid.UUID(identity_id), Identity.is_active
        )
        result = await db.execute(stmt)
        identity = result.scalar_one_or_none()
        return identity
    except (AuthenticationError, JWTError):
        return None


def create_identity_token(identity: Identity) -> str:
    """Create JWT token for an identity."""
    return create_access_token(
        data={
            "sub": str(identity.id),
            "external_id": identity.external_id,
            "role": identity.role,
            "claims": identity.claims,
            "tenant_id": str(identity.tenant_id) if identity.tenant_id else None,
        }
    )


async def create_session_with_tokens(
    identity: Identity, request: Request, db: AsyncSession, expires_in_days: int = 30
) -> dict[str, str | int]:
    """Create a session and return both access and refresh tokens."""
    # Create session
    session, refresh_token = await SessionService.create_session(
        db=db, identity=identity, request=request, expires_in_days=expires_in_days
    )
    # Create access token
    access_token = create_identity_token(identity)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_expiration_minutes * 60,  # seconds
    }


async def refresh_access_token(
    refresh_token: str, db: AsyncSession
) -> dict[str, str | int] | None:
    """Refresh access token using refresh token."""
    # Get identity from refresh token
    identity = await SessionService.get_identity_from_refresh_token(db, refresh_token)
    if not identity:
        return None
    # Create new access token
    access_token = create_identity_token(identity)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,  # Return same refresh token
        "token_type": "bearer",
        "expires_in": settings.jwt_expiration_minutes * 60,  # seconds
    }
