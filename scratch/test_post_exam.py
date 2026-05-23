import asyncio
import sys
import httpx
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager, cache_manager
from cbt.models.user import User

async def main():
    await init_db()
    await redis_manager.connect()
    
    redis_client = redis_manager.redis_client
    
    # Let's find access token for examofficer
    user_id = '6cfa02b4-1db7-44eb-a405-2dcaf7f21c6d'
    keys = await redis_client.keys("access_token:*")
    full_token = None
    for key in keys:
        token = key.decode('utf-8').split(":")[1]
        cached_user_id = await cache_manager.get(f"access_token:{token}")
        if cached_user_id == user_id:
            full_token = token
            break
            
    if not full_token:
        print("No active access token found for examofficer in Redis!")
        await redis_manager.disconnect()
        return
        
    print(f"Found active access token: {full_token}")
    
    # Let's prepare a valid payload for creating an examination
    # We need academic_session_id and semester_id
    # Let's fetch them from database or use sample
    from cbt.models.exam import Examination
    from cbt.models.academic import Course as AcadCourse
    course = await AcadCourse.find_one()
    course_id = course.id if course else "course_id_placeholder"
    
    payload = {
        "title": "GST 101 Examination",
        "course_id": course_id,
        "exam_date": "2026-05-29",
        "start_time": "2026-05-29T10:00:00",
        "duration_minutes": 120,
        "total_points": 100,
        "pass_points": 40,
        "academic_session_id": "session-placeholder",
        "semester_id": "semester-placeholder",
        "question_ids": []
    }
    
    headers = {
        "Authorization": f"Bearer {full_token}",
        "Content-Type": "application/json"
    }
    
    print("\nSending POST request to http://localhost:8000/api/v1/examinations/ ...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/examinations/",
            json=payload,
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
    await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
