#!/usr/bin/env python3
"""
Test script to verify singleton, caching, and batching functionality in EmbeddingModel.
"""

import sys
import os
import time

# Mock sentence_transformers to avoid dependency issues
class MockEmbedding:
    def __init__(self, data):
        self.data = data

    def tolist(self):
        return self.data

class MockSentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, texts):
        if isinstance(texts, str):
            # Single text - return mock embedding
            return MockEmbedding([0.1] * 384)  # 384 dimensions like real model
        else:
            # Batch - return list of embeddings
            return MockEmbedding([[0.1] * 384 for _ in texts])

# Monkey patch
sys.modules['sentence_transformers'] = type(sys)('sentence_transformers')
sys.modules['sentence_transformers'].SentenceTransformer = MockSentenceTransformer

# Import after mocking
from embedding_model import EmbeddingModel

def test_singleton():
    print("Testing singleton pattern...")

    # Create multiple instances
    emb1 = EmbeddingModel()
    emb2 = EmbeddingModel()
    emb3 = EmbeddingModel.get_instance()

    # All should be the same instance
    assert emb1 is emb2, "Multiple instantiations should return same instance"
    assert emb2 is emb3, "get_instance should return same instance"
    print("✓ Singleton pattern works")

def test_caching():
    print("Testing caching functionality...")

    emb = EmbeddingModel()

    text = "Hello, world!"
    start_time = time.time()
    embedding1 = emb.embed(text)
    first_time = time.time() - start_time

    start_time = time.time()
    embedding2 = emb.embed(text)  # Should be cached
    second_time = time.time() - start_time

    assert embedding1 == embedding2, "Cached embedding should be identical"
    assert second_time < first_time, "Cached call should be faster"
    print("✓ Caching works")

def test_batch_embedding():
    print("Testing batch embedding...")

    emb = EmbeddingModel()

    texts = ["Hello", "How are you?", "Goodbye"]
    embeddings = emb.embed(texts)

    assert len(embeddings) == 3, "Should return list of 3 embeddings"
    assert len(embeddings[0]) == 384, "Each embedding should be 384 dimensions"
    print("✓ Batch embedding works")

def test_mixed_cache_and_batch():
    print("Testing mixed cache and batch...")

    emb = EmbeddingModel()

    # First embed single text
    text1 = "Hello, world!"
    emb.embed(text1)

    # Then batch with one cached, one new
    texts = [text1, "New text"]
    embeddings = emb.embed(texts)

    assert len(embeddings) == 2, "Should return 2 embeddings"
    # First should be cached, second new
    print("✓ Mixed cache and batch works")

def test_cache_size_limit():
    print("Testing cache size limit...")

    emb = EmbeddingModel()

    # Fill cache beyond limit
    for i in range(emb.CACHE_SIZE + 10):
        emb.embed(f"Text {i}")

    assert len(emb._cache) <= emb.CACHE_SIZE, "Cache should not exceed size limit"
    print("✓ Cache size limit works")

def test_performance():
    print("Testing performance improvements...")

    emb = EmbeddingModel()

    texts = [f"Text {i}" for i in range(100)]

    # First batch (no cache)
    start_time = time.time()
    embeddings1 = emb.embed(texts)
    first_batch_time = time.time() - start_time

    # Second batch (should be cached)
    start_time = time.time()
    embeddings2 = emb.embed(texts)
    second_batch_time = time.time() - start_time

    assert embeddings1 == embeddings2, "Results should be identical"
    assert second_batch_time < first_batch_time, "Cached batch should be faster"
    print(".2f")
    print(".2f")
    print(".2f")

if __name__ == "__main__":
    test_singleton()
    test_caching()
    test_batch_embedding()
    test_mixed_cache_and_batch()
    test_cache_size_limit()
    test_performance()
    print("\n✅ All EmbeddingModel optimization tests passed!")