import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.cbt.models.user import User, UserRoleAssignment
from src.cbt.models.student import Student
from src.cbt.core.redis import cache_manager, redis_manager
from src.cbt.services.authorization_service import AuthorizationService

async def main():
    # Connect and init DB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.cbt_test, document_models=[User, UserRoleAssignment, Student])
    
    # Connect Redis
    await redis_manager.connect()
    
    # Initialize Authz Service
    authz = AuthorizationService(cache_manager)
    
    # Find student user
    user = await User.find_one(User.username == "test_student")
    if not user:
        print("User test_student not found!")
        return
        
    print(f"Checking permissions for User: {user.username} (ID: {user.id})")
    
    # First, let's clear the cache to ensure we get fresh DB values
    await authz.invalidate_user_cache(user.id)
    
    # Get user roles
    roles = await authz.get_user_roles(user.id)
    print(f"Roles: {roles}")
    
    # Get user permissions
    permissions = await authz.get_user_permissions(user.id)
    print(f"Permissions: {permissions}")
    
    # Check "exam.read" permission
    has_perm = await authz.check_permission(
        user_id=user.id,
        permission="exam.read",
        resource_type="examinations"
    )
    print(f"Has 'exam.read' permission: {has_perm}")
    
    await redis_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
