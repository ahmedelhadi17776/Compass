from typing import Dict, Any, Optional
from Backend.orchestration.ai_registry import ai_registry

class ContextBuilder:
    def __init__(self, db_session):
        self.db = db_session

    async def get_context(self, domain: str, user_id: int) -> Dict[str, Any]:
        """
        Build context for a specific domain and user
        """
        # Get repository for domain
        repository_class = ai_registry.get_repository(domain)
        repository = repository_class(self.db)

        # Get base context from repository
        context = await repository.get_context(user_id)
        
        # Get domain handler if exists
        handler = ai_registry.get_handler(domain)
        if handler:
            # Allow domain-specific context enrichment
            context = await handler.enrich_context(context)

        return context

    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile data for context enrichment"""
        # TODO: Implement user profile fetching
        return {}

    async def merge_contexts(self, contexts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple domain contexts into a single context
        """
        merged = {}
        for domain, context in contexts.items():
            merged[domain] = context
        return merged
