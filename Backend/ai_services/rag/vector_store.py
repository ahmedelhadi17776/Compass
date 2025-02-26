from typing import List, Dict
from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.vector_db.chroma_client import chroma_client

logger = get_logger(__name__)

class VectorStore:
    def __init__(self):
        # Use the centralized ChromaClient instance
        self.client = chroma_client.client
        self.collection = chroma_client.collection

    async def add_task_embedding(self, task_id: str, embedding: List[float], metadata: Dict):
        """Add task embedding to ChromaDB."""
        try:
            self.collection.add(
                embeddings=[embedding],
                documents=[metadata.get("description", "")],
                metadatas=[metadata],
                ids=[str(task_id)]
            )
            return True
        except Exception as e:
            logger.error(f"Error adding task embedding: {str(e)}")
            return False

    async def find_similar_tasks(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Find similar tasks using vector similarity."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            return [
                {
                    "id": result_id,
                    "metadata": metadata,
                    "distance": distance
                }
                for result_id, metadata, distance in zip(
                    results["ids"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
        except Exception as e:
            logger.error(f"Error querying similar tasks: {str(e)}")
            return []