import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.database import init_db
from backend.google_play_console_api import GooglePlayConsoleAPIConnector

@pytest.fixture(autouse=True)
async def setup_test_database():
    await init_db()

def test_play_console_single_reply_publish():
    res = GooglePlayConsoleAPIConnector.publish_reply(
        review_id="gp:test_rev_101",
        reply_text="Hi! We apologize for the delay. Our team is investigating."
    )
    assert res["status"] == "success"
    assert res["package_name"] == "com.zepto.customer"
    assert res["character_count"] <= 350

def test_play_console_character_limit_rejection():
    long_reply = "A" * 360  # Exceeds 350 chars
    res = GooglePlayConsoleAPIConnector.publish_reply(
        review_id="gp:test_rev_102",
        reply_text=long_reply
    )
    assert res["status"] == "error"
    assert "exceeds" in res["message"]

@pytest.mark.asyncio
async def test_load_benchmark_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/loadtest/run")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["PASSED", "WARNING"]
    assert "pii_sanitizer_performance" in data
    assert "normalization_performance" in data
    assert data["total_reviews_tested"] >= 1000
