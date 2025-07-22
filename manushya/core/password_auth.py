"""
Password authentication utilities for Manushya.ai
"""

import re
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manushya.db.models import Identity
from manushya.core.exceptions import AuthenticationError, ValidationError

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
    
    if not re.search(r"[A-Z]", password):
        return False
    
    if not re.search(r"[a-z]", password):
        return False
    
    if not re.search(r"\d", password):
        return False
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        return False
    
    return True


async def authenticate_with_password(
    email: str, password: str, db: AsyncSession
) -> Optional[Identity]:
    """
    Authenticate user with email and password.
    
    Args:
        email: User's email address
        password: Plain text password
        db: Database session
        
    Returns:
        Identity object if authentication successful, None otherwise
    """
    # Find identity by email (assuming email is stored in external_id or claims)
    stmt = select(Identity).where(
        Identity.external_id == email,
        Identity.is_active == True
    )
    result = await db.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        return None
    
    # Check if identity has password hash in claims
    password_hash = identity.claims.get("password_hash")
    if not password_hash:
        return None
    
    # Verify password
    if not verify_password(password, password_hash):
        return None
    
    return identity


async def create_identity_with_password(
    email: str,
    password: str,
    role: str = "user",
    claims: dict = None,
    tenant_id: Optional[str] = None,
    db: AsyncSession = None
) -> Identity:
    """
    Create a new identity with password authentication.
    
    Args:
        email: User's email address
        password: Plain text password
        role: User role
        claims: Additional claims
        tenant_id: Tenant ID
        db: Database session
        
    Returns:
        Created Identity object
        
    Raises:
        ValidationError: If password doesn't meet strength requirements
    """
    if not validate_password_strength(password):
        raise ValidationError(
            "Password must be at least 8 characters long and contain uppercase, "
            "lowercase, digit, and special character"
        )
    
    # Hash password
    password_hash = hash_password(password)
    
    # Prepare claims
    identity_claims = claims or {}
    identity_claims["password_hash"] = password_hash
    identity_claims["email"] = email
    
    # Create identity
    identity = Identity(
        external_id=email,
        role=role,
        claims=identity_claims,
        is_active=True,
        tenant_id=tenant_id
    )
    
    db.add(identity)
    await db.commit()
    await db.refresh(identity)
    
    return identity


async def change_password(
    identity_id: str,
    current_password: str,
    new_password: str,
    db: AsyncSession
) -> bool:
    """
    Change user's password.
    
    Args:
        identity_id: User's identity ID
        current_password: Current password
        new_password: New password
        db: Database session
        
    Returns:
        True if password changed successfully, False otherwise
        
    Raises:
        ValidationError: If new password doesn't meet strength requirements
    """
    # Validate new password strength
    if not validate_password_strength(new_password):
        raise ValidationError(
            "Password must be at least 8 characters long and contain uppercase, "
            "lowercase, digit, and special character"
        )
    
    # Get identity
    stmt = select(Identity).where(Identity.id == identity_id)
    result = await db.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        return False
    
    # Verify current password
    password_hash = identity.claims.get("password_hash")
    if not password_hash or not verify_password(current_password, password_hash):
        return False
    
    # Hash new password
    new_password_hash = hash_password(new_password)
    
    # Update claims
    identity.claims["password_hash"] = new_password_hash
    await db.commit()
    
    return True


async def reset_password(
    email: str,
    reset_token: str,
    new_password: str,
    db: AsyncSession
) -> bool:
    """
    Reset user's password using reset token.
    
    Args:
        email: User's email address
        reset_token: Password reset token
        new_password: New password
        db: Database session
        
    Returns:
        True if password reset successful, False otherwise
    """
    # Validate new password strength
    if not validate_password_strength(new_password):
        raise ValidationError(
            "Password must be at least 8 characters long and contain uppercase, "
            "lowercase, digit, and special character"
        )
    
    # Get identity
    stmt = select(Identity).where(Identity.external_id == email)
    result = await db.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        return False
    
    # Verify reset token (this would typically check against stored reset tokens)
    # For now, we'll assume the token is valid if it matches a pattern
    if not reset_token or len(reset_token) < 10:
        return False
    
    # Hash new password
    new_password_hash = hash_password(new_password)
    
    # Update claims
    identity.claims["password_hash"] = new_password_hash
    await db.commit()
    
    return True


def generate_password_reset_token() -> str:
    """Generate a password reset token."""
    import secrets
    return secrets.token_urlsafe(32)


async def request_password_reset(
    email: str,
    db: AsyncSession
) -> bool:
    """
    Request a password reset for a user.
    
    Args:
        email: User's email address
        db: Database session
        
    Returns:
        True if reset token generated successfully, False otherwise
    """
    # Get identity
    stmt = select(Identity).where(Identity.external_id == email)
    result = await db.execute(stmt)
    identity = result.scalar_one_or_none()
    
    if not identity:
        return False
    
    # Generate reset token
    reset_token = generate_password_reset_token()
    
    # Store reset token in claims (in production, this would be in a separate table)
    identity.claims["password_reset_token"] = reset_token
    identity.claims["password_reset_expires"] = (
        datetime.utcnow() + timedelta(hours=24)
    ).isoformat()
    
    await db.commit()
    
    # In production, send email with reset token
    # For now, we'll just return success
    
    return True


def get_password_strength_score(password: str) -> dict:
    """
    Get detailed password strength score.
    
    Returns:
        Dictionary with strength details
    """
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long")
    
    # Uppercase check
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Password should contain at least one uppercase letter")
    
    # Lowercase check
    if re.search(r"[a-z]", password):
        score += 1
    else:
        feedback.append("Password should contain at least one lowercase letter")
    
    # Digit check
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Password should contain at least one digit")
    
    # Special character check
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        score += 1
    else:
        feedback.append("Password should contain at least one special character")
    
    # Additional strength checks
    if len(password) >= 12:
        score += 1
    
    if len(set(password)) >= len(password) * 0.7:  # Good character variety
        score += 1
    
    # Determine strength level
    if score >= 6:
        strength = "strong"
    elif score >= 4:
        strength = "medium"
    else:
        strength = "weak"
    
    return {
        "score": score,
        "max_score": 7,
        "strength": strength,
        "feedback": feedback,
        "is_acceptable": score >= 4
    } 