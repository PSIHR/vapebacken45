import os
import sys

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base
from database.db import engine
import asyncio


async def init_db():
    async with engine.begin() as conn:
        # Удаляем все существующие таблицы
        await conn.run_sync(Base.metadata.drop_all)
        # Создаем все таблицы заново
        await conn.run_sync(Base.metadata.create_all)
        print("База данных успешно инициализирована!")


if __name__ == "__main__":
    asyncio.run(init_db())
