"""
Reset lecturer password to ensure it matches expected credentials.
"""
import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import User
from cbt.services.auth_service import AuthService
from cbt.core.security import security


async def reset_lecturer_password():
    await init_db()
    await redis_manager.connect()
    
    auth_service = AuthService(None, cache_manager, session_manager)
    
    # Find lecturer
    lecturer = await auth_service._get_user_by_username("lecturer")
    
    if not lecturer:
        print("[ERROR] Lecturer user not found!")
        await redis_manager.disconnect()
        return
    
    print(f"[OK] Found lecturer: {lecturer.username} (id={lecturer.id})")
    print(f"  Current email: {lecturer.email}")
    print(f"  Is active: {lecturer.is_active}")
    print(f"  Is verified: {lecturer.is_verified}")
    
    # Reset password
    new_password = "Lecturer123!"
    salt = security.generate_salt()
    password_hash = security.hash_password(new_password, salt)
    
    await lecturer.set({
        User.salt: salt,
        User.password_hash: password_hash,
        User.failed_login_attempts: 0,
        User.locked_until: None,
        User.is_active: True,
        User.is_verified: True
    })
    
    print(f"\n[OK] Password reset to: {new_password}")
    
    # Test login
    result = await auth_service.authenticate(
        username="lecturer",
        password=new_password,
        ip_address="127.0.0.1",
        user_agent="test",
        device_fingerprint="test"
    )
    
    if result.success:
        print("[OK] Login test PASSED")
    else:
        print(f"[ERROR] Login test FAILED: {result.error_message}")
    
    await redis_manager.disconnect()
    
    print("\n=== Lecturer Credentials ===")
    print("  Username : lecturer")
    print("  Password : Lecturer123!")
    print("  Email    : lecturer@custech.edu.ng")


if __name__ == "__main__":
    asyncio.run(reset_lecturer_password())
