"""
Reset admin script — deletes ALL users and role assignments, then creates a fresh SUPER_ADMIN.
"""
import asyncio
import os
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.services.auth_service import AuthService
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import User, UserRoleAssignment, UserRole


async def reset_admin():
    # New admin credentials
    admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin")
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@custech.edu.ng")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "Admin123!")

    print("=== Connecting to database... ===")
    await init_db()
    await redis_manager.connect()
    print("[OK] Connected")

    # Delete ALL existing role assignments
    print("\n=== Deleting all role assignments... ===")
    role_count = 0
    async for role in UserRoleAssignment.find_all():
        await role.delete()
        role_count += 1
    print(f"[OK] Deleted {role_count} role assignments")

    # Delete ALL existing users
    print("\n=== Deleting all users... ===")
    user_count = 0
    async for user in User.find_all():
        await user.delete()
        user_count += 1
    print(f"[OK] Deleted {user_count} users")

    # Note: Cache entries will expire naturally (TTL 10 minutes for user roles)
    print("\n=== Cache status ===")
    print("[OK] Old cache entries will expire automatically")

    # Create fresh admin user
    print("\n=== Creating new admin user... ===")
    auth_service = AuthService(None, cache_manager, session_manager)

    try:
        user = await auth_service.register_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name='System',
            last_name='Administrator',
            phone_number='+2348000000000',
            ip_address='127.0.0.1',
            user_agent='reset-script',
            date_of_birth=None,
            gender='OTHER'
        )
        print(f"[OK] User created: id={user.id}")

        # Mark as verified
        await user.set({type(user).is_verified: True})
        print("[OK] User verified")

        # Assign SUPER_ADMIN role
        role = UserRoleAssignment(
            user_id=user.id,
            role=UserRole.SUPER_ADMIN,
            granted_by='system'
        )
        await role.insert()
        print("[OK] SUPER_ADMIN role assigned")

    except Exception as e:
        print(f"[ERROR] Failed to create admin: {e}")
        import traceback
        traceback.print_exc()

    await redis_manager.disconnect()

    print("\n" + "=" * 40)
    print("=== NEW ADMIN CREDENTIALS ===")
    print("=" * 40)
    print(f"  Username : {admin_username}")
    print(f"  Password : {admin_password}")
    print(f"  Email    : {admin_email}")
    print(f"  Role     : SUPER_ADMIN")
    print("=" * 40)
    print("\n[IMPORTANT] Change the password after first login!")


asyncio.run(reset_admin())
