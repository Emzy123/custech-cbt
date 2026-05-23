import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.cbt.models.exam import Examination
from src.cbt.core.config import settings

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client.cbt_db
    
    # Initialize Beanie with our updated Examination model
    await init_beanie(database=database, document_models=[Examination])
    
    print("--- Querying all examinations via Beanie ---")
    try:
        exams = await Examination.find_all().to_list()
        for e in exams:
            print(f"Loaded successfully: {e.title}")
            print(f"  ID: {e.id}")
            print(f"  Course Code: {e.course_code}")
            print(f"  Total Questions: {e.total_questions}")
            print(f"  Scheduled Date: {e.scheduled_date}")
            print(f"  Start Time: {e.start_time} (type: {type(e.start_time)})")
            print(f"  End Time: {e.end_time} (type: {type(e.end_time)})")
            print("-" * 30)
        print("Success! All examinations parsed successfully via Beanie!")
    except Exception as err:
        print(f"ERROR: {err}")

if __name__ == "__main__":
    asyncio.run(main())
