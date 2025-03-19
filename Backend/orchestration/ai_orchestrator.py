from typing import Dict, Any
from Backend.orchestration.context_builder import ContextBuilder
from Backend.ai_services.rag.rag_service import RAGService
from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_registry import DOMAIN_CONFIG


class AIOrchestrator:
    def __init__(self, db_session):
        self.db = db_session
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self.context_builder = ContextBuilder(db_session)

    async def process_ai_request(self, domains: list, prompt: str, user_id: int) -> Dict[str, Any]:
        full_context = ""

        # Gather context from all domains
        for domain in domains:
            context = await self.context_builder.get_context(domain, user_id)
            full_context += f"\n{domain.capitalize()} Context:\n{context}"

        # Retrieve additional knowledge (RAG)
        rag_context = await self.rag_service.query_knowledge_base(prompt)
        full_context += f"\nKnowledge Base:\n{rag_context['answer']}"

        # Dynamically format the prompt
        final_prompt = f"User Query: {prompt}\n{full_context[:4000]}"

        # TODO: Add user profile to context
        #user_profile = await self.get_user_profile(user_id)
        # final_prompt += f"User: {user_profile.name}."


        return await self.llm_service.generate_response(final_prompt, context={"user_id": user_id}) # TODO: add context structure
