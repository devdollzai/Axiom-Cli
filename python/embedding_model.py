from sentence_transformers import SentenceTransformer
from typing import Union, List
import hashlib

class EmbeddingModel:
    _instance = None
    _cache = {}
    CACHE_SIZE = 1000

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'model'):
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def _manage_cache_size(self):
        if len(self._cache) > self.CACHE_SIZE:
            # Remove oldest entries (simple FIFO)
            items_to_remove = len(self._cache) - self.CACHE_SIZE
            for key in list(self._cache.keys())[:items_to_remove]:
                del self._cache[key]

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        if isinstance(text, str):
            # Single text
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]
            embedding = self.model.encode(text).tolist()
            self._cache[cache_key] = embedding
            self._manage_cache_size()
            return embedding
        else:
            # Batch processing
            embeddings = []
            uncached_texts = []
            uncached_indices = []

            for i, t in enumerate(text):
                cache_key = self._get_cache_key(t)
                if cache_key in self._cache:
                    embeddings.append(self._cache[cache_key])
                else:
                    embeddings.append(None)  # Placeholder
                    uncached_texts.append(t)
                    uncached_indices.append(i)

            if uncached_texts:
                batch_embeddings = self.model.encode(uncached_texts).tolist()
                for idx, embedding in zip(uncached_indices, batch_embeddings):
                    cache_key = self._get_cache_key(text[idx])
                    self._cache[cache_key] = embedding
                    embeddings[idx] = embedding

            self._manage_cache_size()
            return embeddings

    @classmethod
    def get_instance(cls):
        return cls()