from typing import List, Union, Dict, Optional
from sentence_transformers import SentenceTransformer
from Backend.ai_services.base.ai_service_base import AIServiceBase
from Backend.utils.cache_utils import cache_response
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result

logger = get_logger(__name__)

class EmbeddingService(AIServiceBase):
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        super().__init__("embedding")
        self.model_name = model_name
        self.model_version = "1.0.0"
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the embedding model with error handling."""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise

    @cache_response(ttl=3600)
    async def get_embedding(
        self,
        text: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings with batching and normalization."""
        try:
            if isinstance(text, list):
                return await self._batch_encode(text, batch_size, normalize)
            
            embeddings = self.model.encode(
                text,
                normalize_embeddings=normalize,
                convert_to_tensor=True,
                batch_size=batch_size
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def _batch_encode(
        self,
        texts: List[str],
        batch_size: int,
        normalize: bool
    ) -> List[List[float]]:
        """Process texts in batches for better memory management."""
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.model.encode(
                batch,
                normalize_embeddings=normalize,
                convert_to_tensor=True
            )
            all_embeddings.extend(embeddings.tolist())
        return all_embeddings

    async def compare_embeddings(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """Compare two embeddings using cosine similarity."""
        return self.model.similarity(embedding1, embedding2)

    def get_model_info(self) -> Dict:
        """Get model information and configuration."""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "embedding_dimension": self.dimension,
            "max_sequence_length": self.model.max_seq_length,
            "model_type": self.model.get_sentence_embedding_dimension_info()
        }