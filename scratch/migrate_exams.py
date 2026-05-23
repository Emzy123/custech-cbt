import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.cbt_db
    exams_col = db.examinations
    
    print("--- Starting examinations data migration ---")
    cursor = exams_col.find()
    async for exam in cursor:
        exam_id = exam.get("_id")
        title = exam.get("title")
        updates = {}
        
        # 1. Course Code
        if exam.get("course_code") is None:
            updates["course_code"] = "GST101"
            
        # 2. Total Questions
        if exam.get("total_questions") is None:
            updates["total_questions"] = 0
            
        # 3. Scheduled Date
        # If scheduled_date is None, try to get the date part from start_time if it's a datetime
        start_time_val = exam.get("start_time")
        if exam.get("scheduled_date") is None:
            if isinstance(start_time_val, datetime):
                updates["scheduled_date"] = datetime(start_time_val.year, start_time_val.month, start_time_val.day, 0, 0, 0)
            else:
                updates["scheduled_date"] = datetime(2026, 5, 29, 0, 0, 0)
                
        # 4. Start Time & End Time
        if isinstance(start_time_val, datetime):
            start_str = start_time_val.strftime("%H:%M")
            updates["start_time"] = start_str
            # Calculate end_time based on duration (default 120 minutes)
            duration = exam.get("duration_minutes", 120) or 120
            end_hour = (start_time_val.hour + (duration // 60)) % 24
            end_minute = (start_time_val.minute + (duration % 60)) % 60
            updates["end_time"] = f"{end_hour:02d}:{end_minute:02d}"
        else:
            if exam.get("start_time") is None:
                updates["start_time"] = "09:00"
            if exam.get("end_time") is None:
                updates["end_time"] = "17:00"
                
        # 5. Is Active
        if exam.get("is_active") is None:
            updates["is_active"] = True
            
        if updates:
            print(f"Migrating Exam: '{title}' (ID: {exam_id})")
            for k, v in updates.items():
                print(f"  Setting {k} = {v} (type: {type(v)})")
            await exams_col.update_one({"_id": exam_id}, {"$set": updates})
            print("-" * 40)
            
    print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())
