from typing import Dict, Any, List, Optional
from Backend.orchestration.context_builder import ContextBuilder
from Backend.ai_services.rag.rag_service import RAGService
from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_registry import ai_registry


class AIOrchestrator:
    def __init__(self, db_session):
        self.db = db_session
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self.context_builder = ContextBuilder(db_session)

    async def process_ai_request(
        self, 
        domain: str, 
        prompt: str, 
        user_id: int,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an AI request for a specific domain
        """
        # Get domain configuration and repository
        domain_config = ai_registry.get_domain_config(domain)
        repository_class = ai_registry.get_repository(domain)
        repository = repository_class(self.db)

        # Build context
        context = await self.context_builder.get_context(domain, user_id)
        if additional_context:
            context.update(additional_context)

        # Get domain-specific handler if exists
        handler = ai_registry.get_handler(domain)
        if handler:
            context = await handler.enrich_context(context)

        # Get prompt template and format it
        template = ai_registry.get_prompt_template(domain)
        formatted_prompt = template.format(
            user_prompt=prompt,
            context_data=context
        )

        # Retrieve relevant data via RAG
        rag_result = await self.rag_service.query_knowledge_base(
            query=prompt,
            context=context
        )

        # Build final prompt with RAG context
        if rag_result and rag_result.get('answer'):
            formatted_prompt += f"\n\nAdditional Context:\n{rag_result['answer']}"

        # Generate response
        response = await self.llm_service.generate_response(
            prompt=formatted_prompt,
            context={
                "user_id": user_id,
                "domain": domain,
                **context
            }
        )

        return {
            "response": response,
            "domain": domain,
            "context_used": context,
            "rag_used": bool(rag_result and rag_result.get('answer'))
        }

    async def process_multi_domain_request(
        self,
        domains: List[str],
        prompt: str,
        user_id: int,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an AI request across multiple domains
        """
        all_context = {}
        
        # Gather context from all domains
        for domain in domains:
            context = await self.context_builder.get_context(domain, user_id)
            all_context[domain] = context

        if additional_context:
            all_context.update(additional_context)

        # Use RAG across all domains
        rag_result = await self.rag_service.query_knowledge_base(
            query=prompt,
            context=all_context
        )

        # Build comprehensive prompt
        full_prompt = f"User Query: {prompt}\n\n"
        for domain in domains:
            template = ai_registry.get_prompt_template(domain)
            domain_section = template.format(
                user_prompt=prompt,
                context_data=all_context[domain]
            )
            full_prompt += f"\n{domain.upper()} CONTEXT:\n{domain_section}\n"

        if rag_result and rag_result.get('answer'):
            full_prompt += f"\nADDITIONAL KNOWLEDGE:\n{rag_result['answer']}"

        # Generate response
        response = await self.llm_service.generate_response(
            prompt=full_prompt,
            context={
                "user_id": user_id,
                "domains": domains,
                **all_context
            }
        )

        return {
            "response": response,
            "domains": domains,
            "context_used": all_context,
            "rag_used": bool(rag_result and rag_result.get('answer'))
        }
