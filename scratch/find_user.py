import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.models.user import User, UserRoleAssignment

async def main():
    await init_db()
    user = await User.get('6aead157-1c86-4fbb-8ea9-1fb69ef964fc')
    if user:
        print(f"User: {user.username}")
        print(f"  Name: {user.full_name}")
        print(f"  Email: {user.email}")
        roles = await UserRoleAssignment.find(UserRoleAssignment.user_id == user.id).to_list()
        print(f"  Roles: {[r.role.value for r in roles]}")
    else:
        print("User not found!")

if __name__ == "__main__":
    asyncio.run(main())
