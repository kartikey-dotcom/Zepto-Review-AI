import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.database import init_db
from backend.production_monitor import RatingHealthMonitor

@pytest.fixture(autouse=True)
async def setup_test_database():
    await init_db()

@pytest.mark.asyncio
async def test_rating_health_report_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/monitor/rating-health")
    assert response.status_code == 200
    data = response.json()
    assert "health_score" in data
    assert "health_status" in data
    assert data["health_score"] >= 0 and data["health_score"] <= 100
    assert data["target_package"] == "com.zepto.customer"

@pytest.mark.asyncio
async def test_system_diagnostics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/monitor/system-diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "system_uptime_seconds" in data
    assert "in_memory_cached_reviews" in data

@pytest.mark.asyncio
async def test_trigger_production_scheduler_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/monitor/trigger-scheduler")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scheduler_executed"
    assert "job_summary" in data
