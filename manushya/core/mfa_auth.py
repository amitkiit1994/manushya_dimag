"""
Multi-factor authentication utilities for Manushya.ai
"""

import base64
import secrets
from typing import Optional, List
from datetime import datetime, timedelta
import pyotp
import qrcode
from io import BytesIO

from manushya.db.models import Identity
from manushya.core.exceptions import AuthenticationError, ValidationError


def generate_mfa_secret() -> str:
    """Generate a new MFA secret."""
    return pyotp.random_base32()


def generate_mfa_qr_code(secret: str, email: str, issuer: str = "Manushya.ai") -> str:
    """
    Generate QR code for MFA setup.
    
    Args:
        secret: MFA secret
        email: User's email
        issuer: Service name
        
    Returns:
        Base64 encoded QR code image
    """
    # Create TOTP URI
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=issuer
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def verify_totp(secret: str, token: str, window: int = 1) -> bool:
    """
    Verify a TOTP token.
    
    Args:
        secret: MFA secret
        token: Token to verify
        window: Time window for verification
        
    Returns:
        True if token is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=window)


def generate_backup_codes(count: int = 10) -> List[str]:
    """
    Generate backup codes for MFA.
    
    Args:
        count: Number of backup codes to generate
        
    Returns:
        List of backup codes
    """
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        codes.append(code)
    return codes


async def setup_mfa(identity_id: str, db_session) -> dict:
    """
    Set up MFA for an identity.
    
    Args:
        identity_id: Identity ID
        db_session: Database session
        
    Returns:
        Dictionary with MFA setup information
    """
    from sqlalchemy import select
    
    # Get identity
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db_session.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        raise ValidationError("Identity not found")
    
    # Generate MFA secret
    secret = generate_mfa_secret()
    
    # Generate QR code
    qr_code = generate_mfa_qr_code(secret, identity.external_id)
    
    # Generate backup codes
    backup_codes = generate_backup_codes()
    
    # Store MFA info in claims (in production, this would be in a separate table)
    identity.claims["mfa_secret"] = secret
    identity.claims["mfa_enabled"] = False  # Will be enabled after verification
    identity.claims["mfa_backup_codes"] = backup_codes
    identity.claims["mfa_setup_time"] = datetime.utcnow().isoformat()
    
    await db_session.commit()
    
    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes,
        "setup_url": f"otpauth://totp/Manushya.ai:{identity.external_id}?secret={secret}&issuer=Manushya.ai"
    }


async def verify_mfa_token(identity_id: str, token: str, db_session) -> bool:
    """
    Verify MFA token for an identity.
    
    Args:
        identity_id: Identity ID
        token: MFA token to verify
        db_session: Database session
        
    Returns:
        True if token is valid, False otherwise
    """
    from sqlalchemy import select
    
    # Get identity
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db_session.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        return False
    
    # Check if MFA is enabled
    if not identity.claims.get("mfa_enabled", False):
        return False
    
    # Get MFA secret
    secret = identity.claims.get("mfa_secret")
    if not secret:
        return False
    
    # Verify TOTP token
    if verify_totp(secret, token):
        return True
    
    # Check backup codes
    backup_codes = identity.claims.get("mfa_backup_codes", [])
    if token in backup_codes:
        # Remove used backup code
        backup_codes.remove(token)
        identity.claims["mfa_backup_codes"] = backup_codes
        await db_session.commit()
        return True
    
    return False


async def enable_mfa(identity_id: str, token: str, db_session) -> bool:
    """
    Enable MFA for an identity after verification.
    
    Args:
        identity_id: Identity ID
        token: Verification token
        db_session: Database session
        
    Returns:
        True if MFA enabled successfully, False otherwise
    """
    from sqlalchemy import select
    
    # Get identity
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db_session.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        return False
    
    # Get MFA secret
    secret = identity.claims.get("mfa_secret")
    if not secret:
        return False
    
    # Verify token
    if not verify_totp(secret, token):
        return False
    
    # Enable MFA
    identity.claims["mfa_enabled"] = True
    identity.claims["mfa_enabled_time"] = datetime.utcnow().isoformat()
    
    await db_session.commit()
    
    return True


async def disable_mfa(identity_id: str, token: str, db_session) -> bool:
    """
    Disable MFA for an identity.
    
    Args:
        identity_id: Identity ID
        token: Verification token
        db_session: Database session
        
    Returns:
        True if MFA disabled successfully, False otherwise
    """
    from sqlalchemy import select
    
    # Get identity
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db_session.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        return False
    
    # Verify token (can use backup code or TOTP)
    if not await verify_mfa_token(identity_id, token, db_session):
        return False
    
    # Disable MFA
    identity.claims["mfa_enabled"] = False
    identity.claims["mfa_disabled_time"] = datetime.utcnow().isoformat()
    
    await db_session.commit()
    
    return True


async def regenerate_backup_codes(identity_id: str, token: str, db_session) -> List[str]:
    """
    Regenerate backup codes for an identity.
    
    Args:
        identity_id: Identity ID
        token: Verification token
        db_session: Database session
        
    Returns:
        New backup codes
    """
    from sqlalchemy import select
    
    # Get identity
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db_session.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        raise ValidationError("Identity not found")
    
    # Verify token
    if not await verify_mfa_token(identity_id, token, db_session):
        raise AuthenticationError("Invalid verification token")
    
    # Generate new backup codes
    new_backup_codes = generate_backup_codes()
    
    # Update claims
    identity.claims["mfa_backup_codes"] = new_backup_codes
    identity.claims["mfa_backup_codes_regenerated"] = datetime.utcnow().isoformat()
    
    await db_session.commit()
    
    return new_backup_codes


def get_mfa_status(identity: Identity) -> dict:
    """
    Get MFA status for an identity.
    
    Args:
        identity: Identity object
        
    Returns:
        Dictionary with MFA status information
    """
    claims = identity.claims or {}
    
    return {
        "enabled": claims.get("mfa_enabled", False),
        "setup_time": claims.get("mfa_setup_time"),
        "enabled_time": claims.get("mfa_enabled_time"),
        "backup_codes_remaining": len(claims.get("mfa_backup_codes", [])),
        "backup_codes_regenerated": claims.get("mfa_backup_codes_regenerated")
    }


async def require_mfa_verification(identity: Identity, db_session) -> bool:
    """
    Check if MFA verification is required for an identity.
    
    Args:
        identity: Identity object
        db_session: Database session
        
    Returns:
        True if MFA verification is required, False otherwise
    """
    # Check if MFA is enabled
    if not identity.claims.get("mfa_enabled", False):
        return False
    
    # In production, you might have additional logic here
    # For example, checking if the user is logging in from a new device
    # or if it's been a certain amount of time since last verification
    
    return True


class MFARateLimiter:
    """Rate limiter for MFA attempts."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_attempts = 5
        self.window_seconds = 300  # 5 minutes
    
    async def check_rate_limit(self, identity_id: str) -> bool:
        """
        Check if MFA attempts are within rate limit.
        
        Args:
            identity_id: Identity ID
            
        Returns:
            True if within rate limit, False otherwise
        """
        key = f"mfa_attempts:{identity_id}"
        
        # Get current attempts
        attempts = await self.redis.get(key)
        if attempts is None:
            attempts = 0
        else:
            attempts = int(attempts)
        
        # Check if limit exceeded
        if attempts >= self.max_attempts:
            return False
        
        return True
    
    async def record_attempt(self, identity_id: str, success: bool):
        """
        Record an MFA attempt.
        
        Args:
            identity_id: Identity ID
            success: Whether the attempt was successful
        """
        key = f"mfa_attempts:{identity_id}"
        
        if success:
            # Reset attempts on successful verification
            await self.redis.delete(key)
        else:
            # Increment failed attempts
            await self.redis.incr(key)
            await self.redis.expire(key, self.window_seconds)
    
    async def get_remaining_attempts(self, identity_id: str) -> int:
        """
        Get remaining MFA attempts for an identity.
        
        Args:
            identity_id: Identity ID
            
        Returns:
            Number of remaining attempts
        """
        key = f"mfa_attempts:{identity_id}"
        
        attempts = await self.redis.get(key)
        if attempts is None:
            return self.max_attempts
        
        attempts = int(attempts)
        return max(0, self.max_attempts - attempts) 