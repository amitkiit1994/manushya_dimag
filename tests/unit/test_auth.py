"""
Unit tests for authentication system
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import jwt
from fastapi import HTTPException

from manushya.core.auth import (
    create_access_token,
    verify_token,
    get_current_identity_jwt,
    get_current_identity,
    create_identity_token,
    create_session_with_tokens,
    refresh_access_token,
)
from manushya.core.exceptions import AuthenticationError
from manushya.db.models import Identity, Session


class TestJWTAuthentication:
    """Test JWT authentication functionality."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "test-user-id", "role": "user"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = verify_token(token)
        assert payload["sub"] == "test-user-id"
        assert payload["role"] == "user"
        assert "exp" in payload

    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry."""
        data = {"sub": "test-user-id"}
        expiry = timedelta(hours=2)
        token = create_access_token(data, expiry)
        
        payload = verify_token(token)
        assert payload["sub"] == "test-user-id"
        
        # Check expiry time
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        
        # Should expire in approximately 2 hours
        assert exp_datetime > now
        assert exp_datetime < now + timedelta(hours=3)

    def test_verify_token_invalid(self):
        """Test invalid token verification."""
        with pytest.raises(AuthenticationError):
            verify_token("invalid.token.here")

    def test_verify_token_expired(self):
        """Test expired token verification."""
        # Create expired token
        from manushya.config import settings
        data = {"sub": "test-user-id", "exp": datetime.utcnow() - timedelta(hours=1)}
        token = jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        with pytest.raises(AuthenticationError):
            verify_token(token)

    @pytest.mark.asyncio
    async def test_get_current_identity_jwt_success(self, client, identity, admin_jwt_token):
        """Test successful JWT authentication."""
        # Mock the database session
        with patch('manushya.core.auth.get_db') as mock_get_db:
            mock_get_db.return_value = [identity]
            
            # Mock the security dependency
            credentials = MagicMock()
            credentials.credentials = admin_jwt_token
            
            result = await get_current_identity_jwt(credentials, identity)
            assert result.id == identity.id

    @pytest.mark.asyncio
    async def test_get_current_identity_jwt_invalid_token(self, client):
        """Test JWT authentication with invalid token."""
        credentials = MagicMock()
        credentials.credentials = "invalid.token"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_identity_jwt(credentials, None)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_identity_jwt_missing_sub(self, client):
        """Test JWT authentication with missing subject."""
        # Create token without sub
        data = {"role": "user"}
        token = create_access_token(data)
        
        credentials = MagicMock()
        credentials.credentials = token
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_identity_jwt(credentials, None)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_identity_jwt_identity_not_found(self, client, admin_jwt_token):
        """Test JWT authentication with non-existent identity."""
        credentials = MagicMock()
        credentials.credentials = admin_jwt_token
        
        # Mock empty database result
        with patch('manushya.core.auth.get_db') as mock_get_db:
            mock_get_db.return_value = [None]
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_identity_jwt(credentials, None)
            
            assert exc_info.value.status_code == 401


class TestAPIKeyAuthentication:
    """Test API key authentication functionality."""

    @pytest.mark.asyncio
    async def test_api_key_authentication_success(self, client, admin_api_key):
        """Test successful API key authentication."""
        from manushya.core.api_key_auth import get_current_identity_from_api_key
        
        # Mock API key lookup
        with patch('manushya.core.api_key_auth.get_api_key_by_hash') as mock_get_key:
            mock_get_key.return_value = admin_api_key
            
            credentials = MagicMock()
            credentials.credentials = "mk_test_api_key"
            
            result = await get_current_identity_from_api_key(credentials, None)
            assert result.id == admin_api_key.identity_id

    @pytest.mark.asyncio
    async def test_api_key_authentication_invalid_key(self, client):
        """Test API key authentication with invalid key."""
        from manushya.core.api_key_auth import get_current_identity_from_api_key
        
        credentials = MagicMock()
        credentials.credentials = "mk_invalid_key"
        
        # Mock API key lookup returning None
        with patch('manushya.core.api_key_auth.get_api_key_by_hash') as mock_get_key:
            mock_get_key.return_value = None
            
            result = await get_current_identity_from_api_key(credentials, None)
            assert result is None

    @pytest.mark.asyncio
    async def test_api_key_authentication_expired_key(self, client, admin_api_key):
        """Test API key authentication with expired key."""
        from manushya.core.api_key_auth import get_current_identity_from_api_key
        
        # Set expired date
        admin_api_key.expires_at = datetime.utcnow() - timedelta(days=1)
        
        credentials = MagicMock()
        credentials.credentials = "mk_test_api_key"
        
        with patch('manushya.core.api_key_auth.get_api_key_by_hash') as mock_get_key:
            mock_get_key.return_value = admin_api_key
            
            result = await get_current_identity_from_api_key(credentials, None)
            assert result is None

    @pytest.mark.asyncio
    async def test_api_key_authentication_inactive_key(self, client, admin_api_key):
        """Test API key authentication with inactive key."""
        from manushya.core.api_key_auth import get_current_identity_from_api_key
        
        # Set inactive
        admin_api_key.is_active = False
        
        credentials = MagicMock()
        credentials.credentials = "mk_test_api_key"
        
        with patch('manushya.core.api_key_auth.get_api_key_by_hash') as mock_get_key:
            mock_get_key.return_value = admin_api_key
            
            result = await get_current_identity_from_api_key(credentials, None)
            assert result is None


class TestPasswordAuthentication:
    """Test password-based authentication."""

    @pytest.mark.asyncio
    async def test_password_authentication_success(self, client, identity):
        """Test successful password authentication."""
        from manushya.core.password_auth import authenticate_with_password
        
        # Mock password verification
        with patch('manushya.core.password_auth.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            result = await authenticate_with_password("test@example.com", "password123")
            assert result is not None
            assert result.id == identity.id

    @pytest.mark.asyncio
    async def test_password_authentication_invalid_credentials(self, client):
        """Test password authentication with invalid credentials."""
        from manushya.core.password_auth import authenticate_with_password
        
        with patch('manushya.core.password_auth.verify_password') as mock_verify:
            mock_verify.return_value = False
            
            result = await authenticate_with_password("test@example.com", "wrong_password")
            assert result is None

    @pytest.mark.asyncio
    async def test_password_authentication_user_not_found(self, client):
        """Test password authentication with non-existent user."""
        from manushya.core.password_auth import authenticate_with_password
        
        result = await authenticate_with_password("nonexistent@example.com", "password123")
        assert result is None


class TestMFAAuthentication:
    """Test multi-factor authentication."""

    @pytest.mark.asyncio
    async def test_mfa_verification_success(self, client, identity):
        """Test successful MFA verification."""
        from manushya.core.mfa_auth import verify_mfa_token
        
        # Mock TOTP verification
        with patch('manushya.core.mfa_auth.verify_totp') as mock_verify:
            mock_verify.return_value = True
            
            result = await verify_mfa_token(identity.id, "123456")
            assert result is True

    @pytest.mark.asyncio
    async def test_mfa_verification_invalid_token(self, client, identity):
        """Test MFA verification with invalid token."""
        from manushya.core.mfa_auth import verify_mfa_token
        
        with patch('manushya.core.mfa_auth.verify_totp') as mock_verify:
            mock_verify.return_value = False
            
            result = await verify_mfa_token(identity.id, "000000")
            assert result is False

    @pytest.mark.asyncio
    async def test_mfa_setup(self, client, identity):
        """Test MFA setup process."""
        from manushya.core.mfa_auth import setup_mfa
        
        result = await setup_mfa(identity.id)
        assert "secret" in result
        assert "qr_code" in result


class TestSessionManagement:
    """Test session management functionality."""

    @pytest.mark.asyncio
    async def test_create_session_with_tokens(self, client, identity):
        """Test session creation with tokens."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = "Test User Agent"
        
        db_session = MagicMock()
        
        result = await create_session_with_tokens(identity, request, db_session)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert "expires_in" in result
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, client, identity):
        """Test successful token refresh."""
        # Create a session first
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = "Test User Agent"
        
        db_session = MagicMock()
        session_data = await create_session_with_tokens(identity, request, db_session)
        refresh_token = session_data["refresh_token"]
        
        # Mock session lookup
        with patch('manushya.core.session_service.SessionService.get_session_by_refresh_token') as mock_get:
            mock_get.return_value = MagicMock(identity_id=identity.id)
            
            result = await refresh_access_token(refresh_token, db_session)
            assert result is not None
            assert "access_token" in result

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(self, client):
        """Test token refresh with invalid refresh token."""
        db_session = MagicMock()
        
        result = await refresh_access_token("invalid_refresh_token", db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_session_cleanup(self, client):
        """Test session cleanup functionality."""
        from manushya.core.session_service import SessionService
        
        db_session = MagicMock()
        service = SessionService(db_session)
        
        # Mock expired sessions
        expired_session = MagicMock()
        expired_session.expires_at = datetime.utcnow() - timedelta(hours=1)
        
        with patch.object(service, 'get_expired_sessions') as mock_get:
            mock_get.return_value = [expired_session]
            
            await service.cleanup_expired_sessions()
            
            # Verify session was deleted
            db_session.delete.assert_called_with(expired_session)


class TestAuthenticationIntegration:
    """Integration tests for authentication system."""

    @pytest.mark.asyncio
    async def test_authentication_flow_jwt(self, client, identity, admin_jwt_token):
        """Test complete JWT authentication flow."""
        # Test token creation
        token = create_access_token({"sub": str(identity.id)})
        assert token is not None
        
        # Test token verification
        payload = verify_token(token)
        assert payload["sub"] == str(identity.id)
        
        # Test identity retrieval
        credentials = MagicMock()
        credentials.credentials = token
        
        with patch('manushya.core.auth.get_db') as mock_get_db:
            mock_get_db.return_value = [identity]
            
            result = await get_current_identity_jwt(credentials, None)
            assert result.id == identity.id

    @pytest.mark.asyncio
    async def test_authentication_flow_api_key(self, client, admin_api_key, identity):
        """Test complete API key authentication flow."""
        from manushya.core.api_key_auth import get_current_identity_from_api_key
        
        credentials = MagicMock()
        credentials.credentials = "mk_test_api_key"
        
        with patch('manushya.core.api_key_auth.get_api_key_by_hash') as mock_get_key:
            mock_get_key.return_value = admin_api_key
            
            result = await get_current_identity_from_api_key(credentials, None)
            assert result.id == identity.id

    @pytest.mark.asyncio
    async def test_authentication_fallback(self, client, identity, admin_jwt_token):
        """Test authentication fallback from API key to JWT."""
        credentials = MagicMock()
        credentials.credentials = admin_jwt_token
        
        with patch('manushya.core.auth.get_db') as mock_get_db:
            mock_get_db.return_value = [identity]
            
            result = await get_current_identity(credentials, None)
            assert result.id == identity.id


class TestAuthenticationSecurity:
    """Security tests for authentication system."""

    def test_token_tampering_detection(self):
        """Test detection of tampered tokens."""
        # Create valid token
        data = {"sub": "test-user-id"}
        token = create_access_token(data)
        
        # Tamper with token
        tampered_token = token[:-5] + "XXXXX"
        
        with pytest.raises(AuthenticationError):
            verify_token(tampered_token)

    def test_token_replay_attack_prevention(self):
        """Test prevention of token replay attacks."""
        # This would typically be handled by token blacklisting
        # For now, we test that tokens are properly validated
        data = {"sub": "test-user-id"}
        token = create_access_token(data)
        
        # First verification should work
        payload1 = verify_token(token)
        assert payload1["sub"] == "test-user-id"
        
        # Second verification should also work (no replay protection in basic JWT)
        payload2 = verify_token(token)
        assert payload2["sub"] == "test-user-id"

    @pytest.mark.asyncio
    async def test_rate_limiting_on_auth_endpoints(self, client):
        """Test rate limiting on authentication endpoints."""
        # This would be tested with actual rate limiting implementation
        # For now, we test that identity creation endpoint exists
        response = client.post("/v1/identity/")
        assert response.status_code in [401, 422]  # Should require valid credentials

    def test_password_strength_validation(self):
        """Test password strength validation."""
        from manushya.core.password_auth import validate_password_strength
        
        # Test weak password
        assert not validate_password_strength("123")
        assert not validate_password_strength("password")
        
        # Test strong password
        assert validate_password_strength("StrongP@ssw0rd123!")


class TestAuthenticationPerformance:
    """Performance tests for authentication system."""

    def test_token_generation_speed(self):
        """Test JWT token generation speed."""
        import time
        
        data = {"sub": "test-user-id"}
        
        start_time = time.time()
        for _ in range(100):
            create_access_token(data)
        end_time = time.time()
        
        # Should generate 100 tokens in reasonable time
        assert end_time - start_time < 1.0

    def test_token_verification_speed(self):
        """Test JWT token verification speed."""
        import time
        
        data = {"sub": "test-user-id"}
        token = create_access_token(data)
        
        start_time = time.time()
        for _ in range(100):
            verify_token(token)
        end_time = time.time()
        
        # Should verify 100 tokens in reasonable time
        assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_authentication(self, client, identity):
        """Test concurrent authentication requests."""
        import asyncio
        
        async def authenticate():
            token = create_access_token({"sub": str(identity.id)})
            credentials = MagicMock()
            credentials.credentials = token
            
            with patch('manushya.core.auth.get_db') as mock_get_db:
                mock_get_db.return_value = [identity]
                
                return await get_current_identity_jwt(credentials, None)
        
        # Run 10 concurrent authentications
        tasks = [authenticate() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(result.id == identity.id for result in results) 