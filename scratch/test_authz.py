import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager, cache_manager
from cbt.models.user import User
from cbt.models.student import Student
from cbt.models.exam import ExamInstance
from cbt.services.authorization_service import AuthorizationService

async def test_authz():
    await init_db()
    await redis_manager.connect()
    
    # Student user
    user = await User.find_one(User.username == "student")
    student = await Student.find_one(Student.user_id == str(user.id))
    
    # Instance
    instance = await ExamInstance.find_one(ExamInstance.student_id == str(student.id))
    if not instance:
        print("No instance found for student")
        await redis_manager.disconnect()
        return
        
    print(f"User ID: {user.id}")
    print(f"Student ID: {student.id}")
    print(f"Instance ID: {instance.id}")
    print(f"Instance student_id: {instance.student_id}")
    
    # Step 1: get user permissions
    authz = AuthorizationService(cache_manager)
    permissions = await authz.get_user_permissions(str(user.id))
    print(f"User permissions: {permissions}")
    
    # Step 2: verify ownership
    print(f"student is not None: {student is not None}")
    print(f"instance.student_id: {instance.student_id} (type: {type(instance.student_id)})")
    print(f"student.id: {student.id} (type: {type(student.id)})")
    print(f"str(instance.student_id) == str(student.id): {str(instance.student_id) == str(student.id)}")
    
    await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_authz())
