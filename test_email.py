import asyncio
from app.email_utils import send_reset_email  # Use correct import path

async def test_email():
    print(" Starting email test...")
    await send_reset_email("lalaraza11p@gmail.com", "test-reset-token")
    print(" Email function executed!")

asyncio.run(test_email())
