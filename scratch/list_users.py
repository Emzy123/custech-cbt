import asyncio
import sys
sys.path.insert(0, 'src')

from cbt.core.database import init_db
from cbt.models.user import User

async def main():
    await init_db()
    users = await User.find_all().to_list()
    for u in users:
        print(f"ID: {u.id} | Username: {u.username} | Name: {u.full_name} | Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(main())
