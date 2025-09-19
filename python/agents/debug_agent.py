from ..llm_inference import LLMInference

class DebugAgent:
    def __init__(self):
        self.llm = LLMInference()

    def re_plan(self, alt: str, context_id: str) -> str:
        prompt = f"Re-plan for error: {alt}"
        return self.llm.generate(prompt)