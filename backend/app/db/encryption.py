"""Encryption utilities for sensitive data."""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import get_settings

settings = get_settings()


def _get_fernet() -> Fernet:
    """Get Fernet cipher instance.
    
    Returns:
        Fernet: Cipher instance
    """
    # Derive key from secret key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'sre-agent-salt',  # In production, use a random salt stored securely
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.secret_key.encode()))
    return Fernet(key)


def encrypt_credentials(data: dict) -> str:
    """Encrypt credentials dictionary.
    
    Args:
        data: Credentials dictionary
        
    Returns:
        str: Encrypted string
    """
    import json
    fernet = _get_fernet()
    json_str = json.dumps(data)
    encrypted = fernet.encrypt(json_str.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_credentials(encrypted_str: str) -> dict:
    """Decrypt credentials string.
    
    Args:
        encrypted_str: Encrypted string
        
    Returns:
        dict: Decrypted credentials dictionary
    """
    import json
    fernet = _get_fernet()
    encrypted = base64.urlsafe_b64decode(encrypted_str.encode())
    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted.decode())
