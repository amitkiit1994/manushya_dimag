from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.core.auth import create_session_with_tokens
from manushya.db.database import get_db
from manushya.db.models import Identity
from manushya.services.sso_service import SSOService

router = APIRouter(tags=["sso"])

@router.get("/login/{provider}", summary="Initiate SSO login")
async def sso_login(provider: str, request: Request):
    """Initiate SSO login with a provider. Redirects to the provider's auth page."""
    try:
        return await SSOService.get_login_url(provider, request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSO login failed: {str(e)}") from e

@router.get("/callback/{provider}", summary="SSO callback")
async def sso_callback(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle SSO callback. Creates or updates user and returns tokens."""
    try:
        # Get user info from SSO provider
        userinfo = await SSOService.handle_callback(provider, request)

        # Extract user info
        sso_external_id = userinfo.get("sub") or userinfo.get("id")
        email = userinfo.get("email")
        name = userinfo.get("name", "")

        if not sso_external_id:
            raise HTTPException(status_code=400, detail="Invalid SSO response: missing user ID")

        # Check if user already exists
        stmt = select(Identity).where(
            Identity.sso_provider == provider,
            Identity.sso_external_id == sso_external_id
        )
        result = await db.execute(stmt)
        identity = result.scalar_one_or_none()

        if identity:
            # Update existing user
            identity.sso_email = email
            identity.sso_metadata = userinfo
            identity.updated_at = datetime.utcnow()
        else:
            # Create new user
            identity = Identity(
                external_id=f"{provider}_{sso_external_id}",
                role="user",  # Default role
                claims={
                    "sso_provider": provider,
                    "name": name,
                    "email": email
                },
                sso_provider=provider,
                sso_external_id=sso_external_id,
                sso_email=email,
                sso_metadata=userinfo
            )
            db.add(identity)

        await db.commit()
        await db.refresh(identity)

        # Create session and tokens
        tokens = await create_session_with_tokens(identity, request, db)

        return JSONResponse({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "user": {
                "id": str(identity.id),
                "email": email,
                "name": name,
                "provider": provider
            }
        })

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSO callback failed: {str(e)}") from e
