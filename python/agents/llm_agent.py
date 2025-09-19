from ..llm_inference import LLMInference

class LLMAgent:
    def __init__(self):
        self.llm = LLMInference()

    def generate(self, prompt: str) -> str:
        return self.llm.generate(prompt)