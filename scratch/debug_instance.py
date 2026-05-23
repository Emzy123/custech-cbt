import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager
from cbt.models.exam import ExamInstance
from cbt.services.exam_service import ExamService

async def debug_instance():
    await init_db()
    await redis_manager.connect()
    
    # Get all instances
    instances = await ExamInstance.find_all().to_list()
    print(f"Total instances in DB: {len(instances)}")
    for inst in instances:
        print(f"Instance ID: {inst.id}, student_id: {inst.student_id}, is_active: {getattr(inst, 'is_active', None)}, status: {inst.status}")
        
        # Test lookup by Beanie get()
        get_res = await ExamInstance.get(inst.id)
        print(f"  ExamInstance.get({inst.id}) found: {get_res is not None}")
        
        # Test lookup by find_one()
        find_res = await ExamInstance.find_one(ExamInstance.id == inst.id, ExamInstance.is_active == True)
        print(f"  find_one(id, is_active=True) found: {find_res is not None}")
        
        # Test service method
        try:
            service = ExamService(None)
            service_res = await service.get_exam_instance(inst.id)
            print(f"  ExamService.get_exam_instance({inst.id}) found: {service_res is not None}")
        except Exception as e:
            print(f"  ExamService.get_exam_instance failed: {e}")
            
    await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_instance())
