"""
JWT Authentication utilities for Manushya.ai
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
from manushya.core.exceptions import AuthenticationError
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


async def get_current_identity(
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


async def get_optional_identity(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Identity | None:
    """Get current identity if authenticated, otherwise None."""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
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
        }
    )
