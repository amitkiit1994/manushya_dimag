"""
Field-level encryption utilities for Manushya.ai
"""

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from manushya.config import settings
from manushya.core.exceptions import EncryptionError


def _get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    try:
        # Use the encryption key directly if it's already 32 bytes
        key = settings.encryption_key.encode()
        if len(key) != 32:
            # Derive key using PBKDF2 if not exactly 32 bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"manushya_salt",  # In production, use a random salt per encryption
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key))

        return Fernet(key)
    except Exception as e:
        raise EncryptionError(f"Failed to initialize encryption: {str(e)}") from e


def encrypt_field(value: str) -> str:
    """Encrypt a field value."""
    if not value:
        return value

    try:
        fernet = _get_fernet()
        encrypted_data = fernet.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt field: {str(e)}") from e


def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a field value."""
    if not encrypted_value:
        return encrypted_value

    try:
        fernet = _get_fernet()
        encrypted_data = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode()
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt field: {str(e)}") from e


def encrypt_dict(data: dict, fields_to_encrypt: list) -> dict:
    """Encrypt specific fields in a dictionary."""
    encrypted_data = data.copy()

    for field in fields_to_encrypt:
        if field in encrypted_data and encrypted_data[field]:
            encrypted_data[field] = encrypt_field(str(encrypted_data[field]))

    return encrypted_data


def decrypt_dict(data: dict, fields_to_decrypt: list) -> dict:
    """Decrypt specific fields in a dictionary."""
    decrypted_data = data.copy()

    for field in fields_to_decrypt:
        if field in decrypted_data and decrypted_data[field]:
            try:
                decrypted_data[field] = decrypt_field(str(decrypted_data[field]))
            except EncryptionError:
                # If decryption fails, keep the original value
                pass

    return decrypted_data
