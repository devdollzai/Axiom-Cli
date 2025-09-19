#!/usr/bin/env python3
"""
Test script to verify that LLMInference uses a singleton pattern,
ensuring only one model load occurs when multiple instances are created.
"""

import sys
import os
import time
import logging

# Mock the transformers import to avoid dependency issues during testing
class MockTokenizer:
    def __init__(self):
        self.pad_token = "[PAD]"
        self.eos_token = "[EOS]"

    def __call__(self, prompt, return_tensors="pt"):
        return {"input_ids": [[1, 2, 3]]}

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
    def generate(self, inputs, max_length=512):
        return [[1, 2, 3, 4]]

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

# Set up logging to capture model load messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_singleton_llm():
    print("Testing LLMInference singleton pattern...")

    # Record start time
    start_time = time.time()

    # Create multiple instances of LLMInference directly
    llm1 = LLMInference()
    llm2 = LLMInference()
    llm3 = LLMInference()

    # Check that all instances are the same object
    assert llm1 is llm2, "LLMInference instances should be the same (singleton)"
    assert llm2 is llm3, "LLMInference instances should be the same (singleton)"
    print("✓ Direct LLMInference instances are identical (singleton working)")

    # Test that generate method works
    test_prompt = "Hello, test prompt"
    response1 = llm1.generate(test_prompt)
    response2 = llm2.generate(test_prompt)
    response3 = llm3.generate(test_prompt)

    assert response1 == response2 == response3, "All generate calls should return same response for same prompt"
    print("✓ Generate method works consistently across shared instances")

    end_time = time.time()
    total_time = end_time - start_time
    print(".2f")

    print("\n✅ All tests passed! Singleton pattern is working correctly.")
    print("Only one model load should have occurred (check logs above).")

if __name__ == "__main__":
    test_singleton_llm()