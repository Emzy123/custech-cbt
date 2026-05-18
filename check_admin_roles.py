import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.cbt.core.config import settings
from src.cbt.models.user import User, UserRoleAssignment

async def main():
    client = AsyncIOMotorClient(settings.database_url)
    await init_beanie(database=client[settings.database_name], document_models=[User, UserRoleAssignment])
    
    admin_user = await User.find_one(User.username == "admin")
    if not admin_user:
        print("Admin user not found")
        return
        
    print(f"Admin User ID: {admin_user.id}")
    roles = await UserRoleAssignment.find(UserRoleAssignment.user_id == str(admin_user.id)).to_list()
    print(f"Roles: {[r.role for r in roles]}")

if __name__ == "__main__":
    asyncio.run(main())
