import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.cbt.core.config import settings
from src.cbt.models.question import Question
from src.cbt.models.user import User
from src.cbt.schemas.question import QuestionResponse, QuestionSearch
from src.cbt.services.question_service import QuestionService

async def main():
    client = AsyncIOMotorClient(
        settings.database_url or "mongodb://localhost:27017",
        uuidRepresentation="standard"
    )
    database = client[settings.database_name]
    await init_beanie(database=database, document_models=[Question, User])
    
    service = QuestionService()
    search = QuestionSearch(limit=50)
    
    try:
        questions = await service.list_questions(search)
        print(f"Found {len(questions)} questions in list_questions query")
        serialized = [QuestionResponse.model_validate(q) for q in questions]
        print(f"Successfully serialized {len(serialized)} questions!")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
