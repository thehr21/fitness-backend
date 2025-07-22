import os
import sys
import pytest
from httpx import AsyncClient

os.environ["ENV"] = "test"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_create_community_post():
    async with AsyncClient(base_url=BASE_URL) as ac:
        payload = {
            "user_id": 35,
            "content": "Lost 5kg this week by eating clean and daily workouts!",
            "media_url": None
        }

        response = await ac.post("/community/create-post", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == payload["content"]
        assert data["user"]["id"] == payload["user_id"]

@pytest.mark.asyncio
async def test_add_comment_to_post():
    async with AsyncClient(base_url=BASE_URL) as ac:
        comment_payload = {
            "user_id": 35,
            "post_id": 45,  
            "content": "Awesome work! Keep pushing 💪"
        }

        response = await ac.post("/community/add-comment", json=comment_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == comment_payload["content"]
        assert data["post_id"] == comment_payload["post_id"]
