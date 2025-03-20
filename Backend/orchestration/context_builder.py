from typing import Dict, Any, Optional
from Backend.orchestration.ai_registry import ai_registry


class ContextBuilder:
    def __init__(self, db_session):
        self.db = db_session

    async def get_full_context(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieve and merge data from all registered domains.
        """
        context = {}
        for domain in ai_registry.handler_mapping.keys():
            repository_class = ai_registry.get_repository(domain)
            repository = repository_class(self.db)

            # Fetch and enrich context
            domain_context = await repository.get_context(user_id)
            handler = ai_registry.get_handler(domain, self.db)
            if handler:
                domain_context = await handler.enrich_context(domain_context)

            context[domain] = domain_context
        return context

    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user profile data for context enrichment"""
        # TODO: Implement user profile fetching
        return {}

    async def merge_contexts(self, contexts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple domain contexts into a single context.
        This could be enhanced with ranking or filtering based on relevance.
        """
        merged = {}
        for domain, context in contexts.items():
            merged[domain] = context
        return merged
