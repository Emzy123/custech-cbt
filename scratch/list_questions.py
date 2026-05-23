import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.cbt.core.config import settings
from src.cbt.models.question import Question
from src.cbt.models.user import User

async def main():
    client = AsyncIOMotorClient(
        settings.database_url or "mongodb://localhost:27017",
        uuidRepresentation="standard"
    )
    database = client[settings.database_name]
    await init_beanie(database=database, document_models=[Question, User])
    
    query = Question.find(Question.is_active == True, Question.course_code == "CSC131")
    questions = await query.to_list()
    print(f"Beanie query returns: {len(questions)}")
    for q in questions[:10]:
        print(f"ID: {q.id}, Text: {q.question_text[:30]}, Course: {q.course_code}, Active: {q.is_active}")

if __name__ == "__main__":
    asyncio.run(main())
