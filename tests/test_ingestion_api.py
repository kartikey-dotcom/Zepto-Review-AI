import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.database import init_db

@pytest.fixture(autouse=True)
async def setup_test_database():
    await init_db()

@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["target_package"] == "com.zepto.customer"

@pytest.mark.asyncio
async def test_ingest_single_review_with_pii():
    payload = {
        "review_id": "gp:test_rev_9001",
        "user_name": "Rohan Verma",
        "rating": 1,
        "review_text": "App crash ho raha hai pe! Call me on 9876543210 for refund.",
        "app_version": "v4.12.0",
        "thumbs_up_count": 10
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/reviews/ingest/playstore", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] in ["created", "updated"]
    assert data["pii_detected"] is True
    assert "[PHONE_REDACTED]" in data["sanitized_text"]

@pytest.mark.asyncio
async def test_trigger_playstore_scrape():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/reviews/scrape/playstore", json={"count": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_fetched"] >= 5

@pytest.mark.asyncio
async def test_get_paginated_reviews():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/reviews?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "reviews" in data
    assert data["total_count"] >= 1
