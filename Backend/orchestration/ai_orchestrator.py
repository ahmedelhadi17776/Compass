from typing import Dict, Any, List, Optional
from Backend.app.schemas import user
from Backend.orchestration.context_builder import ContextBuilder
from Backend.ai_services.rag.rag_service import RAGService
from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_registry import ai_registry
from Backend.orchestration.template_engine import render_template
from Backend.orchestration.intent_detector import IntentDetector
from Backend.data_layer.cache.ai_cache import get_cached_ai_result, cache_ai_result
from Backend.data_layer.repositories.ai_model_repository import AIModelRepository
import logging
import hashlib
import json
import time
from Backend.ai_services.reference.reference_resolver import ReferenceResolver

logger = logging.getLogger(__name__)


class AIOrchestrator:
    def __init__(self, db_session):
        self.db = db_session
        self.model_repository = AIModelRepository(db_session)
        self.rag_service = RAGService(db_session)
        self.llm_service = LLMService(db_session)
        self.context_builder = ContextBuilder(db_session)
        self.intent_detector = IntentDetector()
        self.logger = logging.getLogger(__name__)
        self.reference_resolver = ReferenceResolver()
        self._current_model_id: Optional[int] = None

    async def _get_or_create_model(self) -> Optional[int]:
        """Get or create AI model record in database."""
        try:
            model = await self.model_repository.get_model_by_name_version(
                name="ai-orchestrator",
                version="1.0"
            )

            if not model:
                model = await self.model_repository.create_model({
                    "name": "ai-orchestrator",
                    "version": "1.0",
                    "type": "orchestrator",
                    "provider": "hybrid",
                    "model_metadata": {
                        "services": ["rag", "llm", "intent-detection", "reference-resolution"],
                        "cache_enabled": True
                    },
                    "status": "active"
                })

            # Safely convert SQLAlchemy Column to int
            model_id = getattr(model, 'id', None)
            return int(model_id) if model_id is not None else None
        except Exception as e:
            logger.error(f"Error getting/creating AI model: {str(e)}")
            return None

    async def _update_model_stats(self, latency: float, success: bool = True) -> None:
        """Update model usage statistics."""
        if self._current_model_id:
            try:
                await self.model_repository.update_model_stats(
                    self._current_model_id,
                    latency,
                    success
                )
            except Exception as e:
                logger.error(f"Error updating model stats: {str(e)}")

    def _generate_cache_key(self, user_id: int, user_input: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate a cache key using user_id and the input.
        Returns None if caching is disabled.
        """
        cache_config = ai_registry.get_cache_config()
        if cache_config.get("enabled", False):
            cache_input = json.dumps(
                {"user_id": user_id, "query": user_input, "context": context}, sort_keys=True)
            return hashlib.sha256(cache_input.encode()).hexdigest()
        return None

    def _format_context_data(self, data: Any, intent: str) -> str:
        """
        Format context data into a structured, human-readable format based on intent type.

        Args:
            data: The raw context data from a specific domain
            intent: The detected user intent (retrieve, analyze, summarize, plan)

        Returns:
            A formatted string representation of the context data
        """
        if not data:
            return "No data available"

        # Handle different data types
        if isinstance(data, dict):
            if not data:
                return "Empty context"

            # Format dictionary data
            formatted = []
            for key, value in data.items():
                # Skip private or internal keys
                if key.startswith('_'):
                    continue

                # Format based on value type
                if isinstance(value, list):
                    formatted.append(f"{key.capitalize()}:")
                    for i, item in enumerate(value, 1):
                        if isinstance(item, dict):
                            formatted.append(
                                f"  {i}. " + self._format_dict_item(item, intent))
                        else:
                            formatted.append(f"  {i}. {item}")
                else:
                    formatted.append(f"{key.capitalize()}: {value}")

            return "\n".join(formatted)

        elif isinstance(data, list):
            if not data:
                return "Empty list"

            # For analyze and summarize intents, include more details
            include_details = intent in ["analyze", "summarize"]

            formatted = []
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    formatted.append(
                        f"{i}. " + self._format_dict_item(item, intent, include_details))
                else:
                    formatted.append(f"{i}. {item}")

            return "\n".join(formatted)

        # Default fallback for other data types
        return str(data)

    def _format_dict_item(self, item: Dict[str, Any], intent: str, include_details: bool = True) -> str:
        """
        Format a dictionary item into a structured string representation.

        Args:
            item: Dictionary item to format
            intent: Current intent for context-aware formatting
            include_details: Whether to include detailed attributes

        Returns:
            Formatted string representation of the item
        """
        # Extract the most important attributes first
        title = item.get('title', item.get('name', 'Untitled'))
        description = item.get('description', '')
        status = item.get('status', '')
        due_date = item.get('due_date', item.get('deadline', ''))
        priority = item.get('priority', '')

        # Base representation includes title and status if available
        result = f"{title}"

        if status:
            result += f" ({status})"

        # For retrieve intent, keep it brief
        if intent == "retrieve" and not include_details:
            return result

        # For other intents, include more details if available
        details = []
        if due_date:
            details.append(f"due: {due_date}")
        if priority:
            details.append(f"priority: {priority}")
        if description and len(description) > 50:
            details.append(f"description: {description[:50]}...")
        elif description:
            details.append(f"description: {description}")

        if details:
            result += f" - {', '.join(details)}"

        return result

    def _prepare_rag_context(self, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and format the RAG context for template rendering.

        Args:
            rag_result: The raw RAG result from RAGService

        Returns:
            Formatted RAG context with answer and sources
        """
        if not rag_result:
            return {"answer": "", "sources": []}

        answer = rag_result.get("answer", "")
        sources = rag_result.get("sources", [])

        # Format sources if available
        formatted_sources = []
        if sources:
            for i, source in enumerate(sources, 1):
                if isinstance(source, dict):
                    source_info = source.get(
                        "title", source.get("source", f"Source {i}"))
                    formatted_sources.append(f"{i}. {source_info}")
                else:
                    formatted_sources.append(f"{i}. {source}")

        return {
            "answer": answer,
            "sources": formatted_sources,
            "has_sources": bool(formatted_sources)
        }

    async def process_request(self, user_input: str, user_id: int) -> Dict[str, Any]:
        try:
            if not self._current_model_id:
                self._current_model_id = await self._get_or_create_model()

            start_time = time.time()
            success = True

            # Step 1: Collect context from all domains
            context = await self.context_builder.get_full_context(user_id)

            # Step 2: Resolve any references in the user input
            reference_results = await self.reference_resolver.resolve_reference(user_input, context)

            # Step 3: Add reference results to the context
            context['resolved_references'] = reference_results

            # Step 4: Detect intent using the LLM
            intent_data = await self.intent_detector.detect_intent(user_input, context)
            intent, target, description = intent_data["intent"], intent_data["target"], intent_data["description"]

            # Step 5: Apply cache and intent-specific TTL
            cache_key = self._generate_cache_key(user_id, user_input, context)
            cache_config = ai_registry.get_cache_config()
            intent_ttl = cache_config.get("ttl_per_intent", {}).get(
                intent, cache_config["default_ttl"])

            if cache_key and (cached_response := await get_cached_ai_result(cache_key)):
                self.logger.info("Cache hit for key: %s", cache_key)
                return {"response": cached_response["answer"], "cached": True}

            # Step 6: Decide if RAG is needed for the intent
            domain_rag_settings = ai_registry.get_rag_settings(target)
            enable_rag_for_intent = domain_rag_settings.get(
                "intent_rag_usage", {}).get(intent, False)

            # Initialize RAG context
            rag_context = {}
            if enable_rag_for_intent:
                rag_context = await self.rag_service.query_knowledge_base(user_input, context=context)
                # Prepare RAG context with formatted sources
                formatted_rag = self._prepare_rag_context(rag_context)
            else:
                # When RAG is disabled, use an empty formatted RAG context with all required keys
                formatted_rag = {
                    "answer": "",
                    "sources": [],
                    "has_sources": False
                }

            # Step 7: Generate the AI response
            template_variant = intent if intent in [
                "retrieve", "analyze", "plan", "summarize"] else "default"
            prompt_template = ai_registry.get_prompt_template(
                target, template_variant)

            # Format domain-specific context data
            target_context = context.get(target, {})
            formatted_context = self._format_context_data(
                target_context, intent)

            # Prepare template context
            template_context = {
                "user_prompt": user_input,
                "intent": intent,
                "target": target,
                "context_data": formatted_context,
                "raw_context": target_context,
                "rag_data": formatted_rag["answer"],
                "rag_sources": formatted_rag["sources"],
                "has_rag_sources": formatted_rag["has_sources"],
                "all_context": context,
                "description": description,
                "user_id": user_id,
                "resolved_references": reference_results,
                "has_references": bool(reference_results['matches'])
            }

            # Render the template and generate response
            prompt = render_template(prompt_template, template_context)
            response = await self.llm_service.generate_response(prompt)

            if isinstance(response, dict):
                response_text = response.get("text", "")
                confidence = response.get("confidence", 0.0)
            else:
                # Handle streaming response
                chunks = []
                async for chunk in response:
                    chunks.append(chunk)
                response_text = "".join(chunks)
                confidence = 0.0

            # Prepare final response
            result = {
                "response": response_text,
                "intent": intent,
                "target": target,
                "description": description,
                "rag_used": bool(rag_context),
                "cached": False,
                "context_used": context,
                "confidence": confidence
            }

            # Cache the response
            if cache_key:
                await cache_ai_result(cache_key, result, ttl=intent_ttl)

            # Update stats
            latency = time.time() - start_time
            await self._update_model_stats(latency, success)

            return result

        except Exception as e:
            success = False
            latency = time.time() - start_time
            await self._update_model_stats(latency, success)

            logger.error(f"Error processing request: {str(e)}")
            return {
                "response": f"Error: {str(e)}",
                "error": True,
                "cached": False
            }
