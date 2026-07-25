import time
import asyncio
import logging
from typing import Dict, Any, List
from backend.config import settings

logger = logging.getLogger(__name__)

class GoogleAIStudioRateLimiter:
    """
    Asynchronous Leaky Bucket Rate Limiter & Token Throttle for Google AI Studio (Gemini API).
    
    Limits:
    - Requests Per Minute (RPM): 60 (max 1 request per second)
    - Tokens Per Minute (TPM): 100,000 (100K TPM)
    """

    def __init__(
        self,
        max_rpm: int = settings.GOOGLE_AI_STUDIO_RPM_LIMIT,
        max_tpm: int = settings.GOOGLE_AI_STUDIO_TPM_LIMIT
    ):
        self.max_rpm = max_rpm
        self.max_tpm = max_tpm
        self.request_interval = 60.0 / max_rpm  # 1.0 second per request

        self.last_request_time = 0.0
        self.tokens_used_in_window = 0
        self.window_start_time = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_input_tokens: int = 1500):
        """
        Acquires permission to send an API request to Google AI Studio.
        Throttles request execution to stay strictly within 60 RPM and 100K TPM.
        """
        async with self._lock:
            now = time.time()
            elapsed_window = now - self.window_start_time

            # Reset TPM rolling window every 60 seconds
            if elapsed_window >= 60.0:
                self.window_start_time = now
                self.tokens_used_in_window = 0
                elapsed_window = 0.0

            # Check TPM limit
            if self.tokens_used_in_window + estimated_input_tokens > self.max_tpm:
                sleep_for = 60.0 - elapsed_window + 0.1
                logger.warning(f"TPM limit threshold reached ({self.tokens_used_in_window} tokens used). Sleeping for {sleep_for:.2f}s...")
                await asyncio.sleep(sleep_for)
                now = time.time()
                self.window_start_time = now
                self.tokens_used_in_window = 0

            # Check RPM limit (1 request per second)
            time_since_last_req = now - self.last_request_time
            if time_since_last_req < self.request_interval:
                sleep_req = self.request_interval - time_since_last_req
                await asyncio.sleep(sleep_req)
                now = time.time()

            # Record request execution
            self.last_request_time = now
            self.tokens_used_in_window += estimated_input_tokens
            logger.info(f"LLM API Request Permitted | Est. Tokens: {estimated_input_tokens} | TPM Window: {self.tokens_used_in_window}/{self.max_tpm}")

    def estimate_tokens(self, text_or_batch) -> int:
        """Estimates token count (rough heuristic: ~4 chars per token)."""
        if isinstance(text_or_batch, list):
            total_chars = sum(len(str(item)) for item in text_or_batch)
        else:
            total_chars = len(str(text_or_batch))
        return max(10, int(total_chars / 3.5) + 200)  # Includes system prompt overhead

# Global rate limiter instance
rate_limiter = GoogleAIStudioRateLimiter()
