#!/usr/bin/env python3
"""
Test script to verify batching and caching functionality in LLMInference.
"""

import sys
import os
import time
import logging

# Mock the transformers import to avoid dependency issues during testing
class MockTensor:
    def __init__(self, data):
        self.data = data

    def dim(self):
        return len(self.data) if isinstance(self.data, list) else 1

    @property
    def shape(self):
        return (len(self.data), len(self.data[0])) if isinstance(self.data, list) else (len(self.data),)

    def to(self, device):
        return self

    def __getitem__(self, idx):
        return self.data[idx]

    def __len__(self):
        return len(self.data)

class MockInputs:
    def __init__(self, data):
        self.data = data

    def to(self, device):
        return self

    def __getitem__(self, key):
        return self.data[key]

    def keys(self):
        return self.data.keys()

    def __iter__(self):
        return iter(self.data)

class MockTokenizer:
    def __init__(self):
        self.pad_token = "[PAD]"

    def __call__(self, prompts, return_tensors="pt", padding=False):
        if isinstance(prompts, str):
            return MockInputs({"input_ids": MockTensor([[1, 2, 3]])})
        else:
            # Batch
            return MockInputs({"input_ids": MockTensor([[1, 2, 3]] * len(prompts))})

    def decode(self, outputs, skip_special_tokens=True):
        if hasattr(outputs, 'data'):
            data = outputs.data
            if isinstance(data, list) and len(data) > 1:
                return [f"Mock response {i}" for i in range(len(data))]
            else:
                return "Mock response"
        elif isinstance(outputs, list):
            if len(outputs) == 1:
                return "Mock response"
            else:
                return [f"Mock response {i}" for i in range(len(outputs))]
        else:
            return "Mock response"

class MockModel:
    def generate(self, input_ids=None, max_length=512, **kwargs):
        if input_ids is None:
            input_ids = kwargs.get("input_ids")
        if input_ids and hasattr(input_ids, 'dim') and input_ids.dim() == 1:
            return MockTensor([[1, 2, 3, 4]])
        elif input_ids and hasattr(input_ids, 'shape'):
            # Batch
            batch_size = input_ids.shape[0] if input_ids else 1
            return MockTensor([[1, 2, 3, 4]] * batch_size)
        else:
            # Mock case
            return MockTensor([[1, 2, 3, 4]])

    def to(self, device):
        return self

class MockAutoTokenizer:
    @staticmethod
    def from_pretrained(model_name):
        return MockTokenizer()

class MockAutoModelForCausalLM:
    @staticmethod
    def from_pretrained(model_name):
        return MockModel()

class MockCuda:
    @staticmethod
    def is_available():
        return False

class MockTorch:
    cuda = MockCuda()

# Monkey patch the imports
sys.modules['transformers'] = type(sys)('transformers')
sys.modules['transformers'].AutoTokenizer = MockAutoTokenizer
sys.modules['transformers'].AutoModelForCausalLM = MockAutoModelForCausalLM
sys.modules['torch'] = MockTorch

# Import LLMInference
from llm_inference import LLMInference

# Set up logging to capture messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_batching_and_caching():
    print("Testing LLMInference batching and caching...")

    # Create instance
    llm = LLMInference()

    # Test single prompt
    prompt1 = "Hello, world!"
    response1 = llm.generate(prompt1)
    print(f"Single prompt response: {response1}")

    # Test cache hit
    response1_cached = llm.generate(prompt1)
    assert response1 == response1_cached, "Cache should return same response"
    print("✓ Cache hit works")

    # Test batch
    prompts = ["Hello", "How are you?", "Goodbye"]
    responses = llm.generate(prompts)
    assert len(responses) == 3, "Batch should return list of responses"
    print(f"Batch responses: {responses}")

    # Test mixed cache and new
    prompts_mixed = [prompt1, "New prompt"]
    responses_mixed = llm.generate(prompts_mixed)
    assert responses_mixed[0] == response1, "First should be cached"
    print("✓ Mixed cache and new works")

    # Test cache size limit (CACHE_SIZE=100, but with 2 it's fine)
    # Add more to test LRU
    for i in range(105):
        llm.generate(f"Prompt {i}")
    assert len(llm.cache) <= 100, "Cache should not exceed size"
    print("✓ Cache size limit works")

    # Core functionality tested above

    print("\n✅ All batching and caching tests passed!")

if __name__ == "__main__":
    test_batching_and_caching()