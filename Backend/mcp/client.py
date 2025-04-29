# Backend/mcp_integration/client.py

from typing import Optional, Dict, Any
from Backend.core.config import settings
import aiohttp
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.GO_BACKEND_URL
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def call_method(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a method on the MCP server asynchronously."""
        session = await self._get_session()
        url = urljoin(self.base_url, method)

        try:
            async with session.post(url, json=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error calling MCP method {method}: {str(e)}")
            raise

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information from the Go backend."""
        return await self.call_method("user/info", {"user_id": user_id})

    async def get_user_context(self, user_id: str, domain: str) -> Dict[str, Any]:
        """Get user context for a specific domain from the Go backend."""
        return await self.call_method("user/context", {
            "user_id": user_id,
            "domain": domain
        })

    async def create_entity(self, entity_type: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create an entity through the Go backend."""
        return await self.call_method(f"{entity_type}/create", {
            "user_id": user_id,
            "data": data
        })

    async def update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an entity through the Go backend."""
        return await self.call_method(f"{entity_type}/update", {
            "user_id": user_id,
            "entity_id": entity_id,
            "data": data
        })

    async def delete_entity(self, entity_type: str, entity_id: str, user_id: str) -> Dict[str, Any]:
        """Delete an entity through the Go backend."""
        return await self.call_method(f"{entity_type}/delete", {
            "user_id": user_id,
            "entity_id": entity_id
        })
