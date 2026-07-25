import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.database import init_db

@pytest.fixture(autouse=True)
async def setup_test_database():
    await init_db()

@pytest.mark.asyncio
async def test_category_friction_analysis_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/category-adoption/friction-analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "core_grocery_repetition_pct" in data
    assert "non_core_category_adoption_pct" in data
    assert "category_breakdown" in data
    assert "category_switching_friction_barriers" in data
    assert "strategic_growth_recommendations" in data

@pytest.mark.asyncio
async def test_category_adoption_summary_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/category-adoption/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "top_switching_barriers" in data
    assert "growth_recommendations" in data
