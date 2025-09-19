from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from .embedding_model import EmbeddingModel
import uuid

class QdrantMemory:
    def __init__(self, collection_name="sovereign_memory"):
        self.client = QdrantClient("localhost", port=6333)
        self.embedding_model = EmbeddingModel.get_instance()
        self.collection_name = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
        except:
            # Collection doesn't exist, create it
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"Created Qdrant collection: {self.collection_name}")

    def store_context(self, text: str, context_id: str, payload: dict):
        """Store context with embedding in Qdrant"""
        try:
            # Generate embedding for the text
            embedding = self.embedding_model.embed(text)

            # Prepare point for upsert
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": text,
                    "context_id": context_id,
                    **payload
                }
            )

            # Upsert to collection
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            print(f"Stored context '{text[:50]}...' with ID {point.id}")
        except Exception as e:
            print(f"Failed to store context: {e}")

    def search_similar(self, query: str, limit: int = 5):
        """Search for similar contexts using vector similarity"""
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.embed(query)

            # Perform vector search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )

            # Extract results
            results = []
            for hit in search_result:
                results.append({
                    "text": hit.payload.get("text", ""),
                    "context_id": hit.payload.get("context_id", ""),
                    "score": hit.score,
                    "payload": hit.payload
                })

            print(f"Found {len(results)} similar contexts for query '{query[:50]}...'")
            return results
        except Exception as e:
            print(f"Failed to search contexts: {e}")
            return []