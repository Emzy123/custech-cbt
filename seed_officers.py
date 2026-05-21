"""
Seed script — creates sample Admin / Exam Officer user.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.services.auth_service import AuthService
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import User


# Default credentials (override with env vars)
DEFAULTS = {
    'exam_officer_username': os.getenv('SEED_EXAM_OFFICER_USERNAME', 'examofficer'),
    'exam_officer_email': os.getenv('SEED_EXAM_OFFICER_EMAIL', 'examofficer@custech.edu.ng'),
    'exam_officer_password': os.getenv('SEED_EXAM_OFFICER_PASSWORD', 'ExamOfficer123!'),
    'exam_officer_first': os.getenv('SEED_EXAM_OFFICER_FIRST', 'Michael'),
    'exam_officer_last': os.getenv('SEED_EXAM_OFFICER_LAST', 'Johnson'),
}


async def create_exam_officer(auth_service):
    """Create exam officer user with direct admin role."""
    
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
            gender='MALE',
            role='admin',
            department='Academic Affairs'
        )
        print(f"[OK] Exam Officer / Admin user created: {user.username} (id={user.id})")
        
        # Mark as verified
        await user.set({type(user).is_verified: True})
        print('[OK] Admin role assigned directly')
        
        return user
        
    except ValueError as e:
        if "already exists" in str(e):
            print(f"[INFO] Exam Officer user already exists")
            user = await auth_service._get_user_by_username(DEFAULTS['exam_officer_username'])
            
            if user:
                await user.set({
                    User.is_verified: True,
                    User.role: "admin",
                    User.department: "Academic Affairs"
                })
                print('[OK] Admin role/verification ensured')
            return user
        else:
            raise


async def seed_officers():
    """Main seed function."""
    print("=" * 50)
    print("CBT System — Seed Exam Officer / Admin")
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
    await create_exam_officer(auth_service)
    
    # Cleanup
    await redis_manager.disconnect()
    
    # Print credentials
    print("\n" + "=" * 50)
    print("SEED COMPLETE — Credentials")
    print("=" * 50)
    print("\n--- EXAM OFFICER / ADMIN ---")
    print(f"  Username : {DEFAULTS['exam_officer_username']}")
    print(f"  Password : {DEFAULTS['exam_officer_password']}")
    print(f"  Email    : {DEFAULTS['exam_officer_email']}")
    print(f"  Name     : {DEFAULTS['exam_officer_first']} {DEFAULTS['exam_officer_last']}")
    print(f"  Role     : admin")
    print("=" * 50)
    print("\nUse these credentials to login via /api/v1/auth/login")


if __name__ == "__main__":
    asyncio.run(seed_officers())
