from ..llm_inference import LLMInference
from typing import List, Union

class LLMAgent:
    def __init__(self):
        self.llm = LLMInference()

    def generate(self, prompt: str) -> str:
        result = self.llm.generate(prompt)
        if isinstance(result, str):
            return result
        else:
            raise ValueError("Expected string response for single prompt")

    def batch_generate(self, prompts: List[str]) -> List[str]:
        result = self.llm.generate(prompts)
        if isinstance(result, list):
            return result
        else:
            raise ValueError("Expected list response for batch prompts")

    async def agenerate(self, prompt: str) -> str:
        result = await self.llm.agenerate(prompt)
        if isinstance(result, str):
            return result
        else:
            raise ValueError("Expected string response for single prompt")

    async def abatch_generate(self, prompts: List[str]) -> List[str]:
        result = await self.llm.agenerate(prompts)
        if isinstance(result, list):
            return result
        else:
            raise ValueError("Expected list response for batch prompts")