"""
Authentication utilities for password encryption/decryption.
"""

import os
from cryptography.fernet import Fernet
import base64


def get_encryption_key():
    """Get or generate encryption key."""
    key_str = os.getenv("ENCRYPTION_KEY")
    
    if not key_str:
        # Generate a new key if not provided
        key = Fernet.generate_key()
        key_str = key.decode()
        print(f"⚠️  No ENCRYPTION_KEY set. Generated new key: {key_str}")
        print("   Add this to your .env file for production use")
    
    return key_str.encode() if isinstance(key_str, str) else key_str


def encrypt_password(password: str) -> str:
    """
    Encrypt a password using Fernet.
    
    Args:
        password: Plain text password
        
    Returns:
        Encrypted password (base64 encoded)
    """
    try:
        key = get_encryption_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(password.encode())
        return encrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to encrypt password: {str(e)}")


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt an encrypted password.
    
    Args:
        encrypted_password: Encrypted password (base64 encoded)
        
    Returns:
        Plain text password
    """
    try:
        key = get_encryption_key()
        cipher = Fernet(key)
        decrypted = cipher.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt password: {str(e)}")


def verify_password(plain_password: str, encrypted_password: str) -> bool:
    """
    Verify a plain password against encrypted password.
    
    Args:
        plain_password: Plain text password to verify
        encrypted_password: Encrypted password from database
        
    Returns:
        True if passwords match, False otherwise
    """
    try:
        decrypted = decrypt_password(encrypted_password)
        return plain_password == decrypted
    except Exception:
        return False
