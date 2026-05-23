import asyncio
from httpx import AsyncClient
import sys
import json
sys.path.insert(0, 'src')

from cbt.main import app
from cbt.core.database import init_db, close_db
from cbt.core.redis import redis_manager

async def main():
    await init_db()
    await redis_manager.connect()
    
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as test_client:
        login_data = {
            "username": "lecturer",
            "password": "Lecturer123!"
        }
        log_res = await test_client.post("/api/v1/auth/login", json=login_data)
        token = log_res.json()["access_token"]
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        
        # Test GET /api/v1/questions/
        res = await test_client.get("/api/v1/questions/")
        if res.status_code == 200:
            data = res.json()
            print(f"Total questions: {len(data)}")
            if len(data) > 0:
                print("First question detail:")
                print(json.dumps(data[0], indent=2))
        else:
            print(f"Failed to fetch questions: {res.status_code} - {res.text}")

    await redis_manager.disconnect()
    await close_db()

if __name__ == "__main__":
    asyncio.run(main())
