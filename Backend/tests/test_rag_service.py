from Backend.data_layer.vector_db.chroma_client import ChromaClient
from Backend.ai_services.rag.rag_service import RAGService
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
from pathlib import Path
import asyncio

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Backend directory
sys.path.insert(0, str(project_root.parent))  # COMPASS directory

# Import after path setup


@pytest.fixture
def mock_chroma_client():
    """Create a mock ChromaDB client."""
    mock_client = MagicMock()
    mock_collection = MagicMock()

    # Setup mock collection methods
    mock_collection.query.return_value = {
        "documents": [["Document 1", "Document 2"]],
        "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
        "distances": [[0.1, 0.2]],
        "ids": [["id1", "id2"]]
    }

    mock_collection.add.return_value = None
    mock_collection.update.return_value = None
    mock_collection.delete.return_value = None
    mock_collection.count.return_value = 10
    mock_collection.name = "test_collection"

    # Setup mock client
    mock_client.client = MagicMock()
    mock_client.collection = mock_collection

    return mock_client


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    mock_llm = AsyncMock()

    async def mock_generate_response(*args, **kwargs):
        return {
            "text": "This is a mock response from the LLM service.",
            "confidence": 0.95
        }

    mock_llm.generate_response = AsyncMock(side_effect=mock_generate_response)
    return mock_llm


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    mock_embedding = AsyncMock()

    async def mock_get_embedding(*args, **kwargs):
        # Return a simple mock embedding vector
        return [0.1, 0.2, 0.3, 0.4, 0.5]

    mock_embedding.get_embedding = AsyncMock(side_effect=mock_get_embedding)
    mock_embedding.dimension = 5
    return mock_embedding


@pytest.mark.asyncio
async def test_rag_service_query(mock_chroma_client, mock_llm_service, mock_embedding_service):
    """Test querying the RAG service with mocked dependencies."""
    with patch('Backend.ai_services.rag.rag_service.ChromaClient', return_value=mock_chroma_client):
        # Create RAG service with mocked dependencies
        rag_service = RAGService()
        rag_service.llm_service = mock_llm_service
        rag_service.embedding_service = mock_embedding_service

        # Test query_knowledge_base
        result = await rag_service.query_knowledge_base("Test query")

        # Verify the result
        assert "answer" in result
        assert result["answer"] == "This is a mock response from the LLM service."
        assert "sources" in result
        assert len(result["sources"]) == 2
        assert "confidence" in result
        assert result["confidence"] == 0.95


@pytest.mark.asyncio
async def test_rag_service_add_document(mock_chroma_client, mock_embedding_service):
    """Test adding a document to the RAG service with mocked dependencies."""
    with patch('Backend.ai_services.rag.rag_service.ChromaClient', return_value=mock_chroma_client):
        # Create RAG service with mocked dependencies
        rag_service = RAGService()
        rag_service.embedding_service = mock_embedding_service

        # Test add_to_knowledge_base
        result = await rag_service.add_to_knowledge_base(
            content="Test document",
            metadata={"source": "test"}
        )

        # Verify the result
        assert result is True
        mock_chroma_client.collection.add.assert_called_once()


@pytest.mark.asyncio
async def test_rag_service_delete_document(mock_chroma_client):
    """Test deleting a document from the RAG service with mocked dependencies."""
    with patch('Backend.ai_services.rag.rag_service.ChromaClient', return_value=mock_chroma_client):
        # Create RAG service with mocked dependencies
        rag_service = RAGService()

        # Test delete_document
        result = await rag_service.delete_document("test_id")

        # Verify the result
        assert result is True
        mock_chroma_client.collection.delete.assert_called_once_with(ids=[
                                                                     "test_id"])


@pytest.mark.asyncio
async def test_rag_service_get_stats(mock_chroma_client, mock_embedding_service):
    """Test getting collection stats from the RAG service with mocked dependencies."""
    with patch('Backend.ai_services.rag.rag_service.ChromaClient', return_value=mock_chroma_client):
        # Create RAG service with mocked dependencies
        rag_service = RAGService()
        rag_service.embedding_service = mock_embedding_service

        # Test get_collection_stats
        result = await rag_service.get_collection_stats()

        # Verify the result
        assert "count" in result
        assert result["count"] == 10
        assert "dimension" in result
        assert result["dimension"] == 5
        assert "name" in result
        assert result["name"] == "test_collection"


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
