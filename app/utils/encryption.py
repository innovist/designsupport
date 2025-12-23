"""
Encryption utilities for Fashion AI Generator
Handles AES encryption/decryption of sensitive data
"""

import base64
import os
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """Manages encryption and decryption of sensitive data"""

    def __init__(self, password: str = None):
        """Initialize encryption manager

        Args:
            password: Password for key derivation. If None, uses environment variable
        """
        self.password = password or os.getenv('ENCRYPTION_PASSWORD', 'fashion-ai-default-key')
        self.salt = os.getenv('ENCRYPTION_SALT', 'fashion-ai-salt').encode()
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)

    def _derive_key(self) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return key

    def encrypt(self, data: str) -> str:
        """Encrypt string data

        Args:
            data: String to encrypt

        Returns:
            Base64 encoded encrypted string
        """
        if not isinstance(data, str):
            data = str(data)

        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted string

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt dictionary data

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64 encoded encrypted string
        """
        import json
        json_str = json.dumps(data, separators=(',', ':'))
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt to dictionary

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted dictionary
        """
        import json
        decrypted_str = self.decrypt(encrypted_data)
        return json.loads(decrypted_str)

    @staticmethod
    def generate_secure_key() -> str:
        """Generate a secure random key

        Returns:
            Base64 encoded secure key
        """
        return base64.urlsafe_b64encode(os.urandom(32)).decode()

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for verification without storing the actual key

        Args:
            api_key: API key to hash

        Returns:
            SHA-256 hash of the API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """Verify API key against stored hash

        Args:
            api_key: API key to verify
            stored_hash: Stored hash to compare against

        Returns:
            True if API key matches the hash
        """
        return self.hash_api_key(api_key) == stored_hash


# Global encryption manager instance
encryption_manager = EncryptionManager()


# Convenience functions
def encrypt_data(data: str) -> str:
    """Encrypt data using global encryption manager"""
    return encryption_manager.encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using global encryption manager"""
    return encryption_manager.decrypt(encrypted_data)


def encrypt_api_keys(api_keys: dict) -> str:
    """Encrypt API keys dictionary"""
    return encryption_manager.encrypt_dict(api_keys)


def decrypt_api_keys(encrypted_keys: str) -> dict:
    """Decrypt API keys dictionary"""
    return encryption_manager.decrypt_dict(encrypted_keys)


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage"""
    return encryption_manager.hash_api_key(api_key)