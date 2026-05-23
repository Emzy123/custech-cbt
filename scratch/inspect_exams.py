import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def inspect():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.cbt_db
    exams_col = db.examinations
    
    print("--- Inspecting examinations collection ---")
    async for exam in exams_col.find():
        print(f"ID: {exam.get('_id')}")
        print(f"  Title: {exam.get('title')}")
        print(f"  Course Code: {exam.get('course_code')}")
        print(f"  Duration: {exam.get('duration_minutes')}")
        print(f"  Total Questions: {exam.get('total_questions')} (type: {type(exam.get('total_questions'))})")
        print(f"  Scheduled Date: {exam.get('scheduled_date')} (type: {type(exam.get('scheduled_date'))})")
        print(f"  Start Time: {exam.get('start_time')} (type: {type(exam.get('start_time'))})")
        print(f"  End Time: {exam.get('end_time')} (type: {type(exam.get('end_time'))})")
        print(f"  Is Active: {exam.get('is_active')} (type: {type(exam.get('is_active'))})")
        print(f"  Created By: {exam.get('created_by')}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(inspect())
