from typing import Dict, Any, List, Optional
from Backend.app.schemas import user
from Backend.orchestration.context_builder import ContextBuilder
from Backend.ai_services.rag.rag_service import RAGService
from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_registry import ai_registry
from Backend.orchestration.template_engine import render_template
from Backend.orchestration.intent_detector import IntentDetector
from Backend.data_layer.cache.ai_cache import get_cached_ai_result, cache_ai_result
import logging
import hashlib
import json


class AIOrchestrator:
    def __init__(self, db_session):
        self.db = db_session
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self.context_builder = ContextBuilder(db_session)
        self.intent_detector = IntentDetector()
        self.logger = logging.getLogger(__name__)

    def _generate_cache_key(self, user_id: int, user_input: str, context: Dict[str, Any]) -> str:
        """
        Generate a cache key using user_id and the input.
        """
        cache_config = ai_registry.get_cache_config()
        if cache_config.get("enabled", False):
            cache_input = json.dumps(
                {"user_id": user_id, "query": user_input, "context": context}, sort_keys=True)
            return hashlib.sha256(cache_input.encode()).hexdigest()
        return None

    async def process_request(self, user_input: str, user_id: int) -> Dict[str, Any]:
        """
        Processes user input by detecting intent, retrieving data, and generating AI responses.
        """
        # Step 1: Collect context from all domains
        context = await self.context_builder.get_full_context(user_id)
        
        # Step 2: Detect intent using the LLM
        intent_data = await self.intent_detector.detect_intent(user_input, context)
        intent, target, description = intent_data["intent"], intent_data["target"], intent_data["description"]

        # Step 3: Apply cache and intent-specific TTL
        cache_key = self._generate_cache_key(user_id, user_input, context)
        cache_config = ai_registry.get_cache_config()
        intent_ttl = cache_config.get("ttl_per_intent", {}).get(
            intent, cache_config["default_ttl"])

        if cached_response := await get_cached_ai_result(cache_key):
            self.logger.info("Cache hit for key: %s", cache_key)
            return {"response": cached_response["answer"], "cached": True}

        # Step 4: Decide if RAG is needed for the intent
        domain_rag_settings = ai_registry.get_rag_settings(target)
        enable_rag_for_intent = domain_rag_settings.get(
            "intent_rag_usage", {}).get(intent, False)

        rag_context = {}
        if enable_rag_for_intent:
            rag_context = await self.rag_service.query_knowledge_base(user_input, context=context)

        # Step 5: Formulate the AI query using dynamic templates
        # Get the appropriate template based on domain and intent
        template_variant = intent if intent in ["retrieve", "analyze", "plan", "summarize"] else "default"
        prompt_template = ai_registry.get_prompt_template(target, template_variant)
        
        # Prepare template context with all necessary data
        template_context = {
            "user_prompt": user_input,
            "intent": intent,
            "target": target,
            "context_data": context.get(target, {}),
            "rag_data": rag_context.get('answer', ''),
            "all_context": context,
            "description": description
        }
        
        # Render the template with the provided context
        prompt = render_template(prompt_template, template_context)
        
        self.logger.debug(f"Generated prompt using template variant '{template_variant}' for domain '{target}'")

        # Step 6: Generate the AI response
        ai_response = await self.llm_service.generate_response(prompt)

        # Step 7: Store the response in cache (if enabled)
        cache_data = {
            "answer": ai_response["text"],
            "sources": rag_context.get("sources", []),
            "confidence": ai_response.get("confidence", 0.0),
            "context_used": context,
            "intent": intent,
            "target": target
        }
        await cache_ai_result(cache_key, cache_data, ttl=intent_ttl)

        return {
            "response": ai_response["text"],
            "intent": intent,
            "target": target,
            "description": description,
            "rag_used": bool(rag_context),
            "cached": False,
            "context_used": context
        }
