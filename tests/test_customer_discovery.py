import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.database import init_db

@pytest.fixture(autouse=True)
async def setup_test_database():
    await init_db()

@pytest.mark.asyncio
async def test_behavioral_discovery_insights_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/discovery/behavioral-insights")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_questions_answered"] == 8
    assert len(data["behavioral_insights"]) == 8

@pytest.mark.asyncio
async def test_single_question_insight_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/discovery/question/q1_repeat_buying")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["insight"]["question_id"] == "q1_repeat_buying"
    assert "repeat" in data["insight"]["question"].lower()
