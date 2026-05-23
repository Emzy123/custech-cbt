import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document
from src.cbt.models.user import User, UserRoleAssignment
from src.cbt.models.student import Student
from src.cbt.core.config import settings

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    # Initialize Beanie with the test database
    await init_beanie(database=client.cbt_test, document_models=[User, UserRoleAssignment, Student])
    
    print("--- Users ---")
    users = await User.find_all().to_list()
    for u in users:
        print(f"User ID: {u.id}, Username: {u.username}, Active: {u.is_active}")
        
    print("\n--- User Role Assignments ---")
    assignments = await UserRoleAssignment.find_all().to_list()
    for a in assignments:
        print(f"Assignment - User ID: {a.user_id}, Role: {a.role}, Active: {a.is_active}")
        
    print("\n--- Students ---")
    students = await Student.find_all().to_list()
    for s in students:
        print(f"Student ID: {s.id}, User ID: {s.user_id}, Email: {s.email}")

if __name__ == "__main__":
    asyncio.run(main())
