"""Encryption service module."""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import secrets
from .utils import generate_secure_token
from src.core.config import settings


class EncryptionService:
    """Service for handling data encryption and decryption."""

    def __init__(self, key: Optional[bytes] = None):
        """Initialize with optional key or generate a new one."""
        self.key = settings.ENCRYPTION_KEY.encode()
        self.fernet = Fernet(self.key or Fernet.generate_key())

    @classmethod
    def from_password(cls, password: str, salt: Optional[bytes] = None):
        """Create an instance using a password and optional salt."""
        salt = salt or secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return cls(key)

    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted string data."""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def rotate_key(self) -> None:
        """Generate a new encryption key."""
        new_key = Fernet.generate_key()
        self.fernet = Fernet(new_key)
        self._key = new_key

    @property
    def key(self) -> bytes:
        """Get the current encryption key."""
        return self._key
