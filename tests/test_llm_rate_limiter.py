import time
import pytest
from backend.llm_rate_limiter import GoogleAIStudioRateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_rpm_throttling():
    limiter = GoogleAIStudioRateLimiter(max_rpm=60, max_tpm=100000)
    
    t0 = time.time()
    await limiter.acquire(estimated_input_tokens=100)
    t1 = time.time()
    await limiter.acquire(estimated_input_tokens=100)
    t2 = time.time()

    elapsed = t2 - t1
    assert elapsed >= 0.95  # Confirms >= 1.0 second delay enforced between requests

def test_token_estimation():
    limiter = GoogleAIStudioRateLimiter()
    sample_text = "Curd packet was torn and leaked over bread and eggs in my bag!"
    tokens = limiter.estimate_tokens(sample_text)
    assert tokens > 200  # Includes system prompt overhead
