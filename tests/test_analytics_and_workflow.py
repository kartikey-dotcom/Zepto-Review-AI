import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.database import init_db

@pytest.fixture(autouse=True)
async def setup_test_database():
    await init_db()

@pytest.mark.asyncio
async def test_analytics_summary_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_reviews" in data
    assert "average_rating" in data
    assert "star_distribution" in data

@pytest.mark.asyncio
async def test_aspect_trends_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/aspect-trends")
    assert response.status_code == 200
    trends = response.json()
    assert isinstance(trends, list)

@pytest.mark.asyncio
async def test_version_comparison_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/version-comparison")
    assert response.status_code == 200
    matrix = response.json()
    assert isinstance(matrix, list)

@pytest.mark.asyncio
async def test_csv_export_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/export/reviews.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Review ID" in response.text
