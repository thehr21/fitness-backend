import os
import sys
import pytest
from httpx import AsyncClient

os.environ["ENV"] = "test"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_verify_reset_code_valid():
    async with AsyncClient(base_url=BASE_URL) as ac:
        response = await ac.post("/auth/verify-reset-code", json={
            "email": "testuser1234@example.com",
            "reset_code": "491136"  # Replace with real valid code
        })
        assert response.status_code == 200
        assert "message" in response.json()
