import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Category, Item, Taste
from database.db import AsyncSessionLocal
import asyncio


async def add_sample_data():
    async with AsyncSessionLocal() as session:
        category1 = Category(name="Напитки")
        session.add(category1)
        
        category2 = Category(name="Десерты")
        session.add(category2)
        
        await session.flush()
        
        taste1 = Taste(name="Классическая")
        taste2 = Taste(name="Без сахара")
        taste3 = Taste(name="С мякотью")
        taste4 = Taste(name="Ванильное")
        taste5 = Taste(name="Шоколадное")
        
        session.add_all([taste1, taste2, taste3, taste4, taste5])
        await session.flush()
        
        item1 = Item(
            name="Кола",
            description="Освежающий напиток",
            price=100,
            category_id=category1.id,
            image="https://via.placeholder.com/300x300/3498db/ffffff?text=Кола"
        )
        item1.tastes.extend([taste1, taste2])
        session.add(item1)
        
        item2 = Item(
            name="Сок апельсиновый",
            description="Свежевыжатый сок",
            price=150,
            category_id=category1.id,
            image="https://via.placeholder.com/300x300/e67e22/ffffff?text=Сок"
        )
        item2.tastes.append(taste3)
        session.add(item2)
        
        item3 = Item(
            name="Мороженое",
            description="Ванильное мороженое",
            price=120,
            category_id=category2.id,
            image="https://via.placeholder.com/300x300/9b59b6/ffffff?text=Мороженое"
        )
        item3.tastes.extend([taste4, taste5])
        session.add(item3)
        
        item4 = Item(
            name="Торт шоколадный",
            description="Вкусный шоколадный торт",
            price=300,
            category_id=category2.id,
            image="https://via.placeholder.com/300x300/c0392b/ffffff?text=Торт"
        )
        session.add(item4)
        
        await session.commit()
        print("✅ Тестовые товары успешно добавлены!")
        print(f"- Категории: {category1.name}, {category2.name}")
        print(f"- Товары: {item1.name}, {item2.name}, {item3.name}, {item4.name}")


if __name__ == "__main__":
    asyncio.run(add_sample_data())
