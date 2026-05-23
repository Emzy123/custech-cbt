import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.cbt.core.config import settings
from src.cbt.models.question import Question
from src.cbt.models.user import User
from src.cbt.schemas.question import QuestionResponse

async def main():
    client = AsyncIOMotorClient(
        settings.database_url or "mongodb://localhost:27017",
        uuidRepresentation="standard"
    )
    database = client[settings.database_name]
    await init_beanie(database=database, document_models=[Question, User])
    
    q = await Question.find_one()
    if q:
        print(f"Question in DB: {q}")
        try:
            resp = QuestionResponse.from_orm(q)
            print("Successfully converted to QuestionResponse!")
        except Exception as e:
            print(f"Error converting to QuestionResponse: {e}")
    else:
        print("No questions found in database")

if __name__ == "__main__":
    asyncio.run(main())
