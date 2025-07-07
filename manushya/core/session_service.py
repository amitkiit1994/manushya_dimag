"""
Session management service for Manushya.ai
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.models import Identity, Session


class SessionService:
    """Service for managing user sessions and refresh tokens."""

    @staticmethod
    def generate_refresh_token() -> str:
        """Generate a secure refresh token."""
        return f"rt_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_refresh_token(refresh_token: str) -> str:
        """Hash a refresh token for storage."""
        return hashlib.sha256(refresh_token.encode()).hexdigest()

    @staticmethod
    def calculate_session_expiration(days: int = 30) -> datetime:
        """Calculate session expiration date."""
        return datetime.now(timezone.utc) + timedelta(days=days)

    @staticmethod
    def extract_device_info(request: Request) -> dict:
        """Extract device information from request."""
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else None

        # Basic device detection
        device_info = {
            "user_agent": user_agent,
            "ip_address": ip_address,
            "platform": "unknown",
            "browser": "unknown",
        }

        # Simple user agent parsing (in production, use a proper library)
        ua_lower = user_agent.lower()
        if "chrome" in ua_lower:
            device_info["browser"] = "chrome"
        elif "firefox" in ua_lower:
            device_info["browser"] = "firefox"
        elif "safari" in ua_lower:
            device_info["browser"] = "safari"
        elif "edge" in ua_lower:
            device_info["browser"] = "edge"

        if "mobile" in ua_lower:
            device_info["platform"] = "mobile"
        elif "tablet" in ua_lower:
            device_info["platform"] = "tablet"
        elif "windows" in ua_lower:
            device_info["platform"] = "windows"
        elif "mac" in ua_lower:
            device_info["platform"] = "mac"
        elif "linux" in ua_lower:
            device_info["platform"] = "linux"

        return device_info

    @staticmethod
    async def create_session(
        db: AsyncSession,
        identity: Identity,
        request: Request,
        expires_in_days: int = 30
    ) -> tuple[Session, str]:
        """Create a new session and return session object and refresh token."""
        # Generate refresh token
        refresh_token = SessionService.generate_refresh_token()
        refresh_token_hash = SessionService.hash_refresh_token(refresh_token)

        # Calculate expiration
        expires_at = SessionService.calculate_session_expiration(expires_in_days)

        # Extract device info
        device_info = SessionService.extract_device_info(request)

        # Create session
        session = Session(
            identity_id=identity.id,
            refresh_token_hash=refresh_token_hash,
            device_info=device_info,
            ip_address=device_info.get("ip_address"),
            user_agent=device_info.get("user_agent"),
            is_active=True,
            expires_at=expires_at,
            last_used_at=datetime.now(timezone.utc),
            tenant_id=identity.tenant_id,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session, refresh_token

    @staticmethod
    async def validate_refresh_token(
        db: AsyncSession,
        refresh_token: str
    ) -> Session | None:
        """Validate refresh token and return session if valid."""
        if not refresh_token:
            return None

        # Hash the provided refresh token
        refresh_token_hash = SessionService.hash_refresh_token(refresh_token)

        # Find the session
        stmt = select(Session).where(Session.refresh_token_hash == refresh_token_hash)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session or not session.is_valid:
            return None

        # Update last used timestamp
        session.last_used_at = datetime.now(timezone.utc)
        await db.commit()

        return session

    @staticmethod
    async def get_identity_from_refresh_token(
        db: AsyncSession,
        refresh_token: str
    ) -> Identity | None:
        """Get identity from refresh token."""
        session = await SessionService.validate_refresh_token(db, refresh_token)
        if not session:
            return None

        # Get the associated identity
        stmt = select(Identity).where(Identity.id == session.identity_id)
        result = await db.execute(stmt)
        identity = result.scalar_one_or_none()

        if not identity or not identity.is_active:
            return None

        return identity

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        session_id: str
    ) -> bool:
        """Revoke a session by marking it as inactive."""
        stmt = select(Session).where(Session.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return False

        session.is_active = False
        await db.commit()

        return True

    @staticmethod
    async def revoke_all_sessions_for_identity(
        db: AsyncSession,
        identity_id: str,
        except_session_id: str | None = None
    ) -> int:
        """Revoke all sessions for an identity except the specified one."""
        stmt = select(Session).where(
            Session.identity_id == identity_id,
            Session.is_active
        )

        if except_session_id:
            stmt = stmt.where(Session.id != except_session_id)

        result = await db.execute(stmt)
        sessions = result.scalars().all()

        revoked_count = 0
        for session in sessions:
            session.is_active = False
            revoked_count += 1

        await db.commit()
        return revoked_count

    @staticmethod
    async def get_active_sessions_for_identity(
        db: AsyncSession,
        identity_id: str
    ) -> list[Session]:
        """Get all active sessions for an identity."""
        stmt = select(Session).where(
            Session.identity_id == identity_id,
            Session.is_active
        ).order_by(Session.last_used_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def cleanup_expired_sessions(
        db: AsyncSession
    ) -> int:
        """Clean up expired sessions."""
        stmt = select(Session).where(
            Session.expires_at < datetime.now(timezone.utc),
            Session.is_active
        )

        result = await db.execute(stmt)
        expired_sessions = result.scalars().all()

        cleaned_count = 0
        for session in expired_sessions:
            session.is_active = False
            cleaned_count += 1

        await db.commit()
        return cleaned_count
