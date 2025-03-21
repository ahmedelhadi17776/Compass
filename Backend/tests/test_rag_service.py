from Backend.data_layer.vector_db.chroma_client import ChromaClient
from Backend.ai_services.rag.rag_service import RAGService
import pytest
from unittest.mock import AsyncMock, Mock, patch, PropertyMock, MagicMock, ANY
import sys
import os
from pathlib import Path
import asyncio
import json
import hashlib
import numpy as np
from concurrent.futures import ThreadPoolExecutor, Future
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.ai_services.llm.llm_service import LLMService
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result
from Backend.data_layer.repositories.ai_model_repository import AIModelRepository
from typing import Dict, List, Any, Optional, AsyncGenerator, Generator, cast
import copy
from Backend.ai_services.rag.rag_service import RAGService
from Backend.orchestration.ai_registry import ai_registry
from concurrent.futures._base import InvalidStateError

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Backend directory
sys.path.insert(0, str(project_root.parent))  # COMPASS directory

# Test data
MOCK_QUERY = "How do I complete my current tasks?"
MOCK_CONTEXT = {
    "tasks": [{"title": "Design database schema", "status": "pending"}]
}
MOCK_FILTERS = {"metadata_field": "value"}
MOCK_USER_ID = 123

MOCK_EMBEDDING = np.array([0.1, 0.2, 0.3, 0.4, 0.5])  # Simple mock embedding
MOCK_BATCH_EMBEDDINGS = np.array(
    [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])  # For batch testing

MOCK_CHROMA_RESULTS = {
    "ids": [["doc1", "doc2"]],
    "distances": [[0.1, 0.3]],
    "documents": [["Task details for database schema", "Information about task completion"]],
    "metadatas": [[
        {"title": "Database Schema", "source": "task_repository"},
        {"title": "Task Workflow", "source": "knowledge_base"}
    ]]
}

MOCK_EMPTY_CHROMA_RESULTS = {
    "ids": [[]],
    "distances": [[]],
    "documents": [[]],
    "metadatas": [[]]
}

MOCK_LLM_RESPONSE = {
    "text": "Based on your tasks, you should start by finalizing the database schema design.",
    "usage": {"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
    "confidence": 0.92
}

MOCK_CACHED_RESULT = {
    "answer": "Cached response about completing tasks",
    "sources": [{"title": "Task Workflow"}],
    "confidence": 0.9
}


class MockFuture:
    def __init__(self, result=None):
        self._result = result
        self._exception = None
        self._done = False

    def set_exception(self, exception):
        if self._done:
            raise InvalidStateError(f"FINISHED: {self!r}")
        self._exception = exception
        self._done = True

    def set_result(self, result):
        if self._done:
            raise InvalidStateError(f"FINISHED: {self!r}")
        self._result = result
        self._done = True

    def result(self):
        if self._exception:
            raise self._exception
        return self._result

    def done(self):
        return self._done


class TestRAGService:

    @pytest.fixture
    def mock_chroma_client(self) -> Generator[MagicMock, None, None]:
        with patch('Backend.ai_services.rag.rag_service.ChromaClient') as mock:
            client = MagicMock()
            collection = MagicMock()
            mock.return_value.client = client
            mock.return_value.collection = collection
            yield mock

    @pytest.fixture
    def mock_embedding_service(self) -> Generator[AsyncMock, None, None]:
        with patch('Backend.ai_services.rag.rag_service.EmbeddingService') as mock:
            mock_service = AsyncMock()
            mock_service.get_embedding.return_value = [
                0.1] * 384  # Fixed length embedding
            mock.return_value = mock_service
            yield mock

    @pytest.fixture
    def mock_llm_service(self) -> Generator[AsyncMock, None, None]:
        with patch('Backend.ai_services.rag.rag_service.LLMService') as mock:
            mock_service = AsyncMock()
            mock_service.generate_response.return_value = {
                "text": "Test response", "confidence": 0.8}
            mock.return_value = mock_service
            yield mock

    @pytest.fixture
    def mock_thread_pool(self) -> ThreadPoolExecutor:
        return ThreadPoolExecutor(max_workers=1)

    @pytest.fixture
    def mock_model_repository(self) -> Generator[AsyncMock, None, None]:
        with patch('Backend.data_layer.repositories.ai_model_repository.AIModelRepository') as mock:
            mock_repo = AsyncMock()
            mock_repo.get_model_by_name_version.return_value = MagicMock(id=1)
            mock_repo.create_model.return_value = MagicMock(id=1)
            mock_repo.update_model_stats.return_value = None
            mock.return_value = mock_repo
            yield mock

    @pytest.fixture
    def rag_service_with_mocks(
        self,
        mock_chroma_client: MagicMock,
        mock_embedding_service: AsyncMock,
        mock_llm_service: AsyncMock,
        mock_thread_pool: ThreadPoolExecutor,
        mock_model_repository: AsyncMock
    ) -> RAGService:
        service = RAGService(db_session=AsyncMock())
        service.chroma_client = mock_chroma_client()
        service.collection = service.chroma_client.collection
        service.embedding_service = mock_embedding_service()
        service.llm_service = mock_llm_service()
        service.thread_pool = mock_thread_pool
        service.model_repository = mock_model_repository()
        return service

    @pytest.mark.asyncio
    async def test_generate_cache_key(self, rag_service_with_mocks):
        # Setup
        query = MOCK_QUERY
        # Convert dictionaries to JSON strings
        context = json.dumps(MOCK_CONTEXT, sort_keys=True)
        filters = json.dumps(MOCK_FILTERS, sort_keys=True)

        # Execute - don't await since it's not async
        cache_key = rag_service_with_mocks._generate_cache_key(
            query, context, filters)

        # Verify
        assert isinstance(cache_key, str)
        assert cache_key.startswith("rag_query:")
        assert len(cache_key) > len("rag_query:")

    @pytest.mark.asyncio
    async def test_get_embeddings_batch(self, rag_service_with_mocks):
        # Setup
        texts = ["text1", "text2", "text3"]
        mock_embeddings = MOCK_BATCH_EMBEDDINGS.copy()
        rag_service_with_mocks.embedding_service.get_embedding.return_value = mock_embeddings

        # Execute
        result = await rag_service_with_mocks._get_embeddings_batch(texts)

        # Verify
        assert isinstance(result, list)  # Should return a list of embeddings
        rag_service_with_mocks.embedding_service.get_embedding.assert_called_once_with(
            texts, normalize=True
        )

    @pytest.mark.asyncio
    @patch('Backend.ai_services.rag.rag_service.get_cached_ai_result')
    @patch('Backend.ai_services.rag.rag_service.cache_ai_result')
    @patch('Backend.ai_services.rag.rag_service.ai_registry')
    async def test_query_knowledge_base_with_parallel_processing(
        self, mock_ai_registry, mock_cache_result, mock_get_cache, rag_service_with_mocks
    ):
        # Setup mock responses
        mock_embedding = [0.1] * 384
        mock_results = {
            "ids": [["1", "2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[
                {"title": "Database Schema", "source": "task_repository"},
                {"title": "Task Workflow", "source": "knowledge_base"}
            ]],
            "distances": [[0.1, 0.2]]
        }

        # Configure mocks
        mock_get_cache.return_value = None  # No cached result
        mock_ai_registry.get_cache_config.return_value = {
            "ttl_per_intent": {},
            "default_ttl": 3600
        }
        rag_service_with_mocks.embedding_service.get_embedding.return_value = mock_embedding

        # Mock the collection's query method to return the results directly
        def mock_query(*args, **kwargs):
            return mock_results

        rag_service_with_mocks.collection.query = mock_query

        # Mock the LLM response
        rag_service_with_mocks.llm_service.generate_response.return_value = {
            "text": "Based on your tasks, you should start by finalizing the database schema design.",
            "confidence": 0.8
        }

        # Test with dictionaries
        result = await rag_service_with_mocks.query_knowledge_base(
            query="test query",
            context={"key": "value"},
            filters={"type": "test"}
        )

        # Verify the result
        expected_result = {
            "answer": "Based on your tasks, you should start by finalizing the database schema design.",
            "sources": [
                {"title": "Database Schema", "source": "task_repository"},
                {"title": "Task Workflow", "source": "knowledge_base"}
            ],
            "confidence": 0.8,
            "embedding_dimension": 384
        }
        assert result == expected_result
        mock_cache_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_knowledge_base_with_retries(self, rag_service_with_mocks):
        # Mock cache functions
        with patch("Backend.ai_services.rag.rag_service.get_cached_ai_result") as mock_get_cache, \
                patch("Backend.ai_services.rag.rag_service.cache_ai_result") as mock_set_cache, \
                patch("Backend.ai_services.rag.rag_service.ai_registry") as mock_registry, \
                patch("asyncio.get_event_loop") as mock_loop:

            mock_get_cache.return_value = None
            mock_set_cache.return_value = None
            mock_registry.get_cache_config.return_value = {
                "default_ttl": 3600,
                "ttl_per_intent": {}
            }

            # Setup mock responses
            mock_embedding = [0.1] * 384
            mock_results = {
                "ids": [["1", "2"]],
                "documents": [["doc1", "doc2"]],
                "metadatas": [[
                    {"title": "Database Schema", "source": "task_repository"},
                    {"title": "Task Workflow", "source": "knowledge_base"}
                ]],
                "distances": [[0.1, 0.2]]
            }

            # Configure mocks
            rag_service_with_mocks.embedding_service.get_embedding.return_value = mock_embedding
            rag_service_with_mocks._current_model_id = 1

            # Mock the collection's query method to fail twice then succeed
            failure_count = [0]  # Use list to allow modification in closure

            def mock_query(*args, **kwargs):
                if failure_count[0] < 2:
                    failure_count[0] += 1
                    raise Exception(f"Failure {failure_count[0]}")
                return mock_results

            # Setup the run_in_executor mock to handle retries
            async def mock_run_in_executor(executor, func):
                try:
                    result = func()
                    return result
                except Exception as e:
                    if failure_count[0] < 2:
                        # Allow retries by retrying the function
                        await asyncio.sleep(0)  # Simulate retry delay
                        return await mock_run_in_executor(executor, func)
                    return mock_results  # Return success on third try

            mock_executor = AsyncMock()
            mock_executor.run_in_executor = mock_run_in_executor
            mock_loop.return_value = mock_executor

            rag_service_with_mocks.collection.query = mock_query

            # Mock the LLM response
            rag_service_with_mocks.llm_service.generate_response.return_value = {
                "text": "Response after retries",
                "confidence": 0.8
            }

            # Test with dictionaries
            result = await rag_service_with_mocks.query_knowledge_base(
                query="test query",
                context={"key": "value"},
                filters={"type": "test"}
            )

            # Verify the result
            assert isinstance(result, dict)
            assert result.get("answer") == "Response after retries"
            assert result.get("confidence") == 0.8
            assert len(result.get("sources", [])) == 2
            assert result.get("embedding_dimension") == 384
            # Verify we had exactly 2 failures before success
            assert failure_count[0] == 2

    @pytest.mark.asyncio
    async def test_query_knowledge_base_context_window(self, rag_service_with_mocks):
        # Setup - Create results with long documents
        mock_results = {
            # Large documents
            "documents": [["Document 1" * 100, "Document 2" * 100]],
            "metadatas": [[
                {"title": "Test Doc 1", "source": "test"},
                {"title": "Test Doc 2", "source": "test"}
            ]]
        }

        # Configure mocks
        rag_service_with_mocks.embedding_service.get_embedding.return_value = [
            0.1] * 384

        # Mock the collection's query method to return the results directly
        def mock_query(*args, **kwargs):
            return mock_results

        rag_service_with_mocks.collection.query = mock_query

        # Mock cache functions
        with patch('Backend.ai_services.rag.rag_service.get_cached_ai_result', return_value=None), \
                patch('Backend.ai_services.rag.rag_service.cache_ai_result'), \
                patch('Backend.ai_services.rag.rag_service.ai_registry') as mock_registry:

            mock_registry.get_cache_config.return_value = {
                "ttl_per_intent": {},
                "default_ttl": 3600
            }

            # Mock the LLM response
            rag_service_with_mocks.llm_service.generate_response.return_value = {
                "text": "Response with context window",
                "confidence": 0.8
            }

            result = await rag_service_with_mocks.query_knowledge_base(
                query="test query",
                context={"key": "value"},
                context_window=500  # Small context window
            )
            # Verify the result
            assert isinstance(result, dict)
            assert result.get("answer") == "Response with context window"
            assert result.get("confidence") == 0.8
            assert len(result.get("sources", [])) == 2
            assert result.get("embedding_dimension") == 384

    @pytest.mark.asyncio
    async def test_add_to_knowledge_base_with_batching(self, rag_service_with_mocks):
        # Create test data
        contents = ["Document 1", "Document 2", "Document 3"]
        metadatas = [
            {"source": "test1"},
            {"source": "test2"},
            {"source": "test3"}
        ]
        # Create a success future for the add operation
        success_future = create_mock_future(None)
        rag_service_with_mocks.collection.add.return_value = success_future

        # Test adding documents
        result = await rag_service_with_mocks.add_to_knowledge_base(
            content=contents,
            metadata=metadatas,
            batch_size=2
        )

        assert result is True
        # Should be called twice with batch_size=2
        assert rag_service_with_mocks.collection.add.call_count == 2

    @pytest.mark.asyncio
    async def test_model_initialization(self, rag_service_with_mocks, mock_model_repository):
        # Test model initialization
        model_id = await rag_service_with_mocks._get_or_create_model()
        assert model_id == 1
        rag_service_with_mocks.model_repository.get_model_by_name_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_model_stats_update(self, rag_service_with_mocks):
        # Test model stats update
        rag_service_with_mocks._current_model_id = 1
        await rag_service_with_mocks._update_model_stats(0.5, True)
        rag_service_with_mocks.model_repository.update_model_stats.assert_called_once_with(
            1, 0.5, True)

    @pytest.mark.asyncio
    async def test_query_knowledge_base_with_model_tracking(
        self,
        rag_service_with_mocks,
        mock_model_repository
    ):
        # Setup
        with patch("Backend.ai_services.rag.rag_service.get_cached_ai_result") as mock_get_cache, \
                patch("Backend.ai_services.rag.rag_service.cache_ai_result") as mock_set_cache, \
                patch("Backend.ai_services.rag.rag_service.ai_registry") as mock_registry, \
                patch("asyncio.get_event_loop") as mock_loop:

            mock_get_cache.return_value = None
            mock_set_cache.return_value = None
            mock_registry.get_cache_config.return_value = {
                "ttl_per_intent": {},
                "default_ttl": 3600
            }

            # Mock embedding service
            rag_service_with_mocks.embedding_service.get_embedding.return_value = [
                0.1] * 384

            mock_results = {
                "ids": [["1", "2"]],
                "documents": [["doc1", "doc2"]],
                "metadatas": [[{"title": "Test1"}, {"title": "Test2"}]],
                "distances": [[0.1, 0.2]]
            }

            def mock_query(*args, **kwargs):
                return mock_results

            # Setup the run_in_executor mock
            mock_executor = AsyncMock()
            mock_executor.run_in_executor.side_effect = lambda executor, func: func()
            mock_loop.return_value = mock_executor

            rag_service_with_mocks.collection.query = mock_query
            rag_service_with_mocks._current_model_id = 1

            # Mock LLM response
            rag_service_with_mocks.llm_service.generate_response.return_value = {
                "text": "Test response",
                "confidence": 0.8
            }

            # Execute
            result = await rag_service_with_mocks.query_knowledge_base(
                query="test query",
                context={"key": "value"}
            )

            # Verify
            assert isinstance(result, dict)
            assert result.get("answer") == "Test response"
            assert len(result.get("sources", [])) == 2
            rag_service_with_mocks.model_repository.update_model_stats.assert_called_with(
                1, ANY, True)

    
def create_mock_future(result=None, exception=None):
    future = Future()
    if exception:
        future.set_exception(exception)
    else:
        future.set_result(result)
    return future


if __name__ == "__main__":
    pytest.main(["-v", "test_rag_service.py"])
