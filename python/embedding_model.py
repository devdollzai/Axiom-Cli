from sentence_transformers import SentenceTransformer
from typing import Union, List
import hashlib
import json
import os
import asyncio

class EmbeddingModel:
    _instance = None
    _cache = {}
    CACHE_SIZE = 1000
    CACHE_FILE = "embedding_cache.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'model'):
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self._load_cache()

    def _load_cache(self):
        """Load cache from disk if exists"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    self._cache = json.load(f)
                print(f"Loaded {len(self._cache)} cached embeddings from disk")
            except Exception as e:
                print(f"Failed to load embedding cache: {e}")

    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(self._cache, f)
        except Exception as e:
            print(f"Failed to save embedding cache: {e}")

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def _manage_cache_size(self):
        if len(self._cache) > self.CACHE_SIZE:
            # Remove oldest entries (simple FIFO)
            items_to_remove = len(self._cache) - self.CACHE_SIZE
            for key in list(self._cache.keys())[:items_to_remove]:
                del self._cache[key]
        # Save cache periodically
        if len(self._cache) % 50 == 0:
            self._save_cache()

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Synchronous embed method"""
        return asyncio.run(self.aembed(text))

    async def aembed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Asynchronous embed method"""
        if isinstance(text, str):
            # Single text
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]
            # Run encoding in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, self.model.encode, text)
            embedding = embedding.tolist()
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
                # Run batch encoding in thread pool
                loop = asyncio.get_event_loop()
                batch_embeddings = await loop.run_in_executor(None, self.model.encode, uncached_texts)
                batch_embeddings = batch_embeddings.tolist()
                for idx, embedding in zip(uncached_indices, batch_embeddings):
                    cache_key = self._get_cache_key(text[idx])
                    self._cache[cache_key] = embedding
                    embeddings[idx] = embedding

            self._manage_cache_size()
            return embeddings

    @classmethod
    def get_instance(cls):
        return cls()