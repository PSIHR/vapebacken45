import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import AsyncSessionLocal
from database.models import Category, Item, Taste


async def add_sample_data():
    async with AsyncSessionLocal() as session:
        categories_data = [
            {"id": 1, "name": "Одноразовые электронные сигареты"},
            {"id": 2, "name": "Жидкости"},
            {"id": 3, "name": "Поды"},
            {"id": 4, "name": "Устройства"},
        ]

        for cat_data in categories_data:
            existing = await session.get(Category, cat_data["id"])
            if not existing:
                category = Category(**cat_data)
                session.add(category)
                print(f"✅ Добавлена категория: {cat_data['name']}")
            else:
                print(f"⏭️  Категория уже существует: {cat_data['name']}")

        await session.commit()
        print("\n✨ Категории добавлены!")

        print("\n📝 Вы можете добавлять товары через Telegram бота в production")
        print("   Или создать отдельный тестовый бот для development")


if __name__ == "__main__":
    asyncio.run(add_sample_data())
