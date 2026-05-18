"""
Seed script — creates sample EXAM_OFFICER and INVIGILATOR users.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.services.auth_service import AuthService
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import UserRoleAssignment, UserRole, User


# Default credentials (override with env vars)
DEFAULTS = {
    'exam_officer_username': os.getenv('SEED_EXAM_OFFICER_USERNAME', 'examofficer'),
    'exam_officer_email': os.getenv('SEED_EXAM_OFFICER_EMAIL', 'examofficer@custech.edu.ng'),
    'exam_officer_password': os.getenv('SEED_EXAM_OFFICER_PASSWORD', 'ExamOfficer123!'),
    'exam_officer_first': os.getenv('SEED_EXAM_OFFICER_FIRST', 'Michael'),
    'exam_officer_last': os.getenv('SEED_EXAM_OFFICER_LAST', 'Johnson'),
    
    'invigilator_username': os.getenv('SEED_INVIGILATOR_USERNAME', 'invigilator'),
    'invigilator_email': os.getenv('SEED_INVIGILATOR_EMAIL', 'invigilator@custech.edu.ng'),
    'invigilator_password': os.getenv('SEED_INVIGILATOR_PASSWORD', 'Invigilator123!'),
    'invigilator_first': os.getenv('SEED_INVIGILATOR_FIRST', 'Sarah'),
    'invigilator_last': os.getenv('SEED_INVIGILATOR_LAST', 'Williams'),
}


async def create_exam_officer(auth_service):
    """Create exam officer user with EXAM_OFFICER role."""
    
    try:
        user = await auth_service.register_user(
            username=DEFAULTS['exam_officer_username'],
            email=DEFAULTS['exam_officer_email'],
            password=DEFAULTS['exam_officer_password'],
            first_name=DEFAULTS['exam_officer_first'],
            last_name=DEFAULTS['exam_officer_last'],
            phone_number='+2348000000003',
            ip_address='127.0.0.1',
            user_agent='seed-script',
            date_of_birth=None,
            gender='MALE'
        )
        print(f"[OK] Exam Officer user created: {user.username} (id={user.id})")
        
        # Mark as verified
        await user.set({type(user).is_verified: True})
        
        # Assign EXAM_OFFICER role
        role = UserRoleAssignment(
            user_id=user.id,
            role=UserRole.EXAM_OFFICER,
            granted_by='system'
        )
        await role.insert()
        print('[OK] EXAM_OFFICER role assigned')
        
        return user
        
    except ValueError as e:
        if "already exists" in str(e):
            print(f"[INFO] Exam Officer user already exists")
            user = await auth_service._get_user_by_username(DEFAULTS['exam_officer_username'])
            
            if user:
                if not user.is_verified:
                    await user.set({type(user).is_verified: True})
                
                existing = await UserRoleAssignment.find_one(
                    UserRoleAssignment.user_id == user.id,
                    UserRoleAssignment.role == UserRole.EXAM_OFFICER
                )
                if not existing:
                    role = UserRoleAssignment(
                        user_id=user.id,
                        role=UserRole.EXAM_OFFICER,
                        granted_by='system'
                    )
                    await role.insert()
                    print('[OK] EXAM_OFFICER role assigned')
                else:
                    print('[OK] EXAM_OFFICER role already present')
                
                # Reset password to ensure it matches
                from cbt.core.security import security
                salt = security.generate_salt()
                password_hash = security.hash_password(DEFAULTS['exam_officer_password'], salt)
                await user.set({
                    User.salt: salt,
                    User.password_hash: password_hash,
                    User.failed_login_attempts: 0,
                    User.locked_until: None,
                    User.is_active: True,
                })
                print('[OK] Password reset to default')
            return user
        else:
            raise


async def create_invigilator(auth_service):
    """Create invigilator user with INVIGILATOR role."""
    
    try:
        user = await auth_service.register_user(
            username=DEFAULTS['invigilator_username'],
            email=DEFAULTS['invigilator_email'],
            password=DEFAULTS['invigilator_password'],
            first_name=DEFAULTS['invigilator_first'],
            last_name=DEFAULTS['invigilator_last'],
            phone_number='+2348000000004',
            ip_address='127.0.0.1',
            user_agent='seed-script',
            date_of_birth=None,
            gender='FEMALE'
        )
        print(f"[OK] Invigilator user created: {user.username} (id={user.id})")
        
        # Mark as verified
        await user.set({type(user).is_verified: True})
        
        # Assign INVIGILATOR role
        role = UserRoleAssignment(
            user_id=user.id,
            role=UserRole.INVIGILATOR,
            granted_by='system'
        )
        await role.insert()
        print('[OK] INVIGILATOR role assigned')
        
        return user
        
    except ValueError as e:
        if "already exists" in str(e):
            print(f"[INFO] Invigilator user already exists")
            user = await auth_service._get_user_by_username(DEFAULTS['invigilator_username'])
            
            if user:
                if not user.is_verified:
                    await user.set({type(user).is_verified: True})
                
                existing = await UserRoleAssignment.find_one(
                    UserRoleAssignment.user_id == user.id,
                    UserRoleAssignment.role == UserRole.INVIGILATOR
                )
                if not existing:
                    role = UserRoleAssignment(
                        user_id=user.id,
                        role=UserRole.INVIGILATOR,
                        granted_by='system'
                    )
                    await role.insert()
                    print('[OK] INVIGILATOR role assigned')
                else:
                    print('[OK] INVIGILATOR role already present')
                
                # Reset password to ensure it matches
                from cbt.core.security import security
                salt = security.generate_salt()
                password_hash = security.hash_password(DEFAULTS['invigilator_password'], salt)
                await user.set({
                    User.salt: salt,
                    User.password_hash: password_hash,
                    User.failed_login_attempts: 0,
                    User.locked_until: None,
                    User.is_active: True,
                })
                print('[OK] Password reset to default')
            return user
        else:
            raise


async def seed_officers():
    """Main seed function."""
    print("=" * 50)
    print("CBT System — Seed Exam Officer & Invigilator")
    print("=" * 50)
    
    # 1. Boot MongoDB + Beanie
    print("\n=== Connecting to database... ===")
    await init_db()
    await redis_manager.connect()
    print("[OK] Connected")
    
    # 2. Create auth service
    auth_service = AuthService(None, cache_manager, session_manager)
    
    # 3. Create Exam Officer
    print("\n=== Creating Exam Officer... ===")
    exam_officer = await create_exam_officer(auth_service)
    
    # 4. Create Invigilator
    print("\n=== Creating Invigilator... ===")
    invigilator = await create_invigilator(auth_service)
    
    # Cleanup
    await redis_manager.disconnect()
    
    # Print credentials
    print("\n" + "=" * 50)
    print("SEED COMPLETE — Credentials")
    print("=" * 50)
    print("\n--- EXAM OFFICER ---")
    print(f"  Username : {DEFAULTS['exam_officer_username']}")
    print(f"  Password : {DEFAULTS['exam_officer_password']}")
    print(f"  Email    : {DEFAULTS['exam_officer_email']}")
    print(f"  Name     : {DEFAULTS['exam_officer_first']} {DEFAULTS['exam_officer_last']}")
    print(f"  Role     : EXAM_OFFICER")
    print("\n--- INVIGILATOR ---")
    print(f"  Username : {DEFAULTS['invigilator_username']}")
    print(f"  Password : {DEFAULTS['invigilator_password']}")
    print(f"  Email    : {DEFAULTS['invigilator_email']}")
    print(f"  Name     : {DEFAULTS['invigilator_first']} {DEFAULTS['invigilator_last']}")
    print(f"  Role     : INVIGILATOR")
    print("=" * 50)
    print("\nUse these credentials to login via /api/v1/auth/login")


if __name__ == "__main__":
    asyncio.run(seed_officers())
