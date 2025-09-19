from llm_inference import LLMInference
from typing import List
import time
from collections import OrderedDict
import hashlib

class DebugAgent:
    def __init__(self):
        self.llm = LLMInference()
        self.cache = OrderedDict()  # LRU cache with timestamps
        self.cache_size = 100  # Max cache size
        self.cache_ttl = 3600  # TTL in seconds (1 hour)

    def _get_cache_key(self, alt: str, context_id: str) -> str:
        combined = f"{alt}|{context_id}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _is_cache_expired(self, timestamp: float) -> bool:
        return time.time() - timestamp > self.cache_ttl

    def _cleanup_expired_cache(self):
        expired_keys = [k for k, v in self.cache.items() if self._is_cache_expired(v['timestamp'])]
        for k in expired_keys:
            del self.cache[k]

    def _get_cached_result(self, alt: str, context_id: str):
        self._cleanup_expired_cache()
        key = self._get_cache_key(alt, context_id)
        if key in self.cache:
            self.cache.move_to_end(key)  # LRU
            return self.cache[key]['result']
        return None

    def _set_cached_result(self, alt: str, context_id: str, result):
        key = self._get_cache_key(alt, context_id)
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.cache_size:
                self.cache.popitem(last=False)  # Remove LRU
        self.cache[key] = {'result': result, 'timestamp': time.time()}

    def re_plan(self, alt: str, context_id: str) -> str:
        # Check cache first
        cached_result = self._get_cached_result(alt, context_id)
        if cached_result is not None:
            return cached_result

        prompt = f"Re-plan for error: {alt}"
        result = self.llm.generate(prompt)

        # Cache the result
        self._set_cached_result(alt, context_id, result)
        return result

    def batch_re_plan(self, alts: List[str], context_ids: List[str]) -> List[str]:
        results = []
        uncached_alts = []
        uncached_context_ids = []
        uncached_indices = []

        # Check cache for each pair
        for i, (alt, context_id) in enumerate(zip(alts, context_ids)):
            cached_result = self._get_cached_result(alt, context_id)
            if cached_result is not None:
                results.append(cached_result)
            else:
                results.append(None)  # Placeholder
                uncached_alts.append(alt)
                uncached_context_ids.append(context_id)
                uncached_indices.append(i)

        # Process uncached pairs
        if uncached_alts:
            prompts = [f"Re-plan for error: {alt}" for alt in uncached_alts]
            responses = self.llm.generate(prompts)
            for idx, response in zip(uncached_indices, responses):
                results[idx] = response
                # Cache the result
                self._set_cached_result(alts[idx], context_ids[idx], response)

        return results