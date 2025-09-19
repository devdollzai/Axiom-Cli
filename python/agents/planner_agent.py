from ..llm_inference import LLMInference

class PlannerAgent:
    def __init__(self):
        self.llm = LLMInference()
        self.system_prompt = "Decompose NL command into Git subtasks. Respond JSON {'subtasks': [...] }."

    def decompose(self, command: str) -> list:
        prompt = f"{self.system_prompt}\nCommand: {command}"
        response = self.llm.generate(prompt)
        # Parse JSON
        import json
        try:
            data = json.loads(response)
            return data.get('subtasks', [command])
        except:
            return [command]