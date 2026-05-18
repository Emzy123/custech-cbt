"""
Check users in database and verify lecturer/student exist with correct passwords.
"""
import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import User, UserRoleAssignment, UserRole
from cbt.services.auth_service import AuthService


async def check_users():
    await init_db()
    await redis_manager.connect()
    
    auth_service = AuthService(None, cache_manager, session_manager)
    
    print("=== Users in Database ===\n")
    
    users = await User.find_all().to_list()
    
    for user in users:
        print(f"User: {user.username}")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.full_name}")
        print(f"  Active: {user.is_active}")
        print(f"  Verified: {user.is_verified}")
        print(f"  Locked: {user.is_locked}")
        print(f"  Failed Attempts: {user.failed_login_attempts}")
        
        # Get roles
        roles = await UserRoleAssignment.find(
            UserRoleAssignment.user_id == str(user.id)
        ).to_list()
        role_names = [r.role.value for r in roles]
        print(f"  Roles: {role_names}")
        print()
    
    # Test authentication
    print("\n=== Testing Authentication ===\n")
    
    test_cases = [
        ("lecturer", "Lecturer123!"),
        ("student", "Student123!"),
    ]
    
    for username, password in test_cases:
        print(f"Testing {username}...")
        result = await auth_service.authenticate(
            username=username,
            password=password,
            ip_address="127.0.0.1",
            user_agent="test",
            device_fingerprint="test"
        )
        if result.success:
            print(f"  ✓ Login SUCCESS - Token: {result.token[:20]}...")
        else:
            print(f"  ✗ Login FAILED - {result.error_message}")
        print()
    
    await redis_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(check_users())
