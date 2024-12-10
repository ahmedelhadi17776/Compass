"""Security utilities for password hashing, verification, and token management."""
from passlib.context import CryptContext
import secrets
import string
import re
import ipaddress
import hashlib
import base64
from typing import Optional, Tuple, Union

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against
        
    Returns:
        bool: True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def generate_secure_token(length: int = 32, url_safe: bool = False) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token to generate
        url_safe: If True, generate a URL-safe token
        
    Returns:
        str: Secure random token
    """
    if url_safe:
        return secrets.token_urlsafe(length)
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength against comprehensive security requirements.
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check minimum length
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    # Check for complexity
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common patterns
    common_patterns = [
        'password', '123456', 'qwerty', 'admin', 'letmein'
    ]
    if any(pattern in password.lower() for pattern in common_patterns):
        return False, "Password is too common or predictable"
    
    return True, "Password is strong"

def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """
    Securely hash sensitive data with optional salt.
    
    Args:
        data: Data to hash
        salt: Optional salt for additional security
    
    Returns:
        str: Hashed data
    """
    if salt is None:
        salt = generate_secure_token(16)
    
    # Use SHA-256 for hashing
    salted_data = f"{salt}{data}"
    return hashlib.sha256(salted_data.encode()).hexdigest()

def validate_ip_address(ip: str) -> bool:
    """
    Validate if a given string is a valid IP address.
    
    Args:
        ip: IP address to validate
    
    Returns:
        bool: True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def mask_sensitive_data(data: Union[str, None], mask_char: str = '*', 
                        visible_chars: int = 4) -> Optional[str]:
    """
    Mask sensitive data while keeping a few characters visible.
    
    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible at the end
    
    Returns:
        Masked data or None
    """
    if not data:
        return None
    
    if len(data) <= visible_chars:
        return data
    
    return f"{mask_char * (len(data) - visible_chars)}{data[-visible_chars:]}"

def generate_jwt_secret(length: int = 64) -> str:
    """
    Generate a secure secret for JWT token signing.
    
    Args:
        length: Length of the secret
    
    Returns:
        str: Base64 encoded secret
    """
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8')

def is_safe_redirect_url(url: str, allowed_domains: Optional[list[str]] = None) -> bool:
    """
    Check if a redirect URL is safe and within allowed domains.
    
    Args:
        url: URL to validate
        allowed_domains: Optional list of allowed domains
    
    Returns:
        bool: True if URL is safe, False otherwise
    """
    try:
        from urllib.parse import urlparse
        
        parsed_url = urlparse(url)
        
        # Basic URL validation
        if not parsed_url.scheme or not parsed_url.netloc:
            return False
        
        # Check against allowed domains if provided
        if allowed_domains:
            return parsed_url.netloc in allowed_domains
        
        return True
    except Exception:
        return False
