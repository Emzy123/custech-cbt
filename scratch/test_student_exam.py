import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager, cache_manager, session_manager
from cbt.models.user import User
from cbt.models.student import Student
from cbt.models.exam import Examination
from cbt.services.exam_service import ExamService

async def test_exam():
    await init_db()
    await redis_manager.connect()
    
    print("Finding student...")
    user = await User.find_one(User.username == "student")
    student = await Student.find_one(Student.user_id == str(user.id))
    print(f"Student: {student.first_name} {student.last_name} (ID: {student.id})")
    
    print("Finding examination...")
    exam = await Examination.find_one(Examination.is_active == True)
    if not exam:
        print("No active examination found!")
        await redis_manager.disconnect()
        return
    print(f"Examination: {exam.title} (ID: {exam.id})")
    
    exam_service = ExamService(None)
    
    print("\n--- Starting Exam Service Call ---")
    start_res = await exam_service.start_exam(str(exam.id), str(student.id), str(user.id))
    print(f"Start Exam Result: Success={start_res.success}, Message={start_res.message}, Attempt ID={start_res.attempt_id}")
    
    if start_res.success:
        print("\n--- Getting Paper Service Call ---")
        try:
            paper_res = await exam_service.get_paper(start_res.attempt_id)
            print(f"Get Paper Result: Exam Title={paper_res['exam']['course_title']}, Questions Count={len(paper_res['questions'])}")
        except Exception as e:
            print(f"Get Paper Failed: {e}")
            
    await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_exam())
