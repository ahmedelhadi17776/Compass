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
        client.collection = collection
        return client
    
    @pytest.fixture
    def mock_embedding_service(self):
        embedding_service = MagicMock(spec=EmbeddingService)
        embedding_service.get_embedding = AsyncMock(return_value=MOCK_EMBEDDING)
        embedding_service.dimension = len(MOCK_EMBEDDING)
        return embedding_service
    
    @pytest.fixture
    def mock_llm_service(self):
        llm_service = MagicMock(spec=LLMService)
        llm_service.generate_response = AsyncMock(return_value=MOCK_LLM_RESPONSE)
        return llm_service
    
    @pytest.fixture
    def rag_service_with_mocks(self, mock_chroma_client, mock_embedding_service, mock_llm_service):
        with patch('Backend.ai_services.rag.rag_service.ChromaClient', return_value=mock_chroma_client):
            with patch('Backend.ai_services.rag.rag_service.EmbeddingService', return_value=mock_embedding_service):
                with patch('Backend.ai_services.rag.rag_service.LLMService', return_value=mock_llm_service):
                    rag_service = RAGService()
                    rag_service.client = mock_chroma_client
                    rag_service.collection = mock_chroma_client.collection
                    rag_service.embedding_service = mock_embedding_service
                    rag_service.llm_service = mock_llm_service
                    return rag_service
    
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
    @patch('Backend.ai_services.rag.rag_service.get_cached_ai_result')
    @patch('Backend.ai_services.rag.rag_service.cache_ai_result')
    @patch('Backend.ai_services.rag.rag_service.ai_registry')
    async def test_query_knowledge_base_full_workflow(self, mock_ai_registry, 
                                                     mock_cache_result, 
                                                     mock_get_cache,
                                                     rag_service_with_mocks):
        # Setup mocks
        mock_get_cache.return_value = None  # Cache miss
        mock_ai_registry.get_cache_config.return_value = {
            "ttl_per_intent": {"retrieve": 1800, "default_ttl": 3600}
        }
        
        # Execute query_knowledge_base
        result = await rag_service_with_mocks.query_knowledge_base(
            query=MOCK_QUERY,
            context=MOCK_CONTEXT,
            intent="retrieve",
            user_id=MOCK_USER_ID
        )
        
        # Verify workflow steps
        mock_get_cache.assert_called_once()
        rag_service_with_mocks.embedding_service.get_embedding.assert_called_once_with(
            MOCK_QUERY, normalize=True
        )
        rag_service_with_mocks.collection.query.assert_called_once_with(
            query_embeddings=[MOCK_EMBEDDING],
            n_results=8,
            where=None
        )
        rag_service_with_mocks.llm_service.generate_response.assert_called_once()
        mock_cache_result.assert_called_once()
        
        # Verify result structure
        assert "answer" in result
        assert "sources" in result
        assert "confidence" in result
        assert "embedding_dimension" in result
        assert result["answer"] == MOCK_LLM_RESPONSE["text"]
        assert result["confidence"] == MOCK_LLM_RESPONSE.get("confidence", 0.0)
        assert len(result["sources"]) == 2
    
    # Test the workflow with a cache hit
    @patch('Backend.ai_services.rag.rag_service.get_cached_ai_result')
    async def test_query_knowledge_base_with_cache_hit(self, mock_get_cache, rag_service_with_mocks):
        # Setup mock for cache hit
        mock_get_cache.return_value = MOCK_CACHED_RESULT
        
        # Execute query_knowledge_base
        result = await rag_service_with_mocks.query_knowledge_base(
            query=MOCK_QUERY,
            context=MOCK_CONTEXT
        )
        
        # Verify cache was checked and workflow stopped after cache hit
        mock_get_cache.assert_called_once()
        
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
        
        # Setup cache miss
        with patch('Backend.ai_services.rag.rag_service.get_cached_ai_result', return_value=None):
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
        
        # Setup cache miss
        with patch('Backend.ai_services.rag.rag_service.get_cached_ai_result', return_value=None):
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
        
        # Execute
        result = await rag_service_with_mocks.add_to_knowledge_base(content, metadata)
        
        # Verify embedding was generated
        rag_service_with_mocks.embedding_service.get_embedding.assert_called_once_with(
            [content], normalize=True, batch_size=32
        )
        
        # Verify document was added to collection
        rag_service_with_mocks.collection.add.assert_called_once()
        
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
        
        # Execute
        result = await rag_service_with_mocks.add_to_knowledge_base(contents, metadatas)
        
        # Verify embedding was generated for all items
        rag_service_with_mocks.embedding_service.get_embedding.assert_called_once_with(
            contents, normalize=True, batch_size=32
        )
        
        # Verify documents were added to collection
        rag_service_with_mocks.collection.add.assert_called_once()
        
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
            embeddings=[MOCK_EMBEDDING],
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
        # Create RAG service with no collection
        with patch('Backend.ai_services.rag.rag_service.ChromaClient') as mock_chroma_client:
            mock_chroma_client.return_value.collection = None
            
            rag_service = RAGService()
            
            # Execute with no collection
            result = await rag_service.query_knowledge_base(MOCK_QUERY, MOCK_CONTEXT)
            
            # Verify error response
            assert "error" in result
            assert "Knowledge base not initialized" in result["answer"]
            assert result["sources"] == []
            assert result["confidence"] == 0.0


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_rag_service_query(mock_chroma_client(),
                mock_llm_service(), mock_embedding_service()))
    asyncio.run(test_rag_service_add_document(
        mock_chroma_client(), mock_embedding_service()))
    asyncio.run(test_rag_service_delete_document(mock_chroma_client()))
    asyncio.run(test_rag_service_get_stats(
        mock_chroma_client(), mock_embedding_service()))
    print("All RAG service tests passed!")
