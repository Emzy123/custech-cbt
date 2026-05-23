import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager, cache_manager
from cbt.services.authorization_service import AuthorizationService

async def main():
    await init_db()
    await redis_manager.connect()
    
    authz = AuthorizationService(cache_manager)
    
    # Examofficer user ID
    user_id = '6cfa02b4-1db7-44eb-a405-2dcaf7f21c6d'
    
    # Let's trace check_permission
    permission = "exam.create"
    # For POST /api/v1/examinations/
    # path.split("/") gives ['', 'api', 'v1', 'examinations', '']
    # index 1 is "api"
    resource_type = "api"
    resource_id = None
    
    print("=== Calling check_permission ===")
    has_permission = await authz.check_permission(
        user_id=user_id,
        permission=permission,
        resource_type=resource_type,
        resource_id=resource_id
    )
    print(f"Result: {has_permission}")
    
    # Let's fetch all permissions of the user directly
    user_permissions = await authz.get_user_permissions(user_id)
    print(f"\nUser permissions: {user_permissions}")
    print(f"Is '{permission}' in user_permissions?: {permission in user_permissions}")
    
    # Wait, let's check who the CURRENT user logged in actually is!
    # Let's check session or active logins in Redis?
    # No, let's look at the JWT token that the frontend might have sent.
    
    await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
