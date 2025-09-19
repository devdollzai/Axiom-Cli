try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    import time
    import logging
    import hashlib
    import json
    import os
    from collections import OrderedDict
    import asyncio
except ImportError:
    import os
    os.system("pip install transformers torch")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    import time
    import logging
    import hashlib
    import json
    import os
    from collections import OrderedDict
    import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

class LLMInference:
    _instance = None
    CACHE_SIZE = 100  # Max cache size
    CACHE_FILE = "llm_cache.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            start_time = time.time()
            self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            load_time = time.time() - start_time
            logger.info(f"LLM model load time: {load_time:.2f}s")
            self._initialized = True
            self.cache = OrderedDict()  # LRU cache
            self._load_cache()

    def _load_cache(self):
        """Load cache from disk if exists"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert back to OrderedDict, keeping recent items
                    for key, value in list(data.items())[-self.CACHE_SIZE:]:
                        self.cache[key] = value
                logger.info(f"Loaded {len(self.cache)} cached responses from disk")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(dict(list(self.cache.items())), f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _get_cache_key(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()

    def _get_cached_response(self, prompt: str):
        key = self._get_cache_key(prompt)
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def _set_cached_response(self, prompt: str, response: str):
        key = self._get_cache_key(prompt)
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.CACHE_SIZE:
                self.cache.popitem(last=False)  # Remove least recently used
        self.cache[key] = response
        # Save cache periodically (every 10 additions)
        if len(self.cache) % 10 == 0:
            self._save_cache()

    def generate(self, prompt):
        """Synchronous generate method"""
        return asyncio.run(self.agenerate(prompt))

    async def agenerate(self, prompt):
        """Asynchronous generate method"""
        from typing import Union, List
        if isinstance(prompt, str):
            # Single prompt
            cached = self._get_cached_response(prompt)
            if cached:
                logger.info(f"Cache hit for prompt length {len(prompt)}")
                return cached
            start_time = time.time()
            # Run model inference in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            inputs = await loop.run_in_executor(None, self.tokenizer, prompt, {"return_tensors": "pt"})
            if hasattr(inputs, 'to'):
                inputs = inputs.to(self.device)
            outputs = await loop.run_in_executor(None, self.model.generate, inputs, {"max_length": 512})
            if hasattr(outputs, '__getitem__'):
                response = await loop.run_in_executor(None, self.tokenizer.decode, outputs[0], {"skip_special_tokens": True})
            else:
                response = await loop.run_in_executor(None, self.tokenizer.decode, outputs, {"skip_special_tokens": True})
            gen_time = time.time() - start_time
            logger.info(f"LLM generate time for prompt length {len(prompt)}: {gen_time:.2f}s")
            self._set_cached_response(prompt, response)
            return response
        elif isinstance(prompt, list):
            # Batch prompts
            responses = []
            uncached_prompts = []
            uncached_indices = []
            for i, p in enumerate(prompt):
                cached = self._get_cached_response(p)
                if cached:
                    responses.append(cached)
                else:
                    responses.append(None)  # Placeholder
                    uncached_prompts.append(p)
                    uncached_indices.append(i)
            if uncached_prompts:
                start_time = time.time()
                loop = asyncio.get_event_loop()
                inputs = await loop.run_in_executor(None, self.tokenizer, uncached_prompts, {"return_tensors": "pt", "padding": True})
                if hasattr(inputs, 'to'):
                    inputs = inputs.to(self.device)
                outputs = await loop.run_in_executor(None, self.model.generate, inputs, {"max_length": 512})
                batch_responses = []
                if hasattr(outputs, '__iter__'):
                    for output in outputs:
                        resp = await loop.run_in_executor(None, self.tokenizer.decode, output, {"skip_special_tokens": True})
                        batch_responses.append(resp)
                else:
                    # Single output case
                    resp = await loop.run_in_executor(None, self.tokenizer.decode, outputs, {"skip_special_tokens": True})
                    batch_responses = [resp] * len(uncached_prompts)
                gen_time = time.time() - start_time
                logger.info(f"LLM batch generate time for {len(uncached_prompts)} prompts: {gen_time:.2f}s")
                for idx, resp in zip(uncached_indices, batch_responses):
                    responses[idx] = resp
                    self._set_cached_response(prompt[idx], resp)
            return responses
        else:
            raise ValueError("Prompt must be str or list[str]")