from spirit.db.models import Base
from spirit.db.database import engine, init_db


async def init():
    await init_db()


if __name__ == "__main__":
    import asyncio
    asyncio.run(init())
    print("数据库初始化完成!")
