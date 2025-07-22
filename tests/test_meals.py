# tests/test_meals.py

import os, sys, pytest
from httpx import AsyncClient

os.environ["ENV"] = "test"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_meal_fetch_and_log():
    async with AsyncClient(base_url=BASE_URL) as ac:
        res = await ac.get("/meals/gain_muscle?refresh=true")
        assert res.status_code == 200
        meals = res.json()
        assert isinstance(meals, list) and meals

        meal = meals[0]
        log_res = await ac.post("/log-meals/", json={
            "user_id": 35,
            "food_item": meal["food_item"],
            "calories": meal["calories"],
            "protein": meal["protein"],
            "carbs": 0,
            "fats": 0
        })
        assert log_res.status_code == 200
        assert "id" in log_res.json()
