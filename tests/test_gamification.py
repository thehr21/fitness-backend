import os
import sys
import pytest
from httpx import AsyncClient

os.environ["ENV"] = "test"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_fetch_user_badges():
    async with AsyncClient(base_url=BASE_URL) as ac:
        response = await ac.get("/gamification/badges", params={"user_id": 35})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "id" in data[0]
            assert "name" in data[0]
            assert "fa_icon_class" in data[0]

@pytest.mark.asyncio
async def test_fetch_user_progress():
    async with AsyncClient(base_url=BASE_URL) as ac:
        response = await ac.get("/gamification/user-progress", params={"user_id": 35})
        assert response.status_code == 200
        data = response.json()
        assert "current_streaks" in data
        assert "best_streaks" in data
        assert "total_logs" in data
