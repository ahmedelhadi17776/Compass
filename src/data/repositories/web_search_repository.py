"""Web search repository module."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.web_search import WebSearch
from core.exceptions import SearchNotFoundError

class WebSearchRepository:
    """Web search repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize web search repository."""
        self._session = session

    async def create_search(self, search_data: dict) -> WebSearch:
        """Create a new web search entry."""
        search = WebSearch(
            user_id=search_data["user_id"],
            query=search_data["query"],
            search_type=search_data.get("search_type", "general"),
            parameters=search_data.get("parameters"),
            results=search_data.get("results"),
            status=search_data.get("status", "pending"),
            timestamp=datetime.utcnow()
        )
        self._session.add(search)
        await self._session.commit()
        await self._session.refresh(search)
        return search

    async def get_search(self, search_id: int) -> WebSearch:
        """Get a specific search entry."""
        search = await self._session.execute(
            select(WebSearch).where(WebSearch.id == search_id)
        )
        search = search.scalar_one_or_none()
        if not search:
            raise SearchNotFoundError(f"Search with id {search_id} not found")
        return search

    async def get_user_searches(
        self,
        user_id: int,
        search_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[WebSearch]:
        """Get searches for a specific user."""
        query = select(WebSearch).where(WebSearch.user_id == user_id)
        
        if search_type:
            query = query.where(WebSearch.search_type == search_type)
        if status:
            query = query.where(WebSearch.status == status)
            
        query = query.order_by(desc(WebSearch.timestamp)).limit(limit)
        searches = await self._session.execute(query)
        return searches.scalars().all()

    async def update_search_results(
        self, search_id: int, results: dict, status: str = "completed"
    ) -> WebSearch:
        """Update search results."""
        search = await self.get_search(search_id)
        search.results = results
        search.status = status
        search.completed_at = datetime.utcnow()
        await self._session.commit()
        await self._session.refresh(search)
        return search

    async def get_recent_searches(
        self, user_id: int, limit: int = 10
    ) -> List[WebSearch]:
        """Get recent searches for a user."""
        query = select(WebSearch).where(
            WebSearch.user_id == user_id,
            WebSearch.status == "completed"
        ).order_by(desc(WebSearch.timestamp)).limit(limit)
        searches = await self._session.execute(query)
        return searches.scalars().all()

    async def get_similar_searches(
        self, query: str, limit: int = 5
    ) -> List[WebSearch]:
        """Get similar previous searches."""
        # Note: This is a simple implementation. In production,
        # you might want to use full-text search or more sophisticated
        # similarity matching
        query = select(WebSearch).where(
            WebSearch.query.ilike(f"%{query}%"),
            WebSearch.status == "completed"
        ).order_by(desc(WebSearch.timestamp)).limit(limit)
        searches = await self._session.execute(query)
        return searches.scalars().all()

    async def create_task_related_search(
        self, user_id: int, task_id: int, query: str
    ) -> WebSearch:
        """Create a task-related search."""
        return await self.create_search({
            "user_id": user_id,
            "query": query,
            "search_type": "task_related",
            "parameters": {"task_id": task_id}
        })

    async def create_context_search(
        self, user_id: int, query: str, context: dict
    ) -> WebSearch:
        """Create a context-aware search."""
        return await self.create_search({
            "user_id": user_id,
            "query": query,
            "search_type": "context_aware",
            "parameters": {"context": context}
        })
