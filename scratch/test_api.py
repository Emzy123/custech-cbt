import asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.cbt.main import app
from src.cbt.models.user import User, UserRoleAssignment, UserRole
from src.cbt.models.student import Student
from src.cbt.core.redis import cache_manager, redis_manager
from src.cbt.core.database import db_manager

async def main():
    # Connect and init DB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(database=client.cbt_test, document_models=[User, UserRoleAssignment, Student])
    await redis_manager.connect()
    
    sample_user_data = {
        "username": "test_student",
        "email": "test.user@university.edu",
        "password": "SecureTestPassword123!",
        "confirm_password": "SecureTestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "student",
        "department": "Computer Science",
        "matric_number": "202400001"
    }

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        # Register user
        reg_res = await test_client.post("/api/v1/auth/register", json=sample_user_data)
        print(f"Register status: {reg_res.status_code}")
        
        # Seed active student role assignment if it does not exist
        user = await User.find_one(User.username == sample_user_data["username"])
        if not user:
            print("User was not registered successfully!")
            return
            
        role_assignment = await UserRoleAssignment.find_one(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role == UserRole.STUDENT
        )
        if not role_assignment:
            role_assignment = UserRoleAssignment(
                user_id=user.id,
                role=UserRole.STUDENT,
                is_active=True
            )
            await role_assignment.insert()
            print("Seeded role assignment!")
            
        # Seed student profile document if it does not exist
        student = await Student.find_one(Student.user_id == user.id)
        if not student:
            student = Student(
                id="student-001",
                user_id=user.id,
                first_name=sample_user_data["first_name"],
                last_name=sample_user_data["last_name"],
                email=sample_user_data["email"],
                matric_number=sample_user_data["matric_number"],
                department_id="Computer Science",
                academic_session_id="2023/2024",
                admission_year=2020,
                current_level=400,
                graduated=False
            )
            await student.insert()
            print("Seeded student profile!")
            
        # Clear cache
        await cache_manager.delete(f"user_permissions:{user.id}")
        await cache_manager.delete(f"user_roles:{user.id}")
        
        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        log_res = await test_client.post("/api/v1/auth/login", json=login_data)
        print(f"Login status: {log_res.status_code}")
        token = log_res.json()["access_token"]
        
        # Make GET request
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        res = await test_client.get("/api/v1/examinations/my/results")
        print(f"GET /my/results status: {res.status_code}")
        print(f"Response: {res.text}")
        
    await redis_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
