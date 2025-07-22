import os
import sys
import pytest
from httpx import AsyncClient

os.environ["ENV"] = "test"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_ai_habit_suggestion_valid_user():
    async with AsyncClient(base_url=BASE_URL) as ac:
        response = await ac.get("/ai/ai/suggestions/35") 
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "suggestion" in data
        assert "model_input" in data
