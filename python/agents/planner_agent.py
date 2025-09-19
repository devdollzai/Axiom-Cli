from llm_inference import LLMInference
from typing import List
import time
from collections import OrderedDict
import hashlib

class PlannerAgent:
    def __init__(self):
        self.llm = LLMInference()
        self.system_prompt = "Decompose NL command into Git subtasks. Respond JSON {'subtasks': [...] }."
        self.cache = OrderedDict()  # LRU cache with timestamps
        self.cache_size = 100  # Max cache size
        self.cache_ttl = 3600  # TTL in seconds (1 hour)

    def _get_cache_key(self, command: str) -> str:
        return hashlib.md5(command.encode()).hexdigest()

    def _is_cache_expired(self, timestamp: float) -> bool:
        return time.time() - timestamp > self.cache_ttl

    def _cleanup_expired_cache(self):
        expired_keys = [k for k, v in self.cache.items() if self._is_cache_expired(v['timestamp'])]
        for k in expired_keys:
            del self.cache[k]

    def _get_cached_result(self, command: str):
        self._cleanup_expired_cache()
        key = self._get_cache_key(command)
        if key in self.cache:
            self.cache.move_to_end(key)  # LRU
            return self.cache[key]['result']
        return None

    def _set_cached_result(self, command: str, result):
        key = self._get_cache_key(command)
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.cache_size:
                self.cache.popitem(last=False)  # Remove LRU
        self.cache[key] = {'result': result, 'timestamp': time.time()}

    def decompose(self, command: str) -> list:
        # Check cache first
        cached_result = self._get_cached_result(command)
        if cached_result is not None:
            return cached_result

        prompt = f"{self.system_prompt}\nCommand: {command}"
        response = self.llm.generate(prompt)
        # Parse JSON
        import json
        try:
            data = json.loads(response)
            result = data.get('subtasks', [command])
        except:
            result = [command]

        # Cache the result
        self._set_cached_result(command, result)
        return result

    def batch_decompose(self, commands: List[str]) -> List[list]:
        results = []
        uncached_commands = []
        uncached_indices = []

        # Check cache for each command
        for i, cmd in enumerate(commands):
            cached_result = self._get_cached_result(cmd)
            if cached_result is not None:
                results.append(cached_result)
            else:
                results.append(None)  # Placeholder
                uncached_commands.append(cmd)
                uncached_indices.append(i)

        # Process uncached commands
        if uncached_commands:
            prompts = [f"{self.system_prompt}\nCommand: {cmd}" for cmd in uncached_commands]
            responses = self.llm.generate(prompts)
            import json
            for idx, response in zip(uncached_indices, responses):
                try:
                    data = json.loads(response)
                    result = data.get('subtasks', [commands[idx]])
                except:
                    result = [commands[idx]]
                results[idx] = result
                # Cache the result
                self._set_cached_result(commands[idx], result)

        return results