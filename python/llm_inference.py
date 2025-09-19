try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    import time
    import logging
except ImportError:
    import os
    os.system("pip install transformers torch")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    import time
    import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

class LLMInference:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            start_time = time.time()
            self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
            self.model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            load_time = time.time() - start_time
            logger.info(f"LLM model load time: {load_time:.2f}s")
            self._initialized = True

    def generate(self, prompt: str) -> str:
        start_time = time.time()
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_length=512)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        gen_time = time.time() - start_time
        logger.info(f"LLM generate time for prompt length {len(prompt)}: {gen_time:.2f}s")
        return response