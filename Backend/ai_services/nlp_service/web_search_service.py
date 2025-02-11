"""Web search service module."""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...data.repositories.web_search_repository import WebSearchRepository
from ...data.database.models.web_search import WebSearch
from core.exceptions import SearchNotFoundError

class WebSearchService:
    """Web search service class."""

    def __init__(self, session: AsyncSession):
        """Initialize web search service."""
        self._repository = WebSearchRepository(session)

    async def create_search(
        self,
        user_id: int,
        query: str,
        search_type: str = "general",
        parameters: Optional[Dict] = None
    ) -> WebSearch:
        """Create a new web search entry."""
        # Validate search type
        valid_search_types = ["general", "task_related", "context_aware", "code", "documentation"]
        if search_type not in valid_search_types:
            raise ValueError(f"Invalid search type. Must be one of: {valid_search_types}")

        return await self._repository.create_search({
            "user_id": user_id,
            "query": query,
            "search_type": search_type,
            "parameters": parameters,
            "status": "pending"
        })

    async def get_search_results(
        self, search_id: int
    ) -> WebSearch:
        """Get search results."""
        return await self._repository.get_search(search_id)

    async def update_search_results(
        self,
        search_id: int,
        results: Dict,
        status: str = "completed"
    ) -> WebSearch:
        """Update search results."""
        valid_statuses = ["pending", "in_progress", "completed", "failed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        return await self._repository.update_search_results(
            search_id,
            results,
            status
        )

    async def get_user_search_history(
        self,
        user_id: int,
        search_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[WebSearch]:
        """Get search history for a user."""
        return await self._repository.get_user_searches(
            user_id,
            search_type,
            status,
            limit
        )

    async def get_recent_searches(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[WebSearch]:
        """Get recent searches for a user."""
        return await self._repository.get_recent_searches(user_id, limit)

    async def get_similar_searches(
        self,
        query: str,
        limit: int = 5
    ) -> List[WebSearch]:
        """Get similar previous searches."""
        return await self._repository.get_similar_searches(query, limit)

    async def create_task_related_search(
        self,
        user_id: int,
        task_id: int,
        query: str
    ) -> WebSearch:
        """Create a task-related search."""
        return await self._repository.create_task_related_search(
            user_id,
            task_id,
            query
        )

    async def create_context_search(
        self,
        user_id: int,
        query: str,
        context: Dict
    ) -> WebSearch:
        """Create a context-aware search."""
        return await self._repository.create_context_search(
            user_id,
            query,
            context
        )

    async def execute_search(
        self,
        search: WebSearch
    ) -> Dict:
        """Execute a web search."""
        try:
            # Update status to in_progress
            await self.update_search_results(
                search.id,
                {},
                "in_progress"
            )

            # Execute the search based on type
            results = await self._execute_search_query(search)

            # Update results
            await self.update_search_results(
                search.id,
                results,
                "completed"
            )

            return results
        except Exception as e:
            # Log the error and update status
            await self.update_search_results(
                search.id,
                {"error": str(e)},
                "failed"
            )
            raise

    async def _execute_search_query(self, search: WebSearch) -> Dict:
        """Execute the specific search query."""
        # This would contain the actual implementation for web searching
        # For now, we'll return a placeholder result
        return {
            "query": search.query,
            "timestamp": datetime.utcnow().isoformat(),
            "results": []
        }

    async def analyze_search_patterns(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict:
        """Analyze user's search patterns."""
        searches = await self.get_user_search_history(
            user_id,
            limit=1000  # Get a large sample
        )

        analysis = {
            "total_searches": len(searches),
            "search_types": {},
            "success_rate": 0,
            "average_results": 0,
            "common_queries": []
        }

        # Analyze search types
        for search in searches:
            search_type = search.search_type
            analysis["search_types"][search_type] = analysis["search_types"].get(search_type, 0) + 1

        # Calculate success rate
        successful = sum(1 for s in searches if s.status == "completed")
        analysis["success_rate"] = successful / len(searches) if searches else 0

        return analysis
