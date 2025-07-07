import secrets

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request

from manushya.config import settings


class SSOService:
    """SSO service for OAuth2/OIDC integration."""
    oauth = None

    @classmethod
    def get_oauth(cls):
        if cls.oauth is None:
            cls.oauth = OAuth()
            for provider, conf in settings.sso_providers.items():
                cls.oauth.register(
                    name=provider,
                    client_id=conf["client_id"],
                    client_secret=conf["client_secret"],
                    authorize_url=conf["authorize_url"],
                    access_token_url=conf["access_token_url"],
                    userinfo_endpoint=conf["userinfo_url"],
                    client_kwargs={"scope": conf["scope"]},
                )
        return cls.oauth

    @classmethod
    async def get_login_url(cls, provider: str, request: Request) -> str:
        oauth = cls.get_oauth()
        if provider not in settings.sso_providers:
            raise HTTPException(400, f"Unknown SSO provider: {provider}")
        redirect_uri = settings.sso_providers[provider]["redirect_uri"]
        state = secrets.token_urlsafe(16)
        nonce = secrets.token_urlsafe(16)
        request.session["sso_state"] = state
        request.session["sso_nonce"] = nonce
        client = getattr(oauth, provider)
        return await client.authorize_redirect(request, redirect_uri, state=state, nonce=nonce)

    @classmethod
    async def handle_callback(cls, provider: str, request: Request):
        oauth = cls.get_oauth()
        if provider not in settings.sso_providers:
            raise HTTPException(400, f"Unknown SSO provider: {provider}")
        client = getattr(oauth, provider)
        token = await client.authorize_access_token(request)
        userinfo = await client.parse_id_token(request, token)
        # You can now use userinfo to create or update your Identity
        return userinfo
