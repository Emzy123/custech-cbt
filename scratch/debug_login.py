import asyncio
import sys
import traceback
from datetime import datetime

# Mock the settings and dependency imports
import pydantic
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

# Add src to python path if needed
sys.path.insert(0, "/home/purist/Desktop/projects/custech-cbt")

from src.cbt.core.config import settings
from src.cbt.models.user import User
from src.cbt.models.security import UserSession, AuditLog, SecurityEvent
from src.cbt.models.question import Question
from src.cbt.models.exam import Examination, ExamInstance, Result
from src.cbt.models.student import Student
from src.cbt.services.auth_service import AuthService
from src.cbt.core.redis import cache_manager, session_manager, redis_manager

async def debug_login():
    print("Initializing MongoDB...")
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["cbt_test"]
    
    # Wipe the users collection so we start fresh
    await db["users"].drop()
    await db["sessions"].drop()
    await db["audit_logs"].drop()
    
    await init_beanie(
        database=db,
        document_models=[
            User,
            Student,
            Question,
            Examination,
            ExamInstance,
            Result,
            AuditLog,
            UserSession,
            SecurityEvent
        ]
    )
    print("Beanie initialized.")
    
    # Connect to Redis
    print("Connecting to Redis...")
    await redis_manager.connect()
    
    auth_service = AuthService(
        db=db,
        cache=cache_manager,
        sessions=session_manager
    )
    
    # Register user
    print("Registering user...")
    try:
        user = await auth_service.register_user(
            username="debug_student",
            email="debug@student.edu",
            password="SecurePassword123!",
            first_name="Debug",
            last_name="User",
            phone_number=None,
            date_of_birth=None,
            gender=None,
            ip_address="127.0.0.1",
            user_agent="Mozilla",
            role="student",
            matric_number="2024999"
        )
        print("Registration successful:", user.id)
    except Exception as e:
        print("Registration failed!")
        traceback.print_exc()
        return

    # Authenticate user
    print("Authenticating user...")
    try:
        res = await auth_service.authenticate(
            username="debug_student",
            password="SecurePassword123!",
            ip_address="127.0.0.1",
            user_agent="Mozilla",
            device_fingerprint="fp123"
        )
        print("Auth result success:", res.success)
        print("Auth error message:", res.error_message)
        
        if res.success:
            print("Serializing with ProfileResponse...")
            from src.cbt.schemas.auth import ProfileResponse
            profile = ProfileResponse.from_orm(res.user)
            print("Serialization successful:", profile.full_name)
            
    except Exception as e:
        print("Authentication or serialization threw an exception!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_login())
