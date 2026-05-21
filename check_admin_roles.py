import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.cbt.core.config import settings
from src.cbt.models.user import User

async def main():
    client = AsyncIOMotorClient(settings.database_url)
    await init_beanie(database=client[settings.database_name], document_models=[User])
    
    admin_user = await User.find_one(User.username == "admin")
    if not admin_user:
        print("Admin user not found")
        return
        
    print(f"Admin User ID: {admin_user.id}")
    print(f"Role (direct): {admin_user.role}")

if __name__ == "__main__":
    asyncio.run(main())
