"""
Production-grade SSO service with OAuth2/OIDC support
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.config import settings
from manushya.core.auth import create_identity_token
from manushya.core.session_service import SessionService
from manushya.db.models import Identity, SSOProvider, SSOSession

logger = logging.getLogger(__name__)
# OAuth2/OIDC provider configurations
OAUTH_PROVIDERS = {
    "google": {
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile",
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
    },
}


class SSOService:
    """Production-grade SSO service with OAuth2/OIDC support."""

    def __init__(
        self,
        db: AsyncSession,
        sso_providers: dict[str, Any] = None,
        default_provider: str = None,
    ):
        self.db = db
        self.sso_providers = sso_providers or {}
        self.default_provider = default_provider

    async def initiate_sso(
        self,
        provider: str,
        tenant_id: str,
        redirect_uri: str,
        state: str | None = None,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Initiate SSO flow with OAuth2 provider.
        Args:
            provider: OAuth2 provider name (google, microsoft, github, okta)
            tenant_id: Tenant ID for the SSO session
            redirect_uri: Callback URL
            state: Optional state parameter for security
            scope: Optional custom scope
        Returns:
            Authorization URL and session data
        """
        if provider not in OAUTH_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported SSO provider: {provider}",
            )
        provider_config = OAUTH_PROVIDERS[provider]
        # Generate state if not provided
        if not state:
            state = secrets.token_urlsafe(32)
        # Generate nonce for OIDC
        nonce = secrets.token_urlsafe(32)
        # Create SSO session
        sso_session = SSOSession(
            provider=provider,
            tenant_id=tenant_id,
            state=state,
            nonce=nonce,
            redirect_uri=redirect_uri,
            scope=scope or provider_config["scope"],
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        self.db.add(sso_session)
        await self.db.commit()
        await self.db.refresh(sso_session)
        # Build authorization URL
        auth_params = {
            "client_id": provider_config["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": sso_session.scope,
            "state": state,
            "nonce": nonce,
        }
        # Add provider-specific parameters
        if provider == "microsoft":
            auth_params["response_mode"] = "query"
        auth_url = f"{provider_config['authorization_url']}?{urlencode(auth_params)}"
        logger.info(f"Initiated SSO flow for provider {provider}, tenant {tenant_id}")
        return {
            "authorization_url": auth_url,
            "state": state,
            "session_id": str(sso_session.id),
            "expires_at": sso_session.expires_at.isoformat(),
        }

    async def handle_callback(
        self,
        provider: str,
        code: str,
        state: str,
        error: str | None = None,
        error_description: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle OAuth2 callback and exchange code for tokens.
        Args:
            provider: OAuth2 provider name
            code: Authorization code from provider
            state: State parameter for verification
            error: OAuth2 error if any
            error_description: Error description if any
        Returns:
            Identity token and user information
        """
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth2 error: {error} - {error_description}",
            )
        # Verify SSO session
        sso_session = await self._get_sso_session(provider, state)
        if not sso_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired SSO session",
            )
        # Exchange code for tokens
        tokens = await self._exchange_code_for_tokens(
            provider, code, sso_session.redirect_uri
        )
        # Get user information
        user_info = await self._get_user_info(provider, tokens["access_token"])
        # Create or update identity
        identity = await self._create_or_update_identity(
            provider, user_info, sso_session.tenant_id
        )
        # Create session and tokens
        session, refresh_token = await SessionService.create_session(
            self.db, identity, sso_session.redirect_uri
        )
        # Generate access token
        access_token = create_identity_token(identity)
        # Mark SSO session as completed
        sso_session.completed_at = datetime.now(UTC)
        sso_session.user_id = str(identity.id)
        await self.db.commit()
        logger.info(
            f"SSO callback completed for provider {provider}, user {identity.external_id}"
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "identity": {
                "id": str(identity.id),
                "external_id": identity.external_id,
                "role": identity.role,
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
            },
        }

    async def _get_sso_session(self, provider: str, state: str) -> SSOSession | None:
        """Get SSO session by provider and state."""
        stmt = select(SSOSession).where(
            and_(
                SSOSession.provider == provider,
                SSOSession.state == state,
                SSOSession.expires_at > datetime.now(UTC),
                SSOSession.completed_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _exchange_code_for_tokens(
        self, provider: str, code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        provider_config = OAUTH_PROVIDERS[provider]
        token_data = {
            "client_id": provider_config["client_id"],
            "client_secret": provider_config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        headers = {"Accept": "application/json"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                provider_config["token_url"], data=token_data, headers=headers
            )
            if response.status_code != 200:
                logger.error(f"Token exchange failed for {provider}: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange authorization code: {response.text}",
                )
            tokens = response.json()
            # Handle GitHub's different response format
            if provider == "github":
                tokens = {"access_token": tokens.get("access_token")}
            return tokens

    async def _get_user_info(self, provider: str, access_token: str) -> dict[str, Any]:
        """Get user information from OAuth2 provider."""
        provider_config = OAUTH_PROVIDERS[provider]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                provider_config["userinfo_url"], headers=headers
            )
            if response.status_code != 200:
                logger.error(f"User info fetch failed for {provider}: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to fetch user information: {response.text}",
                )
            user_info = response.json()
            # Normalize user info across providers
            normalized_info = {
                "id": user_info.get("id") or user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name") or user_info.get("display_name"),
                "picture": user_info.get("picture") or user_info.get("avatar_url"),
                "provider": provider,
            }
            return normalized_info

    async def _create_or_update_identity(
        self, provider: str, user_info: dict[str, Any], tenant_id: str
    ) -> Identity:
        """Create or update identity from SSO user info."""
        external_id = f"{provider}:{user_info['id']}"
        # Check if identity exists
        stmt = select(Identity).where(
            and_(Identity.external_id == external_id, Identity.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        identity = result.scalar_one_or_none()
        if identity:
            # Update existing identity
            identity.sso_email = user_info.get("email")
            identity.updated_at = datetime.now(UTC)
            await self.db.commit()
            await self.db.refresh(identity)
            logger.info(f"Updated existing identity {identity.id} from SSO")
        else:
            # Create new identity
            identity = Identity(
                external_id=external_id,
                sso_email=user_info.get("email"),
                role="user",  # Default role for SSO users
                tenant_id=tenant_id,
                claims={
                    "sso_provider": provider,
                    "sso_id": user_info["id"],
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                },
            )
            self.db.add(identity)
            await self.db.commit()
            await self.db.refresh(identity)
            logger.info(f"Created new identity {identity.id} from SSO")
        return identity

    async def get_sso_providers(self, tenant_id: str) -> list[dict[str, Any]]:
        """Get available SSO providers for a tenant."""
        stmt = select(SSOProvider).where(
            and_(SSOProvider.tenant_id == tenant_id, SSOProvider.is_active)
        )
        result = await self.db.execute(stmt)
        providers = result.scalars().all()
        return [
            {
                "id": str(provider.id),
                "name": provider.name,
                "provider_type": provider.provider_type,
                "client_id": provider.client_id,
                "is_active": provider.is_active,
                "created_at": provider.created_at.isoformat(),
            }
            for provider in providers
        ]

    async def create_sso_provider(
        self,
        tenant_id: str,
        name: str,
        provider_type: str,
        client_id: str,
        client_secret: str,
        config: dict[str, Any] | None = None,
    ) -> SSOProvider:
        """Create a new SSO provider configuration."""
        provider = SSOProvider(
            tenant_id=tenant_id,
            name=name,
            provider_type=provider_type,
            client_id=client_id,
            client_secret=client_secret,
            config=config or {},
            is_active=True,
        )
        self.db.add(provider)
        await self.db.commit()
        await self.db.refresh(provider)
        logger.info(f"Created SSO provider {provider.id} for tenant {tenant_id}")
        return provider

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired SSO sessions."""
        cutoff = datetime.now(UTC) - timedelta(hours=1)
        stmt = select(SSOSession).where(
            and_(SSOSession.expires_at < cutoff, SSOSession.completed_at.is_(None))
        )
        result = await self.db.execute(stmt)
        expired_sessions = result.scalars().all()
        deleted_count = 0
        for session in expired_sessions:
            await self.db.delete(session)
            deleted_count += 1
        if deleted_count > 0:
            await self.db.commit()
            logger.info(f"Cleaned up {deleted_count} expired SSO sessions")
        return deleted_count
