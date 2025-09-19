from qdrant_client import QdrantClient

class QdrantMemory:
    def __init__(self):
        self.client = QdrantClient("localhost", port=6333)

    def store_context(self, text: str, context_id: str, payload: dict):
        # Simplified: upsert to collection
        pass