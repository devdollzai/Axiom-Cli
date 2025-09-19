#!/usr/bin/env python3
"""
Test script to verify that LLMInference uses a singleton pattern,
ensuring only one model load occurs when multiple agents are instantiated.
"""

import sys
import os
import time
import logging

# Add the parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock the transformers import to avoid dependency issues during testing
class MockTokenizer:
    def __call__(self, prompt, return_tensors="pt"):
        return {"input_ids": [[1, 2, 3]]}

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

class MockTorch:
    cuda = False

# Monkey patch the imports
sys.modules['transformers'] = type(sys)('transformers')
sys.modules['transformers'].AutoTokenizer = MockAutoTokenizer
sys.modules['transformers'].AutoModelForCausalLM = MockAutoModelForCausalLM
sys.modules['torch'] = MockTorch

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from llm_inference import LLMInference
from agents.planner_agent import PlannerAgent
from agents.debug_agent import DebugAgent
from agents.llm_agent import LLMAgent

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

    # Create multiple agents
    planner = PlannerAgent()
    debug = DebugAgent()
    llm_agent = LLMAgent()

    # Check that agents share the same LLM instance
    assert planner.llm is debug.llm, "Planner and Debug agents should share LLM instance"
    assert debug.llm is llm_agent.llm, "Debug and LLM agents should share LLM instance"
    assert planner.llm is llm1, "Agent LLM should be same as direct instance"
    print("✓ All agents share the same LLM instance")

    # Test that generate method works
    test_prompt = "Hello, test prompt"
    response1 = llm1.generate(test_prompt)
    response2 = planner.llm.generate(test_prompt)
    response3 = debug.llm.generate(test_prompt)

    assert response1 == response2 == response3, "All generate calls should return same response for same prompt"
    print("✓ Generate method works consistently across shared instances")

    end_time = time.time()
    total_time = end_time - start_time
    print(".2f")

    print("\n✅ All tests passed! Singleton pattern is working correctly.")
    print("Only one model load should have occurred (check logs above).")

if __name__ == "__main__":
    test_singleton_llm()