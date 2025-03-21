from Backend.data_layer.vector_db.chroma_client import ChromaClient
from Backend.ai_services.rag.rag_service import RAGService
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
from pathlib import Path
import asyncio
import json
import hashlib
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
import chromadb
from chromadb.api.models.Collection import Collection
from Backend.ai_services.rag.rag_service import RAGService
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.ai_services.llm.llm_service import LLMService

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Backend directory
sys.path.insert(0, str(project_root.parent))  # COMPASS directory

# Import after path setup

# Test data
MOCK_QUERY = "How do I complete my current tasks?"
MOCK_CONTEXT = {"tasks": [{"title": "Design database schema", "status": "pending"}]}
MOCK_FILTERS = {"metadata_field": "value"}
MOCK_USER_ID = 123

MOCK_EMBEDDING = [0.1, 0.2, 0.3, 0.4, 0.5]  # Simple mock embedding

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


class TestRAGService:
    
    @pytest.fixture
    def mock_chroma_client(self):
        client = MagicMock()
        collection = MagicMock(spec=Collection)
        collection.query.return_value = MOCK_CHROMA_RESULTS
        collection.count.return_value = 10
        collection.name = "test_collection"
        collection.add = MagicMock(side_effect=lambda **kwargs: None)
        collection.update = MagicMock(side_effect=lambda **kwargs: None)
        collection.delete = MagicMock(side_effect=lambda **kwargs: None)
        client.collection = collection
        client.get_collection = MagicMock(return_value=collection)
        client.create_collection = MagicMock(return_value=collection)
        return client
    
    @pytest.fixture
    def mock_embedding_service(self):
        embedding_service = MagicMock(spec=EmbeddingService)
        # Return flat list for single items, list of lists for multiple items
        embedding_service.get_embedding = AsyncMock(side_effect=lambda x, **kwargs: 
            MOCK_EMBEDDING if isinstance(x, str) else 
            [MOCK_EMBEDDING] if isinstance(x, list) and len(x) == 1 else 
            [MOCK_EMBEDDING for _ in x]
        )
        embedding_service.dimension = len(MOCK_EMBEDDING)
        return embedding_service
    
    @pytest.fixture
    def mock_llm_service(self):
        llm_service = MagicMock(spec=LLMService)
        llm_service.generate_response = AsyncMock(return_value=MOCK_LLM_RESPONSE)
        return llm_service
    
    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client for the cache functions."""
        mock_redis = AsyncMock()
        # Set return value for get as a string (redis returns strings)
        mock_redis.get.return_value = None  # Default to cache miss
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = True
        return mock_redis
    
    @pytest.fixture
    def rag_service_with_mocks(self, mock_chroma_client, mock_embedding_service, mock_llm_service, mock_redis_client):
        # Create patches that will affect the imported modules
        redis_patch = patch('Backend.data_layer.cache.redis_client.redis_client', mock_redis_client)
        
        # Start all patches
        redis_patch.start()
        
        # Create direct patches for the cache functions
        cache_get_patch = patch('Backend.ai_services.rag.rag_service.get_cached_ai_result')
        cache_set_patch = patch('Backend.ai_services.rag.rag_service.cache_ai_result')
        
        # Start these patches and obtain the mocks
        mock_get_cached = cache_get_patch.start()
        mock_set_cached = cache_set_patch.start()
        
        # Set default return value for get_cached_ai_result
        mock_get_cached.return_value = None  # Default to cache miss
        
        # Create ChromaDB patch
        chroma_patch = patch('Backend.ai_services.rag.rag_service.ChromaClient', return_value=mock_chroma_client)
        embedding_patch = patch('Backend.ai_services.rag.rag_service.EmbeddingService', return_value=mock_embedding_service)
        llm_patch = patch('Backend.ai_services.rag.rag_service.LLMService', return_value=mock_llm_service)
        
        # Start these patches
        chroma_patch.start()
        embedding_patch.start()
        llm_patch.start()
        
        # Create service instance
        rag_service = RAGService()
        
        # Replace the service's dependencies with our mocks
        rag_service.chroma_client = mock_chroma_client
        rag_service.client = mock_chroma_client
        rag_service.collection = mock_chroma_client.collection
        rag_service.embedding_service = mock_embedding_service
        rag_service.llm_service = mock_llm_service
        
        # Store mocks in the service instance for assertions in tests
        rag_service.mock_get_cached = mock_get_cached
        rag_service.mock_set_cached = mock_set_cached
        rag_service.redis_client = mock_redis_client
        
        # Yield the service for use in tests
        yield rag_service
        
        # Stop all patches after test completion
        redis_patch.stop()
        cache_get_patch.stop()
        cache_set_patch.stop()
        chroma_patch.stop()
        embedding_patch.stop()
        llm_patch.stop()
    
    # Test the cache key generation
    def test_generate_cache_key(self, rag_service_with_mocks):
        # Setup
        query = MOCK_QUERY
        context = MOCK_CONTEXT
        filters = MOCK_FILTERS
        
        # Execute
        cache_key = rag_service_with_mocks._generate_cache_key(query, context, filters)
        
        # Verify
        expected_input = json.dumps({"query": query, "context": context, "filters": filters}, sort_keys=True)
        expected_key = f"rag_query:{hashlib.sha256(expected_input.encode()).hexdigest()}"
        
        assert cache_key == expected_key
    
    # Test the full query_knowledge_base workflow (no cache hit)
    async def test_query_knowledge_base_full_workflow(self, rag_service_with_mocks):
        # Setup registry mock directly in the test
        with patch('Backend.ai_services.rag.rag_service.ai_registry') as mock_ai_registry:
            # Provide a complete cache configuration that matches expected structure
            mock_ai_registry.get_cache_config.return_value = {
                "enabled": True,
                "default_ttl": 3600,
                "ttl_per_intent": {
                    "retrieve": 1800,
                    "analyze": 7200,
                    "summarize": 14400,
                    "plan": 10800
                }
            }
            
            # Ensure cache miss for this test
            rag_service_with_mocks.mock_get_cached.return_value = None
            
            # Execute query_knowledge_base
            result = await rag_service_with_mocks.query_knowledge_base(
                query=MOCK_QUERY,
                context=MOCK_CONTEXT,
                intent="retrieve",
                user_id=MOCK_USER_ID
            )
            
            # Verify cache check was performed
            rag_service_with_mocks.mock_get_cached.assert_called_once()
            
            # Verify embedding generation was called
            rag_service_with_mocks.embedding_service.get_embedding.assert_called_once_with(
                MOCK_QUERY, normalize=True
            )
            
            # Verify query to collection was made
            rag_service_with_mocks.collection.query.assert_called_once_with(
                query_embeddings=[MOCK_EMBEDDING],  # Single flat list
                n_results=8,
                where=None
            )
            
            # Verify the LLM was called with the expected prompt
            rag_service_with_mocks.llm_service.generate_response.assert_called_once()
            prompt_arg = rag_service_with_mocks.llm_service.generate_response.call_args[1]['prompt']
            assert MOCK_QUERY in prompt_arg, "Query should be in the prompt"
            
            # Verify cache_ai_result was called
            rag_service_with_mocks.mock_set_cached.assert_called_once()
            
            # Verify result structure
            assert "answer" in result, "Result should contain 'answer' key"
            assert "sources" in result, "Result should contain 'sources' key"
            assert "confidence" in result, "Result should contain 'confidence' key"
            assert "embedding_dimension" in result, "Result should contain 'embedding_dimension' key"
            assert result["answer"] == MOCK_LLM_RESPONSE["text"], "Result answer should match mock response text"
            assert result["confidence"] == MOCK_LLM_RESPONSE.get("confidence", 0.0), "Result confidence should match mock response confidence"
            assert len(result["sources"]) == 2, "Result should contain 2 sources"
    
    # Test the workflow with a cache hit
    async def test_query_knowledge_base_with_cache_hit(self, rag_service_with_mocks):
        # Setup mock for cache hit
        rag_service_with_mocks.mock_get_cached.return_value = MOCK_CACHED_RESULT
        
        # Setup registry mock
        with patch('Backend.ai_services.rag.rag_service.ai_registry') as mock_ai_registry:
            mock_ai_registry.get_cache_config.return_value = {
                "enabled": True,
                "default_ttl": 3600,
                "ttl_per_intent": {}
            }
            
            # Execute query_knowledge_base
            result = await rag_service_with_mocks.query_knowledge_base(
                query=MOCK_QUERY,
                context=MOCK_CONTEXT
            )
            
            # Verify get_cached_ai_result was called (not Redis directly)
            rag_service_with_mocks.mock_get_cached.assert_called_once()
            
            # Embedding generation should not be called on cache hit
            rag_service_with_mocks.embedding_service.get_embedding.assert_not_called()
            
            # LLM should not be called on cache hit
            rag_service_with_mocks.llm_service.generate_response.assert_not_called()
            
            # Verify result matches cached result
            assert result == MOCK_CACHED_RESULT
    
    # Test handling empty query results
    async def test_query_knowledge_base_with_empty_results(self, rag_service_with_mocks):
        # Setup mock to return empty results
        rag_service_with_mocks.collection.query.return_value = MOCK_EMPTY_CHROMA_RESULTS
        
        # Ensure cache miss
        rag_service_with_mocks.mock_get_cached.return_value = None
        
        # Setup registry mock
        with patch('Backend.ai_services.rag.rag_service.ai_registry') as mock_ai_registry:
            mock_ai_registry.get_cache_config.return_value = {
                "enabled": True,
                "default_ttl": 3600,
                "ttl_per_intent": {}
            }
            
            # Execute query_knowledge_base
            result = await rag_service_with_mocks.query_knowledge_base(
                query=MOCK_QUERY,
                context=MOCK_CONTEXT
            )
        
        # Verify embedding was still generated
        rag_service_with_mocks.embedding_service.get_embedding.assert_called_once()
        
        # Verify query was attempted
        rag_service_with_mocks.collection.query.assert_called_once()
        
        # For empty results, LLM should NOT be called
        rag_service_with_mocks.llm_service.generate_response.assert_not_called()
        
        # Verify standard empty result format
        assert result["answer"] == "No relevant information found in the knowledge base."
        assert result["sources"] == []
        assert result["confidence"] == 0.0
    
    # Test error handling in query_knowledge_base
    async def test_query_knowledge_base_error_handling(self, rag_service_with_mocks):
        # Setup mock to raise exception
        rag_service_with_mocks.collection.query.side_effect = Exception("Database error")
        
        # Ensure cache miss
        rag_service_with_mocks.mock_get_cached.return_value = None
        
        # Setup registry mock
        with patch('Backend.ai_services.rag.rag_service.ai_registry') as mock_ai_registry:
            mock_ai_registry.get_cache_config.return_value = {
                "enabled": True,
                "default_ttl": 3600,
                "ttl_per_intent": {}
            }
            
            # Execute query_knowledge_base
            result = await rag_service_with_mocks.query_knowledge_base(
                query=MOCK_QUERY,
                context=MOCK_CONTEXT
            )
        
        # Verify error response format
        assert result["answer"] == "Error querying the knowledge base."
        assert result["sources"] == []
        assert result["confidence"] == 0.0
        assert "error" in result
        assert "Database error" in result["error"]
    
    # Test add_to_knowledge_base with single item
    async def test_add_to_knowledge_base_single_item(self, rag_service_with_mocks):
        # Setup
        content = "This is a single document"
        metadata = {"title": "Test Document", "source": "unit_test"}
        
        # Reset mocks to ensure clean state
        rag_service_with_mocks.collection.add.reset_mock()
        rag_service_with_mocks.embedding_service.get_embedding.reset_mock()
        
        # Execute with the properly mocked service
        result = await rag_service_with_mocks.add_to_knowledge_base(content, metadata)
        
        # Verify embedding was generated
        rag_service_with_mocks.embedding_service.get_embedding.assert_called_once_with(
            [content], normalize=True, batch_size=32
        )
        
        # Generate expected ID
        expected_id = f"doc_0_{hash(content)}"
        
        # Verify document was added to collection with correct arguments
        rag_service_with_mocks.collection.add.assert_called_once_with(
            embeddings=[MOCK_EMBEDDING],  # Single flat list
            documents=[content],
            metadatas=[metadata],
            ids=[expected_id]
        )
        
        # Function should return True on success
        assert result is True
    
    # Test add_to_knowledge_base with multiple items
    async def test_add_to_knowledge_base_multiple_items(self, rag_service_with_mocks):
        # Setup
        contents = ["Document 1", "Document 2", "Document 3"]
        metadatas = [
            {"title": "Doc 1", "source": "test"}, 
            {"title": "Doc 2", "source": "test"}, 
            {"title": "Doc 3", "source": "test"}
        ]
        
        # Reset mocks to ensure clean state
        rag_service_with_mocks.collection.add.reset_mock()
        rag_service_with_mocks.embedding_service.get_embedding.reset_mock()
        
        # Execute with the properly mocked service
        result = await rag_service_with_mocks.add_to_knowledge_base(contents, metadatas)
        
        # Verify embedding was generated for all items
        rag_service_with_mocks.embedding_service.get_embedding.assert_called_once_with(
            contents, normalize=True, batch_size=32
        )
        
        # Generate expected IDs
        expected_ids = [f"doc_{i}_{hash(content)}" for i, content in enumerate(contents)]
        
        # Verify documents were added to collection with correct arguments
        rag_service_with_mocks.collection.add.assert_called_once_with(
            embeddings=[MOCK_EMBEDDING for _ in contents],  # List of flat lists
            documents=contents,
            metadatas=metadatas,
            ids=expected_ids
        )
        
        # Function should return True on success
        assert result is True
    
    # Test update_document
    async def test_update_document(self, rag_service_with_mocks):
        # Setup
        doc_id = "doc123"
        content = "Updated document content"
        metadata = {"title": "Updated Document", "source": "test"}
        
        # Execute
        result = await rag_service_with_mocks.update_document(doc_id, content, metadata)
        
        # Verify embedding was generated
        rag_service_with_mocks.embedding_service.get_embedding.assert_called_once_with(
            content, normalize=True
        )
        
        # Verify document was updated
        rag_service_with_mocks.collection.update.assert_called_once_with(
            ids=[doc_id],
            embeddings=[MOCK_EMBEDDING],  # Single flat list
            documents=[content],
            metadatas=[metadata]
        )
        
        # Function should return True on success
        assert result is True
    
    # Test delete_document
    async def test_delete_document(self, rag_service_with_mocks):
        # Setup
        doc_id = "doc123"
        
        # Execute
        result = await rag_service_with_mocks.delete_document(doc_id)
        
        # Verify document was deleted
        rag_service_with_mocks.collection.delete.assert_called_once_with(ids=[doc_id])
        
        # Function should return True on success
        assert result is True
    
    # Test get_collection_stats
    async def test_get_collection_stats(self, rag_service_with_mocks):
        # Execute
        result = await rag_service_with_mocks.get_collection_stats()
        
        # Verify collection.count was called
        rag_service_with_mocks.collection.count.assert_called_once()
        
        # Verify result structure
        assert "count" in result
        assert "dimension" in result
        assert "name" in result
        assert result["count"] == 10
        assert result["dimension"] == len(MOCK_EMBEDDING)
    
    # Test collection not initialized error handling
    async def test_query_knowledge_base_with_no_collection(self):
        # Create a mock client with no collection
        mock_client = MagicMock()
        mock_client.collection = None
        
        # Create a mock Redis client
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        # Create mock for get_cached_ai_result
        mock_get_cached = AsyncMock(return_value=None)
        
        # Create RAG service with no collection
        with patch('Backend.ai_services.rag.rag_service.ChromaClient', return_value=mock_client):
            with patch('Backend.data_layer.cache.redis_client.redis_client', mock_redis):
                with patch('Backend.ai_services.rag.rag_service.get_cached_ai_result', mock_get_cached):
                    with patch('Backend.ai_services.rag.rag_service.ai_registry') as mock_ai_registry:
                        mock_ai_registry.get_cache_config.return_value = {
                            "enabled": True,
                            "default_ttl": 3600,
                            "ttl_per_intent": {}
                        }
                        
                        rag_service = RAGService()
                        rag_service.client = mock_client
                        rag_service.collection = None
                        
                        # Execute with no collection
                        result = await rag_service.query_knowledge_base(MOCK_QUERY, MOCK_CONTEXT)
                        
                        # Verify error response 
                        # Accept either error message format since they're both valid
                        assert "error" in result
                        error_message = result["error"]
                        assert "Knowledge base not initialized" in error_message or "ChromaDB collection not initialized" in error_message
                        assert result["sources"] == []
                        assert result["confidence"] == 0.0


if __name__ == "__main__":
    # Updated to use pytest directly
    pytest.main(["-xvs", __file__])
