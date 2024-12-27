"""Core authentication security module."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import secrets
import logging
from fastapi import HTTPException, status

from src.core.config import settings
from src.core.security.exceptions import InvalidTokenError, ExpiredTokenError

logger = logging.getLogger(__name__)


class TokenManager:
    """Token management service."""

    def __init__(self):
        self.token_blacklist = set()

    def create_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
        token_type: str = "access"
    ) -> str:
        """Create a JWT token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            if token_type == "access":
                expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            else:
                expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({
            "exp": expire,
            "type": token_type,
            "jti": secrets.token_hex(16)
        })

        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    def verify_token(self, token: str, verify_exp: bool = True) -> Optional[dict]:
        """Verify a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": verify_exp}
            )

            if payload.get("jti") in self.token_blacklist:
                raise InvalidTokenError()

            return payload
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError()
        except jwt.JWTError:
            raise InvalidTokenError()

    def blacklist_token(self, token: str) -> bool:
        """Blacklist a token using its JTI claim."""
        try:
            payload = self.verify_token(token, verify_exp=False)
            if payload and "jti" in payload:
                self.token_blacklist.add(payload["jti"])
                return True
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")
        return False
