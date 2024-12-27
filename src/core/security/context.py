"""Security context module."""
from dataclasses import dataclass
from typing import Optional

from .auth import TokenManager
from .encryption import EncryptionService


@dataclass
class SecurityContext:
    """Security context for request handling."""
    user_id: Optional[int]
    client_ip: str
    path: str
    method: str
    user_agent: Optional[str] = None
    token_manager: Optional[TokenManager] = None
    encryption_service: Optional[EncryptionService] = None

    @classmethod
    def create(
        cls,
        token_manager: TokenManager,
        encryption_service: EncryptionService,
        client_ip: str,
        path: str,
        method: str
    ) -> "SecurityContext":
        """Create a new security context."""
        return cls(
            user_id=None,
            client_ip=client_ip,
            path=path,
            method=method,
            token_manager=token_manager,
            encryption_service=encryption_service
        )
