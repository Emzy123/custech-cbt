"""
Seed script — creates the admin user in MongoDB.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.services.auth_service import AuthService
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import User


async def create_admin():
    admin_username = os.getenv("SEED_ADMIN_USERNAME", "admin")
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@custech.edu.ng")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "Admin123!")
    if not admin_password:
        raise ValueError(
            "SEED_ADMIN_PASSWORD is required. "
            "Set it in your shell or use the default before running the seed script."
        )

    # 1. Boot MongoDB + Beanie
    await init_db()
    # 2. Boot Redis
    await redis_manager.connect()

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
            user_agent='seed-script',
            date_of_birth=None,
            gender='OTHER',
            role='admin'
        )
        print(f'[OK] User created: id={user.id}')

        # Mark as verified
        await user.set({type(user).is_verified: True})
        print('[OK] Admin role assigned directly')

    except ValueError as e:
        if "already exists" in str(e):
            print("[INFO] Admin user already exists. Ensuring role is admin...")
            user = await auth_service._get_user_by_username(admin_username)

            if user:
                # Ensure verified and role is admin
                await user.set({
                    User.is_verified: True,
                    User.role: "admin"
                })
                print('[OK] Admin role and verification ensured')
            else:
                print('[ERROR] Could not find admin user')
        else:
            print(f'[ERROR] {e}')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'[ERROR] {type(e).__name__}: {e}')

    await redis_manager.disconnect()
    print('\n=== Admin Credentials ===')
    print(f'  Username : {admin_username}')
    print(f'  Password : {admin_password}')
    print('  Role     : admin')


if __name__ == "__main__":
    asyncio.run(create_admin())

