"""
Seed script — creates the SUPER_ADMIN user in MongoDB.
"""
import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.services.auth_service import AuthService
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import UserRoleAssignment, UserRole


async def create_admin():
    # 1. Boot MongoDB + Beanie
    await init_db()
    # 2. Boot Redis
    await redis_manager.connect()

    auth_service = AuthService(None, cache_manager, session_manager)

    try:
        user = await auth_service.register_user(
            username='admin',
            email='admin@custech.edu.ng',
            password='Admin@CBT2024',
            first_name='System',
            last_name='Administrator',
            phone_number='+2348000000000',
            ip_address='127.0.0.1',
            user_agent='seed-script',
            date_of_birth=None,
            gender='OTHER'
        )
        print(f'[OK] User created: id={user.id}')

        # Mark as verified
        await user.set({type(user).is_verified: True})

        # Assign SUPER_ADMIN role
        role = UserRoleAssignment(
            user_id=user.id,
            role=UserRole.SUPER_ADMIN,
            granted_by='system'
        )
        await role.insert()
        print('[OK] SUPER_ADMIN role assigned')

    except ValueError as e:
        if "already exists" in str(e):
            print("[INFO] Admin user already exists. Ensuring role...")
            user = await auth_service._get_user_by_username('admin')

            if user:
                # Ensure verified
                if not user.is_verified:
                    await user.set({type(user).is_verified: True})

                # Check for existing role
                existing = await UserRoleAssignment.find_one(
                    UserRoleAssignment.user_id == user.id,
                    UserRoleAssignment.role == UserRole.SUPER_ADMIN
                )
                if not existing:
                    role = UserRoleAssignment(
                        user_id=user.id,
                        role=UserRole.SUPER_ADMIN,
                        granted_by='system'
                    )
                    await role.insert()
                    print('[OK] SUPER_ADMIN role assigned')
                else:
                    print('[OK] SUPER_ADMIN role already present')
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
    print('  Username : admin')
    print('  Password : Admin@CBT2024')
    print('  Role     : SUPER_ADMIN')


asyncio.run(create_admin())
