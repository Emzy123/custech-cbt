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
    
    user_id = '3b290e21-35e7-4225-acc6-d384a64ba772' # John Doe
    
    # Check cache first
    cache_key_perms = f"user_permissions:{user_id}"
    cache_key_roles = f"user_roles:{user_id}"
    
    cached_perms = await cache_manager.get(cache_key_perms)
    cached_roles = await cache_manager.get(cache_key_roles)
    
    print("=== Cached State ===")
    print(f"Cached Roles: {cached_roles}")
    print(f"Cached Perms: {cached_perms}")
    
    # Let's get them from service
    roles = await authz.get_user_roles(user_id)
    perms = await authz.get_user_permissions(user_id)
    
    print("\n=== Resolved State ===")
    print(f"Resolved Roles: {roles}")
    print(f"Resolved Perms: {perms}")
    print(f"Has 'question.read'?: {'question.read' in perms}")
    
    # Invalidate cache just in case to force reload
    print("\n=== Invalidating Cache ===")
    await authz.invalidate_user_cache(user_id)
    print("Cache invalidated.")
    
    # Get again after invalidation
    roles_after = await authz.get_user_roles(user_id)
    perms_after = await authz.get_user_permissions(user_id)
    
    print("\n=== Resolved State After Invalidation ===")
    print(f"Resolved Roles: {roles_after}")
    print(f"Resolved Perms: {perms_after}")
    print(f"Has 'question.read'?: {'question.read' in perms_after}")
    
    await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
