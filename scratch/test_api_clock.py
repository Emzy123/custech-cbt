import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.core.redis import redis_manager
from cbt.models.user import User
from cbt.models.student import Student
from cbt.models.exam import ExamInstance
from cbt.api.examinations import sync_clock, _ensure_instance_access

async def test_endpoint():
    await init_db()
    await redis_manager.connect()
    
    user = await User.find_one(User.username == "student")
    instance_id = "2febeae5-b25b-41a4-a45b-566404a234fa"
    
    print("Testing _ensure_instance_access...")
    try:
        instance = await _ensure_instance_access(instance_id, user)
        print("  ✓ Access allowed!")
    except Exception as e:
        print(f"  ✗ Access failed: {e}")
        import traceback
        traceback.print_exc()
        
    print("\nTesting sync_clock endpoint logic...")
    try:
        # We can call the api function directly. It takes exam_id, instance_id, db, current_user.
        # But wait, sync_clock API function is:
        # async def sync_clock(exam_id: str, instance_id: str, db: Any = Depends(get_db), current_user = Depends(get_current_active_user))
        res = await sync_clock(
            exam_id="be5bdb16-182f-4c6e-bd46-1dcbbd53cd3a",
            instance_id=instance_id,
            db=None,
            current_user=user
        )
        print(f"  ✓ sync_clock returned: {res}")
    except Exception as e:
        print(f"  ✗ sync_clock failed: {e}")
        if hasattr(e, "detail"):
            print(f"    Detail: {e.detail}")
        import traceback
        traceback.print_exc()
        
    await redis_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
