"""Encryption utilities for sensitive data."""

import os
from typing import Optional
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manage encryption/decryption of sensitive data."""
    
    def __init__(self):
        """Initialize encryption manager."""
        # Try to get key from environment, generate if not found
        key_str = os.getenv('ENCRYPTION_KEY')
        
        if not key_str:
            # Generate new key in production - this should be stored securely
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
            logger.warning("No ENCRYPTION_KEY found in .env. Generated new key. Store it securely!")
        else:
            try:
                self.cipher = Fernet(key_str.encode() if isinstance(key_str, str) else key_str)
            except Exception as e:
                logger.error(f"Invalid encryption key: {e}")
                # Fallback: generate new key
                key = Fernet.generate_key()
                self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext.
        
        Args:
            plaintext: Text to encrypt
            
        Returns:
            Encrypted text
        """
        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext.
        
        Args:
            ciphertext: Encrypted text
            
        Returns:
            Decrypted plaintext
        """
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise


# Global instance
encryption_manager = EncryptionManager()


def encrypt_token(token: str) -> str:
    """Encrypt API token."""
    return encryption_manager.encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt API token."""
    return encryption_manager.decrypt(encrypted_token)
