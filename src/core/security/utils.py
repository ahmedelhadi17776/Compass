"""Security utility functions."""
import secrets
import string
import re
import ipaddress
import hashlib
import base64
from typing import Optional, Union
from urllib.parse import urlparse


def generate_secure_token(length: int = 32, url_safe: bool = False) -> str:
    """Generate a cryptographically secure random token."""
    if url_safe:
        return secrets.token_urlsafe(length)
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """Securely hash sensitive data with optional salt."""
    if salt is None:
        salt = generate_secure_token(16)
    salted_data = f"{salt}{data}"
    return hashlib.sha256(salted_data.encode()).hexdigest()


def mask_sensitive_data(data: Union[str, None], mask_char: str = '*',
                        visible_chars: int = 4) -> Optional[str]:
    """Mask sensitive data while keeping a few characters visible."""
    if not data:
        return None
    if len(data) <= visible_chars:
        return data
    return f"{mask_char * (len(data) - visible_chars)}{data[-visible_chars:]}"


def is_safe_redirect_url(url: str, allowed_domains: Optional[list[str]] = None) -> bool:
    """Check if a redirect URL is safe and within allowed domains."""
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False
        return parsed_url.netloc in (allowed_domains or [])
    except Exception:
        return False
