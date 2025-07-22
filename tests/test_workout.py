import os, sys, pytest
from httpx import AsyncClient

os.environ["ENV"] = "test"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_workout_fetch_and_log():
    async with AsyncClient(base_url=BASE_URL) as ac:
        res = await ac.get("/workouts", params={"user_id": 35, "workout_type": "home", "muscle_group": "chest"})
        assert res.status_code == 200
        workout = res.json()["workouts"][0]
        assert "name" in workout

        log = await ac.post("/log-workout", json={
            "user_id": 35,
            "workout_name": workout["name"],
            "muscle_group": workout["target_muscle"],
            "equipment": workout["equipment"]
        })
        assert log.status_code == 200 and "id" in log.json()
