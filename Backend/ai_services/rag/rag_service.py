import chromadb
from sentence_transformers import SentenceTransformer
import os

class RAGService:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.chroma_store_path = os.path.join(self.script_dir, "chroma_store")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_store_path)
        self.collection = self.chroma_client.get_collection("knowledge_base")

    async def get_relevant_context(self, query: str, n_results: int = 3) -> str:
        """
        Get relevant context from ChromaDB based on the query.
        
        Args:
            query: The user's query
            n_results: Number of relevant chunks to retrieve
            
        Returns:
            A string containing the relevant context
        """
        # Generate embedding for the query
        query_embedding = self.embedder.encode(query).tolist()
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas"]
        )
        
        # Format the results into a context string
        context_chunks = []
        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
            source = metadata.get('source', 'Unknown')
            context_chunks.append(f"From {source}:\n{doc}\n")
            
        return "\n".join(context_chunks)

    def get_sources_used(self, query: str, n_results: int = 3) -> list:
        """
        Get the sources of the documents used for context.
        
        Args:
            query: The user's query
            n_results: Number of relevant chunks to retrieve
            
        Returns:
            List of source filenames used
        """
        query_embedding = self.embedder.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas"]
        )
        
        sources = [meta.get('source', 'Unknown') for meta in results['metadatas'][0]]
        return list(set(sources))  # Remove duplicates 