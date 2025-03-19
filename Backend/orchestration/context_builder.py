from typing import Dict, Any
from Backend.orchestration.ai_registry import DOMAIN_CONFIG

class ContextBuilder:
    def __init__(self, db_session):
        self.db = db_session

    async def get_context(self, domain: str, user_id: int) -> str:
        domain_config = DOMAIN_CONFIG.get(domain)
        repository_class = domain_config["repository"]
        repository = repository_class(self.db)

        # Fetch and build context dynamically
        context_data = await repository.get_context(user_id) # TODO: Implement get_context method in repositories
        return context_data
