
import asyncio
from sqlalchemy import select
from database.db import AsyncSessionLocal
from database.models import Category

async def update_category_images():
    """Обновляет изображения категорий"""
    async with AsyncSessionLocal() as session:
        # Получаем все категории
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        
        # Маппинг имен категорий на файлы изображений
        image_mapping = {
            "Жидкости": "uploads/zhidkosti.jpg",
            "Одноразки": "uploads/odnorazki.jpg",
            "Устройства": "uploads/ustroystva.jpg",
            "Поды": "uploads/pody.jpg",
        }
        
        updated = 0
        for category in categories:
            if category.name in image_mapping:
                category.image = image_mapping[category.name]
                updated += 1
                print(f"✅ Обновлена категория '{category.name}' -> {category.image}")
        
        await session.commit()
        print(f"\n✅ Всего обновлено категорий: {updated}")

if __name__ == "__main__":
    asyncio.run(update_category_images())
