from typing import Dict, Any, List, Optional, cast, Set
from Backend.app.schemas import user
from Backend.orchestration.context_builder import ContextBuilder
from Backend.ai_services.rag.rag_service import RAGService
from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_registry import ai_registry
from Backend.orchestration.template_engine import render_template
from Backend.orchestration.intent_detector import IntentDetector
from Backend.data_layer.cache.ai_cache import get_cached_ai_result, cache_ai_result
from Backend.data_layer.cache.redis_client import get_cached_value, set_cached_value, get_keys_by_pattern

from Backend.data_layer.repositories.ai_model_repository import AIModelRepository
from Backend.app.schemas.message_schemas import ConversationHistory, UserMessage, AssistantMessage
import logging
import hashlib
import json
import time
from Backend.ai_services.reference.reference_resolver import ReferenceResolver
from openai.types.chat import ChatCompletionMessageParam
from sqlalchemy import Column
from difflib import SequenceMatcher
import uuid

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
        self.ai_registry = ai_registry
        # Use ConversationHistory for each user
        self._conversation_histories: Dict[int, ConversationHistory] = {}
        self.max_history_length = 10
        self.cache_hits: Dict[str, int] = {}
        self.cache_ttls: Dict[str, int] = {}
        self.cache_hit_threshold = 5
        self.similarity_threshold = 0.85  # Threshold for considering queries similar

    async def _get_or_create_model(self) -> int:
        """Get or create the AI model ID."""
        try:
            model = await self.model_repository.get_model_by_name_version("rag-service", "1.0")
            if model:
                model_id = getattr(model, 'id', None)
                if model_id is not None:
                    return int(str(model_id))

            # Create a new model if it doesn't exist
            model = await self.model_repository.create_model({
                "name": "rag-service",
                "version": "1.0",
                "type": "rag",
                "provider": "openai",
                "status": "active"
            })

            if model:
                model_id = getattr(model, 'id', None)
                if model_id is not None:
                    return int(str(model_id))

            raise ValueError("Failed to get valid model ID")
        except Exception as e:
            logger.error(f"Error getting/creating model: {str(e)}")
            raise

    async def _update_model_stats(self, latency: float, success: bool = True) -> None:
        """Update model usage statistics."""
        if self.model_repository and self._current_model_id:
            try:
                await self.model_repository.update_model_stats(
                    self._current_model_id,
                    latency,
                    success
                )
            except Exception as e:
                logger.error(f"Error updating model stats: {str(e)}")

    def _normalize_query(self, query: str) -> str:
        """Normalize query by removing extra whitespace and converting to lowercase."""
        return " ".join(query.lower().split())

    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries."""
        return SequenceMatcher(None, self._normalize_query(query1), self._normalize_query(query2)).ratio()

    async def _get_similar_cache_keys(self, user_input: str, prefix: str) -> Set[str]:
        """Get all cache keys that might contain similar queries."""
        similar_keys = set()
        try:
            # Get all keys with the given prefix
            all_keys = await get_keys_by_pattern(f"{prefix}*")

            # For each key, check if it contains a similar query
            for key in all_keys:
                cached_value = await get_cached_value(key)
                if cached_value:
                    try:
                        cached_data = json.loads(cached_value)
                        if isinstance(cached_data, dict):
                            # Extract the original query from the cache key components
                            key_components = json.loads(
                                cached_data.get("cache_key_components", "{}"))
                            cached_query = key_components.get("user_input", "")
                            if cached_query and self._calculate_similarity(user_input, cached_query) >= self.similarity_threshold:
                                similar_keys.add(key)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(
                            f"Error parsing cached value for key {key}: {e}")
        except Exception as e:
            logger.error(f"Error getting similar cache keys: {e}")
        return similar_keys

    async def _generate_cache_key(self, user_id: int, user_input: str, context: Dict[str, Any]) -> str:
        """Generate a cache key for the given input and context."""
        try:
            # Normalize the input to create a stable key
            normalized_input = self._normalize_query(user_input)

            # Create a stable version of the context
            stable_context = {}
            for key, value in context.items():
                if key == "conversation_history":
                    # Skip conversation history in cache key to maintain consistency
                    continue
                elif key == "domain":
                    # Include domain if present
                    if value:
                        stable_context[key] = str(value)
                elif isinstance(value, dict):
                    stable_context[key] = {
                        str(k): str(v) for k, v in value.items()}
                else:
                    stable_context[key] = str(value)

            # Create a deterministic string representation
            context_str = json.dumps(stable_context, sort_keys=True)

            # Generate the final key components
            key_components = [
                "ai_response",
                str(user_id),
                normalized_input,
                context_str
            ]

            # Create a hash of the components
            key_hash = hashlib.sha256(
                "|".join(key_components).encode()).hexdigest()
            return key_hash

        except Exception as e:
            logger.error(f"Error generating cache key: {str(e)}")
            # Return a fallback key that won't match anything in cache
            return f"error_key_{uuid.uuid4()}"

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result with enhanced statistics and similarity search."""
        try:
            # Get the cache config and prefix
            cache_config = self.ai_registry.get_cache_config()
            prefix = cache_config.get("llm_cache_key_prefix", "ai_cache:")

            # First try exact match
            cached = await get_cached_value(cache_key)
            if cached:
                cached_data = json.loads(cached)
                cached_data["cached"] = True  # Set cached flag to True
                self._update_cache_stats(cache_key)
                return cached_data

            # If no exact match, look for similar queries
            similar_keys = await self._get_similar_cache_keys(cache_key, prefix)
            if similar_keys:
                # Get the most recently cached similar result
                most_recent = None
                most_recent_time = 0
                for key in similar_keys:
                    cached = await get_cached_value(key)
                    if cached:
                        cached_data = json.loads(cached)
                        cached_time = cached_data.get("timestamp", 0)
                        if cached_time > most_recent_time:
                            most_recent = cached_data
                            most_recent_time = cached_time

                if most_recent:
                    # Update stats for the similar cache hit
                    most_recent["cached"] = True  # Set cached flag to True
                    self._update_cache_stats(list(similar_keys)[0])
                    return most_recent

        except Exception as e:
            logger.error(f"Error accessing cache: {str(e)}")
        return None

    async def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache result with metadata for similarity matching."""
        try:
            if not cache_key:
                return

            # Get TTL from config based on intent
            cache_config = self.ai_registry.get_cache_config()
            intent = result.get("intent", "default")
            ttl = cache_config.get("ttl_per_intent", {}).get(
                intent, cache_config.get("default_ttl", 3600))

            # Add metadata for similarity matching
            result["timestamp"] = time.time()
            result["cache_key_components"] = json.dumps({
                "user_input": result.get("original_input", ""),
                "intent": intent,
                "target": result.get("target", "default")
            })

            # Cache the result
            await set_cached_value(cache_key, json.dumps(result), ttl)
            logger.info(f"Cached result for key: {cache_key}")
        except Exception as e:
            logger.error(f"Error caching result: {str(e)}")

    def _update_cache_stats(self, cache_key: str) -> None:
        """Update cache statistics for a key."""
        if not hasattr(self, 'cache_hits'):
            self.cache_hits = {}
            self.cache_ttls = {}
            self.cache_hit_threshold = 5

        if cache_key not in self.cache_hits:
            self.cache_hits[cache_key] = 1
        else:
            self.cache_hits[cache_key] += 1

            # Increase TTL for frequently accessed items
            if self.cache_hits[cache_key] >= self.cache_hit_threshold:
                cache_config = self.ai_registry.get_cache_config()
                self.cache_ttls[cache_key] = min(
                    cache_config.get("default_ttl", 3600) *
                    2,  # Double the TTL
                    86400  # Max 24 hours
                )

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
            return {"answer": "", "sources": [], "has_sources": False}

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

    def _get_conversation_history(self, user_id: int) -> ConversationHistory:
        """Get or create conversation history for a user."""
        if user_id not in self._conversation_histories:
            self._conversation_histories[user_id] = ConversationHistory()
        return self._conversation_histories[user_id]

    def _update_conversation_history(self, user_id: int, prompt: str, response: str) -> None:
        """Update conversation history with new messages."""
        history = self._get_conversation_history(user_id)
        history.add_message(UserMessage(content=prompt))
        history.add_message(AssistantMessage(content=response))

    async def process_request(self, user_input: str, user_id: int, domain: Optional[str] = None) -> Dict[str, Any]:
        """Process an AI request with caching."""
        try:
            logger.info(
                f"Starting request processing for user {user_id} with input: {user_input[:50]}...")
            start_time = time.time()

            # Get conversation history
            logger.debug(f"Getting conversation history for user {user_id}")
            conversation_history = self._get_conversation_history(user_id)

            # Prepare context
            logger.debug("Preparing request context")
            context = {
                "conversation_history": conversation_history,
                "domain": domain,
                "user_id": user_id
            }

            # Generate cache key
            logger.debug("Generating cache key")
            cache_key = await self._generate_cache_key(user_id, user_input, context)
            logger.info(f"Generated cache key: {cache_key}")

            # Try to get from cache first
            logger.debug("Checking cache")
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"Cache hit for key: {cache_key}")
                self._update_cache_stats(cache_key)
                return cached_result

            logger.info("Cache miss - processing new request")
            try:
                # Process the request
                result = await self._process_request_internal(user_input, context)

                # Update conversation history
                if result and "response" in result:
                    logger.debug("Updating conversation history")
                    self._update_conversation_history(
                        user_id, user_input, result["response"])

                # Cache the result
                logger.debug("Caching result")
                await self._cache_result(cache_key, result)

                # Update model stats
                latency = time.time() - start_time
                logger.info(f"Request processed in {latency:.2f} seconds")
                await self._update_model_stats(latency)

                return result

            except Exception as e:
                logger.error(
                    f"Error in request processing: {str(e)}", exc_info=True)
                raise

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }

    async def _process_request_internal(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the request internally with all necessary steps."""
        try:
            logger.info("Starting internal request processing")

            if not self._current_model_id:
                logger.debug("Getting or creating model ID")
                self._current_model_id = await self._get_or_create_model()

            # Get domain and user_id from context
            domain = context.get("domain")
            user_id = context.get("user_id")
            logger.info(
                f"Processing request for domain: {domain}, user_id: {user_id}")

            if not isinstance(user_id, int):
                logger.error(f"Invalid user_id type: {type(user_id)}")
                raise ValueError("Invalid user_id in context")

            # Step 1: Collect context from the specified domain or all domains
            logger.debug("Collecting domain context")
            if domain:
                logger.debug(f"Getting context for specific domain: {domain}")
                repository_class = self.ai_registry.get_repository(domain)
                repository = repository_class(self.db)
                domain_context = {domain: await repository.get_context(user_id)}
                context.update(domain_context)
            else:
                logger.debug("Getting full context from all domains")
                full_context = await self.context_builder.get_full_context(user_id)
                context.update(full_context)

            # Step 2: Resolve any references in the user input
            logger.debug("Resolving references")
            reference_results = await self.reference_resolver.resolve_reference(user_input, context)
            context['resolved_references'] = reference_results
            logger.debug(
                f"Found {len(reference_results.get('matches', []))} references")

            # Step 3: Detect intent using the LLM
            logger.debug("Detecting intent")
            intent_data = await self.intent_detector.detect_intent(user_input, context)
            intent, target, description = intent_data["intent"], intent_data["target"], intent_data["description"]
            logger.info(f"Detected intent: {intent}, target: {target}")

            # Step 4: Decide if RAG is needed for the intent
            logger.debug("Checking RAG settings")
            domain_rag_settings = self.ai_registry.get_rag_settings(target)
            enable_rag_for_intent = domain_rag_settings.get(
                "intent_rag_usage", {}).get(intent, False)
            logger.info(f"RAG enabled for intent: {enable_rag_for_intent}")

            # Initialize RAG context
            if enable_rag_for_intent:
                logger.debug("Querying knowledge base")
                rag_context = await self.rag_service.query_knowledge_base(user_input, context=context)
                formatted_rag = self._prepare_rag_context(rag_context)
                logger.debug(
                    f"RAG response received with {len(formatted_rag.get('sources', []))} sources")
            else:
                formatted_rag = {
                    "answer": "",
                    "sources": [],
                    "has_sources": False
                }

            # Step 5: Generate the AI response
            logger.debug("Preparing response generation")
            template_variant = intent if intent in [
                "retrieve", "analyze", "plan", "summarize"] else "default"
            prompt_template = self.ai_registry.get_prompt_template(
                target, template_variant)
            logger.debug(f"Using template variant: {template_variant}")

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
                "resolved_references": reference_results,
                "has_references": bool(reference_results['matches']),
                "conversation_history": context.get("conversation_history", [])
            }

            # Render the template and generate response
            logger.debug("Rendering template and generating response")
            prompt = render_template(prompt_template, template_context)
            response = await self.llm_service.generate_response(prompt)
            logger.debug("Response received from LLM")

            if isinstance(response, dict):
                response_text = response.get("text", "")
                confidence = response.get("confidence", 0.0)
            else:
                # Handle streaming response
                logger.debug("Processing streaming response")
                chunks = []
                async for chunk in response:
                    chunks.append(chunk)
                response_text = "".join(chunks)
                confidence = 0.0

            # Prepare final response
            logger.info("Preparing final response")
            return {
                "response": response_text,
                "intent": intent,
                "target": target,
                "description": description,
                "rag_used": enable_rag_for_intent,
                "cached": False,
                "original_input": user_input,
                "context_used": context,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(
                f"Error in _process_request_internal: {str(e)}", exc_info=True)
            raise
