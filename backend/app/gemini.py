import collections
import hashlib
import logging
import time
from typing import Dict, Optional, Any
from .config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("gemini")

class RateLimitExceeded(Exception):
    pass

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL or "gemini-2.5-flash"
        # Limiter: 8 requests per minute, 400 per day
        self._minute_timestamps = collections.deque()
        self._day_timestamps = collections.deque()
        self._cache: Dict[str, str] = {}

    def _check_rate_limit(self) -> None:
        now = time.time()
        # Clean timestamps older than 60s
        while self._minute_timestamps and now - self._minute_timestamps[0] > 60:
            self._minute_timestamps.popleft()
        # Clean timestamps older than 86400s (24h)
        while self._day_timestamps and now - self._day_timestamps[0] > 86400:
            self._day_timestamps.popleft()

        if len(self._minute_timestamps) >= 8:
            raise RateLimitExceeded("Client rate limit exceeded: maximum 8 requests per minute.")

        if len(self._day_timestamps) >= 400:
            raise RateLimitExceeded("Client rate limit exceeded: maximum 400 requests per day.")

    def _record_request(self) -> None:
        now = time.time()
        self._minute_timestamps.append(now)
        self._day_timestamps.append(now)

    def generate_draft(self, prompt: str) -> str:
        """
        Generate content using google-genai SDK.
        Caches identical requests in-memory.
        Enforces 8 req/min and 400 req/day limits.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # In-memory cache check
        cache_key = hashlib.sha256(f"{self.model}:{prompt}".encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        self._check_rate_limit()

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        self._record_request()

        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=600
        )

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )

        text = response.text or ""
        self._cache[cache_key] = text
        return text
