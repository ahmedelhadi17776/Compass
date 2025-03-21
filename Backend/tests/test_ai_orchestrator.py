import pytest
import json
import hashlib
from unittest.mock import MagicMock, patch, AsyncMock, ANY
from Backend.orchestration.ai_orchestrator import AIOrchestrator
from Backend.orchestration.context_builder import ContextBuilder
from Backend.orchestration.intent_detector import IntentDetector
from Backend.ai_services.rag.rag_service import RAGService
from Backend.ai_services.llm.llm_service import LLMService
from Backend.data_layer.cache.ai_cache import get_cached_ai_result, cache_ai_result
from Backend.data_layer.repositories.ai_model_repository import AIModelRepository
from typing import Dict, List, Any, Optional, cast

# Test data
MOCK_USER_ID = 123
MOCK_USER_INPUT = "Summarize my tasks for this week"

MOCK_CONTEXT = {
    "tasks": [
        {"title": "Complete project report", "due_date": "2023-06-15",
            "priority": "high", "status": "in_progress"},
        {"title": "Review pull requests", "due_date": "2023-06-13",
            "priority": "medium", "status": "pending"}
    ],
    "todos": [
        {"title": "Buy groceries", "status": "pending"},
        {"title": "Call dentist", "status": "completed"}
    ]
}

MOCK_INTENT_DATA = {
    "intent": "summarize",
    "target": "tasks",
    "description": "Provide a summary of current tasks"
}

MOCK_RAG_RESULT = {
    "answer": "Based on the knowledge base, you have 2 tasks due this week.",
    "sources": [{"title": "Task Database", "id": "task_records"}],
    "confidence": 0.92
}

MOCK_LLM_RESPONSE = {
    "text": "This week you have 2 tasks: 'Complete project report' (high priority, due Jun 15) and 'Review pull requests' (medium priority, due Jun 13).",
    "usage": {"prompt_tokens": 250, "completion_tokens": 150, "total_tokens": 400}
}

MOCK_CACHE_RESPONSE = {
    "answer": "Cached response: You have 2 tasks due this week.",
    "sources": [{"title": "Task Database"}],
    "confidence": 0.95
}


class TestAIOrchestrator:

    @pytest.fixture
    def mock_db_session(self):
        return MagicMock()

    @pytest.fixture
    def mock_model_repository(self):
        repository = AsyncMock(spec=AIModelRepository)
        repository.get_model_by_name_version.return_value = MagicMock(id=1)
        repository.create_model.return_value = MagicMock(id=1)
        repository.update_model_stats.return_value = None
        return repository

    @pytest.fixture
    def orchestrator(self, mock_db_session, mock_model_repository):
        orchestrator = AIOrchestrator(mock_db_session)
        orchestrator.model_repository = mock_model_repository
        return orchestrator

    @pytest.fixture
    def mock_context_builder(self):
        context_builder = MagicMock(spec=ContextBuilder)
        context_builder.get_full_context = AsyncMock(return_value=MOCK_CONTEXT)
        return context_builder

    @pytest.fixture
    def mock_intent_detector(self):
        intent_detector = MagicMock(spec=IntentDetector)
        intent_detector.detect_intent = AsyncMock(
            return_value=MOCK_INTENT_DATA)
        return intent_detector

    @pytest.fixture
    def mock_rag_service(self):
        rag_service = MagicMock(spec=RAGService)
        rag_service.query_knowledge_base = AsyncMock(
            return_value=MOCK_RAG_RESULT)
        return rag_service

    @pytest.fixture
    def mock_llm_service(self):
        llm_service = MagicMock(spec=LLMService)
        llm_service.generate_response = AsyncMock(
            return_value=MOCK_LLM_RESPONSE)
        return llm_service

    # Test the full workflow with no cache hit
    @patch('Backend.orchestration.ai_orchestrator.get_cached_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.cache_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.ai_registry')
    async def test_process_request_full_workflow(self, mock_ai_registry, mock_cache_result,
                                                 mock_get_cache, orchestrator,
                                                 mock_context_builder, mock_intent_detector,
                                                 mock_rag_service, mock_llm_service):
        # Setup mocks
        orchestrator.context_builder = mock_context_builder
        orchestrator.intent_detector = mock_intent_detector
        orchestrator.rag_service = mock_rag_service
        orchestrator.llm_service = mock_llm_service

        # Mock cache miss
        mock_get_cache.return_value = None

        # Mock RAG settings
        mock_ai_registry.get_cache_config.return_value = {
            "enabled": True,
            "default_ttl": 3600,
            "ttl_per_intent": {
                "summarize": 14400
            }
        }
        mock_ai_registry.get_rag_settings.return_value = {
            "intent_rag_usage": {
                "summarize": True
            }
        }
        mock_ai_registry.get_prompt_template.return_value = "User Input: {{ user_prompt }}\nIntent: {{ intent }}\nContext: {{ context_data }}\nRAG: {{ rag_data }}"

        # Execute the process_request method
        result = await orchestrator.process_request(MOCK_USER_INPUT, MOCK_USER_ID)

        # Assert workflow steps were called in the correct order
        mock_context_builder.get_full_context.assert_called_once_with(
            MOCK_USER_ID)
        mock_intent_detector.detect_intent.assert_called_once_with(
            MOCK_USER_INPUT, MOCK_CONTEXT)
        mock_get_cache.assert_called_once()
        mock_ai_registry.get_rag_settings.assert_called_once_with(
            MOCK_INTENT_DATA["target"])
        mock_rag_service.query_knowledge_base.assert_called_once()
        mock_llm_service.generate_response.assert_called_once()
        mock_cache_result.assert_called_once()

        # Assert the expected response
        assert result["response"] == MOCK_LLM_RESPONSE["text"]
        assert result["intent"] == MOCK_INTENT_DATA["intent"]
        assert result["target"] == MOCK_INTENT_DATA["target"]
        assert result["cached"] is False
        assert result["rag_used"] is True

    # Test workflow with cache hit
    @patch('Backend.orchestration.ai_orchestrator.get_cached_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.ai_registry')
    async def test_process_request_with_cache_hit(self, mock_ai_registry, mock_get_cache,
                                                  orchestrator, mock_context_builder,
                                                  mock_intent_detector):
        # Setup mocks
        orchestrator.context_builder = mock_context_builder
        orchestrator.intent_detector = mock_intent_detector

        # Mock cache hit
        mock_get_cache.return_value = {"answer": MOCK_CACHE_RESPONSE["answer"]}

        # Mock cache config
        mock_ai_registry.get_cache_config.return_value = {
            "enabled": True,
            "default_ttl": 3600,
            "ttl_per_intent": {
                "summarize": 14400
            }
        }

        # Execute the process_request method
        result = await orchestrator.process_request(MOCK_USER_INPUT, MOCK_USER_ID)

        # Assert cache was checked and workflow stopped after cache hit
        mock_context_builder.get_full_context.assert_called_once_with(
            MOCK_USER_ID)
        mock_intent_detector.detect_intent.assert_called_once_with(
            MOCK_USER_INPUT, MOCK_CONTEXT)
        mock_get_cache.assert_called_once()

        # Assert the expected response
        assert result["response"] == MOCK_CACHE_RESPONSE["answer"]
        assert result["cached"] is True

    # Test the cache key generation
    def test_generate_cache_key(self, orchestrator):
        # Setup
        user_id = MOCK_USER_ID
        user_input = MOCK_USER_INPUT
        context = MOCK_CONTEXT

        # Test when cache is enabled
        with patch('Backend.orchestration.ai_orchestrator.ai_registry') as mock_ai_registry:
            mock_ai_registry.get_cache_config.return_value = {"enabled": True}

            # Execute
            cache_key = orchestrator._generate_cache_key(
                user_id, user_input, context)

            # Verify
            expected_input = json.dumps(
                {"user_id": user_id, "query": user_input, "context": context},
                sort_keys=True
            )
            expected_hash = hashlib.sha256(expected_input.encode()).hexdigest()
            assert cache_key == expected_hash

        # Test when cache is disabled
        with patch('Backend.orchestration.ai_orchestrator.ai_registry') as mock_ai_registry:
            mock_ai_registry.get_cache_config.return_value = {"enabled": False}

            # Execute
            cache_key = orchestrator._generate_cache_key(
                user_id, user_input, context)

            # Verify
            assert cache_key is None

    # Test context data formatting
    def test_format_context_data(self, orchestrator):
        # Test formatting for different intents
        data = MOCK_CONTEXT["tasks"]

        # Test for retrieve intent (should be brief)
        retrieve_result = orchestrator._format_context_data(data, "retrieve")
        assert "Complete project report" in retrieve_result

        # Test for analyze intent (should be more detailed)
        analyze_result = orchestrator._format_context_data(data, "analyze")
        assert "Complete project report" in analyze_result
        assert "high" in analyze_result
        assert "due" in analyze_result

    # Test RAG context preparation
    def test_prepare_rag_context(self, orchestrator):
        # Test with empty RAG result
        empty_result = orchestrator._prepare_rag_context({})
        assert empty_result["answer"] == ""
        assert empty_result["sources"] == []

        # Test with valid RAG result
        full_result = orchestrator._prepare_rag_context(MOCK_RAG_RESULT)
        assert full_result["answer"] == MOCK_RAG_RESULT["answer"]
        assert len(full_result["sources"]) == 1
        assert full_result["has_sources"] is True

    # Test workflow when RAG is disabled for intent
    @patch('Backend.orchestration.ai_orchestrator.get_cached_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.cache_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.ai_registry')
    async def test_process_request_with_rag_disabled(self, mock_ai_registry, mock_cache_result,
                                                     mock_get_cache, orchestrator,
                                                     mock_context_builder, mock_intent_detector,
                                                     mock_llm_service):
        # Setup mocks
        orchestrator.context_builder = mock_context_builder
        orchestrator.intent_detector = mock_intent_detector
        orchestrator.llm_service = mock_llm_service

        # Create a mock for rag_service
        mock_rag_service = MagicMock()
        orchestrator.rag_service = mock_rag_service

        # Mock cache miss
        mock_get_cache.return_value = None

        # Mock RAG settings with RAG disabled for summarize intent
        mock_ai_registry.get_cache_config.return_value = {
            "enabled": True,
            "default_ttl": 3600,
            "ttl_per_intent": {
                "summarize": 14400
            }
        }
        mock_ai_registry.get_rag_settings.return_value = {
            "intent_rag_usage": {
                "summarize": False
            }
        }
        mock_ai_registry.get_prompt_template.return_value = "User Input: {{ user_prompt }}\nIntent: {{ intent }}\nContext: {{ context_data }}"

        # Execute the process_request method
        result = await orchestrator.process_request(MOCK_USER_INPUT, MOCK_USER_ID)

        # Assert that RAG was NOT called
        mock_rag_service.query_knowledge_base.assert_not_called()

        # Assert the expected response
        assert result["response"] == MOCK_LLM_RESPONSE["text"]
        assert result["intent"] == MOCK_INTENT_DATA["intent"]
        assert result["rag_used"] is False

    # Test workflow with string response from LLM
    @patch('Backend.orchestration.ai_orchestrator.get_cached_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.cache_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.ai_registry')
    async def test_process_request_with_string_response(self, mock_ai_registry, mock_cache_result,
                                                        mock_get_cache, orchestrator,
                                                        mock_context_builder, mock_intent_detector,
                                                        mock_rag_service, mock_llm_service):
        # Setup mocks
        orchestrator.context_builder = mock_context_builder
        orchestrator.intent_detector = mock_intent_detector
        orchestrator.rag_service = mock_rag_service
        orchestrator.llm_service = mock_llm_service
        orchestrator._current_model_id = 1

        # Mock cache miss
        mock_get_cache.return_value = None

        # Mock string response from LLM
        mock_llm_service.generate_response.return_value = {
            "text": "Simple string response",
            "confidence": 0.8
        }

        # Mock configs
        mock_ai_registry.get_cache_config.return_value = {
            "enabled": True,
            "default_ttl": 3600,
            "ttl_per_intent": {}
        }
        mock_ai_registry.get_rag_settings.return_value = {
            "intent_rag_usage": {
                "summarize": True
            }
        }
        mock_ai_registry.get_prompt_template.return_value = "Test template"

        # Execute
        result = await orchestrator.process_request(MOCK_USER_INPUT, MOCK_USER_ID)

        # Verify
        assert isinstance(result, dict)
        assert result["response"] == "Simple string response"
        assert result["cached"] is False
        assert result["rag_used"] is True

    @pytest.mark.asyncio
    async def test_model_initialization(self, orchestrator, mock_model_repository):
        # Test model initialization
        model_id = await orchestrator._get_or_create_model()
        assert model_id == 1
        mock_model_repository.get_model_by_name_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_model_stats_update(self, orchestrator):
        # Test model stats update
        orchestrator._current_model_id = 1
        await orchestrator._update_model_stats(0.5, True)
        orchestrator.model_repository.update_model_stats.assert_called_once_with(
            1, 0.5, True)

    @pytest.mark.asyncio
    @patch('Backend.orchestration.ai_orchestrator.get_cached_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.cache_ai_result')
    @patch('Backend.orchestration.ai_orchestrator.ai_registry')
    async def test_process_request_with_model_tracking(
        self,
        mock_ai_registry,
        mock_cache_result,
        mock_get_cache,
        orchestrator,
        mock_context_builder,
        mock_intent_detector,
        mock_rag_service,
        mock_llm_service
    ):
        # Setup mocks
        orchestrator.context_builder = mock_context_builder
        orchestrator.intent_detector = mock_intent_detector
        orchestrator.rag_service = mock_rag_service
        orchestrator.llm_service = mock_llm_service
        orchestrator._current_model_id = 1

        # Mock cache miss
        mock_get_cache.return_value = None

        # Mock registry settings
        mock_ai_registry.get_cache_config.return_value = {
            "enabled": True,
            "default_ttl": 3600,
            "ttl_per_intent": {}
        }
        mock_ai_registry.get_rag_settings.return_value = {
            "intent_rag_usage": {
                "summarize": True
            }
        }
        mock_ai_registry.get_prompt_template.return_value = "Test template"

        # Mock service responses
        mock_context_builder.get_full_context.return_value = MOCK_CONTEXT
        mock_intent_detector.detect_intent.return_value = MOCK_INTENT_DATA
        mock_rag_service.query_knowledge_base.return_value = MOCK_RAG_RESULT
        mock_llm_service.generate_response.return_value = MOCK_LLM_RESPONSE

        # Execute
        result = await orchestrator.process_request(MOCK_USER_INPUT, MOCK_USER_ID)

        # Verify model tracking and response
        assert isinstance(result, dict)
        assert result.get("response") == MOCK_LLM_RESPONSE["text"]
        assert result.get("intent") == MOCK_INTENT_DATA["intent"]
        assert result.get("rag_used") is True
        orchestrator.model_repository.update_model_stats.assert_called_with(
            1, ANY, True)

        # Verify workflow steps were called
        mock_context_builder.get_full_context.assert_called_once_with(
            MOCK_USER_ID)
        mock_intent_detector.detect_intent.assert_called_once_with(
            MOCK_USER_INPUT, MOCK_CONTEXT)
        mock_rag_service.query_knowledge_base.assert_called_once()
        mock_llm_service.generate_response.assert_called_once()
        mock_cache_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_request_error_handling(
        self,
        orchestrator,
        mock_context_builder,
        mock_intent_detector
    ):
        # Setup
        orchestrator.context_builder = mock_context_builder
        orchestrator.intent_detector = mock_intent_detector
        orchestrator._current_model_id = 1

        # Force an error
        mock_context_builder.get_full_context.side_effect = Exception(
            "Test error")

        # Execute
        result = await orchestrator.process_request(MOCK_USER_INPUT, MOCK_USER_ID)

        # Verify
        assert isinstance(result, dict)
        assert result.get("error") is True
        assert "Test error" in result.get("response", "")
        orchestrator.model_repository.update_model_stats.assert_called_with(
            1, ANY, False)
