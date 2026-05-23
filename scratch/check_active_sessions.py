import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager, cache_manager
from cbt.models.user import User

async def main():
    await init_db()
    await redis_manager.connect()
    
    # Get all keys in Redis matching session:*
    redis_client = redis_manager.redis_client
    keys = await redis_client.keys("session:*")
    print(f"=== Active Sessions in Redis ({len(keys)}) ===")
    
    for key in keys:
        session_token = key.decode('utf-8').split(":")[1]
        session_data = await cache_manager.get(f"session:{session_token}")
        if session_data:
            user_id = session_data.get("user_id")
            user = await User.get(user_id)
            username = user.username if user else "Unknown"
            print(f"Session Token: {session_token[:10]}...")
            print(f"  User ID: {user_id}")
            print(f"  Username: {username}")
            print(f"  IP: {session_data.get('ip_address')}")
            print(f"  User Agent: {session_data.get('user_agent')}")
            print(f"  Biometric Verified: {session_data.get('biometric_verified')}")
        else:
            print(f"Session key {key.decode('utf-8')} has no cached data")
            
    # Let's also check active access tokens
    access_keys = await redis_client.keys("access_token:*")
    print(f"\n=== Active Access Tokens in Redis ({len(access_keys)}) ===")
    for key in access_keys:
        token = key.decode('utf-8').split(":")[1]
        user_id = await cache_manager.get(f"access_token:{token}")
        user = await User.get(user_id) if user_id else None
        username = user.username if user else "Unknown"
        print(f"Access Token: {token[:10]}... -> User: {username} (ID: {user_id})")
            
    await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
