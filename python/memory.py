from qdrant_client import QdrantClient
from .embedding_model import EmbeddingModel

class QdrantMemory:
    def __init__(self):
        self.client = QdrantClient("localhost", port=6333)
        self.embedding_model = EmbeddingModel.get_instance()

    def store_context(self, text: str, context_id: str, payload: dict):
        # Generate embedding for the text
        embedding = self.embedding_model.embed(text)

        # Simplified: upsert to collection with embedding
        # In real implementation, you'd specify collection name and handle the upsert
        print(f"Storing context '{text[:50]}...' with embedding of length {len(embedding)}")

    def search_similar(self, query: str, limit: int = 5):
        # Generate embedding for query
        query_embedding = self.embedding_model.embed(query)

        # Simplified: search in collection
        # In real implementation, you'd perform vector search
        print(f"Searching for similar contexts to '{query}' with embedding of length {len(query_embedding)}")
        return []