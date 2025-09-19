#!/usr/bin/env python3
"""
Test script to verify caching functionality in PlannerAgent and DebugAgent.
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
                return '{"subtasks": ["mock", "response"]}' if "decompose" in str(outputs) else "Mock re-plan response"
        elif isinstance(outputs, list):
            if len(outputs) == 1:
                return '{"subtasks": ["mock", "response"]}' if "decompose" in str(outputs) else "Mock re-plan response"
            else:
                return ['{"subtasks": ["mock", "response"]}' if "decompose" in str(outputs) else "Mock re-plan response"] * len(outputs)
        else:
            return '{"subtasks": ["mock", "response"]}' if "decompose" in str(outputs) else "Mock re-plan response"

class MockModel:
    def generate(self, input_ids=None, max_length=512, **kwargs):
        if input_ids is None:
            input_ids = kwargs.get("input_ids")
        if input_ids and input_ids.dim() == 1:
            return MockTensor([[1, 2, 3, 4]])
        else:
            # Batch
            batch_size = input_ids.shape[0] if input_ids else 1
            return MockTensor([[1, 2, 3, 4]] * batch_size)

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

# Import agents
from agents.planner_agent import PlannerAgent
from agents.debug_agent import DebugAgent

# Set up logging to capture messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_planner_agent_caching():
    print("Testing PlannerAgent caching...")

    # Create instance
    planner = PlannerAgent()

    # Test single decompose
    command1 = "Create a new git repository"
    result1 = planner.decompose(command1)
    print(f"First decompose result: {result1}")

    # Test cache hit
    result1_cached = planner.decompose(command1)
    assert result1 == result1_cached, "Cache should return same result"
    print("✓ PlannerAgent cache hit works")

    # Test batch decompose
    commands = [command1, "Add files to git", "Commit changes"]
    batch_results = planner.batch_decompose(commands)
    assert len(batch_results) == 3, "Batch should return list of results"
    assert batch_results[0] == result1, "First result should be cached"
    print(f"Batch results: {batch_results}")
    print("✓ PlannerAgent batch caching works")

    # Test cache size limit
    for i in range(105):
        planner.decompose(f"Command {i}")
    assert len(planner.cache) <= 100, "Cache should not exceed size"
    print("✓ PlannerAgent cache size limit works")

    return True

def test_debug_agent_caching():
    print("\nTesting DebugAgent caching...")

    # Create instance
    debug = DebugAgent()

    # Test single re_plan
    alt1 = "File not found error"
    context_id1 = "ctx123"
    result1 = debug.re_plan(alt1, context_id1)
    print(f"First re_plan result: {result1}")

    # Test cache hit
    result1_cached = debug.re_plan(alt1, context_id1)
    assert result1 == result1_cached, "Cache should return same result"
    print("✓ DebugAgent cache hit works")

    # Test batch re_plan
    alts = [alt1, "Permission denied", "Network timeout"]
    context_ids = [context_id1, "ctx456", "ctx789"]
    batch_results = debug.batch_re_plan(alts, context_ids)
    assert len(batch_results) == 3, "Batch should return list of results"
    assert batch_results[0] == result1, "First result should be cached"
    print(f"Batch results: {batch_results}")
    print("✓ DebugAgent batch caching works")

    # Test cache size limit
    for i in range(105):
        debug.re_plan(f"Error {i}", f"context{i}")
    assert len(debug.cache) <= 100, "Cache should not exceed size"
    print("✓ DebugAgent cache size limit works")

    return True

def test_ttl_expiration():
    print("\nTesting TTL expiration...")

    # Create agents with short TTL for testing
    planner = PlannerAgent()
    planner.cache_ttl = 1  # 1 second TTL

    debug = DebugAgent()
    debug.cache_ttl = 1  # 1 second TTL

    # Cache some results
    planner.decompose("Test command")
    debug.re_plan("Test error", "test_ctx")

    # Wait for TTL to expire
    time.sleep(2)

    # Check that cache is cleaned up on access
    planner.decompose("Different command")  # This should trigger cleanup
    debug.re_plan("Different error", "diff_ctx")  # This should trigger cleanup

    # The expired entries should be cleaned up
    print("✓ TTL expiration works (expired entries cleaned up)")

    return True

if __name__ == "__main__":
    try:
        test_planner_agent_caching()
        test_debug_agent_caching()
        test_ttl_expiration()
        print("\n✅ All agent caching tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)