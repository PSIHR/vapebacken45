"""
Парсер Google Docs для автоматической загрузки товаров
"""
import re
import aiohttp
from typing import List, Dict, Optional
from database.models import Item, Category
from database.db import AsyncSessionLocal
from sqlalchemy import select


class GoogleDocsParser:
    """Парсер для извлечения товаров из Google Docs"""
    
    CATEGORY_MAPPING = {
        'одноразки': 'Одноразки',
        'жижи': 'Жидкости',
        'жидкости': 'Жидкости',
        'снюс': 'Снюс',
        'расходники': 'Расходники',
    }
    
    @staticmethod
    def extract_doc_id(url: str) -> Optional[str]:
        """Извлечь ID документа из URL"""
        pattern = r'/document/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    @staticmethod
    async def fetch_doc_content(doc_id: str) -> str:
        """Получить содержимое документа в текстовом формате"""
        export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(export_url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    raise Exception(f"Не удалось получить документ: {response.status}")
    
    @staticmethod
    def parse_disposables(content: str) -> List[Dict]:
        """Парсинг одноразок"""
        products = []
        
        # Паттерн для одноразок: название, тяги, цена
        # Пример: "HQD Cuvie Plus 800 1200 тяг 15 BYN"
        pattern = r'([A-Za-z0-9\s]+?)\s+(\d+)\s*(?:тяг|puffs?)\s+(\d+(?:\.\d+)?)\s*BYN'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            name = match.group(1).strip()
            puffs = match.group(2)
            price = float(match.group(3))
            
            products.append({
                'name': name,
                'puffs': puffs,
                'price': price,
                'description': f'{name} - {puffs} тяг'
            })
        
        return products
    
    @staticmethod
    def parse_liquids(content: str) -> List[Dict]:
        """Парсинг жидкостей"""
        products = []
        
        # Паттерн для жидкостей: название, крепость, объем, цена
        # Пример: "MACKINTOSH 20mg 30ml 15 BYN"
        pattern = r'([A-Za-z0-9\s]+?)\s+(\d+)\s*mg\s+(\d+)\s*ml\s+(\d+(?:\.\d+)?)\s*BYN'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            name = match.group(1).strip()
            strength = match.group(2)
            volume = match.group(3)
            price = float(match.group(4))
            
            products.append({
                'name': name,
                'strength': f'{strength}mg',
                'tank_volume': f'{volume}ml',
                'price': price,
                'description': f'{name} {strength}mg {volume}ml'
            })
        
        return products
    
    @staticmethod
    def parse_snus(content: str) -> List[Dict]:
        """Парсинг снюса"""
        products = []
        
        # Паттерн для снюса: название, крепость, цена
        pattern = r'([A-Za-z0-9\s]+?)\s+(\d+)\s*mg\s+(\d+(?:\.\d+)?)\s*BYN'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            name = match.group(1).strip()
            strength = match.group(2)
            price = float(match.group(3))
            
            products.append({
                'name': name,
                'strength': f'{strength}mg',
                'price': price,
                'description': f'{name} {strength}mg'
            })
        
        return products
    
    @staticmethod
    def parse_accessories(content: str) -> List[Dict]:
        """Парсинг расходников"""
        products = []
        
        # Паттерн для расходников: название, параметры, цена
        # Пример: "Vaporesso xros 0.6 Ohm 12 BYN"
        pattern = r'([A-Za-z0-9\s]+?)\s+([\d\.]+)\s*(?:Ohm|Om|Ом)?\s+(\d+(?:\.\d+)?)\s*BYN'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            name = match.group(1).strip()
            resistance = match.group(2)
            price = float(match.group(3))
            
            products.append({
                'name': name,
                'description': f'{name} {resistance}Ω',
                'price': price
            })
        
        return products
    
    @staticmethod
    async def get_or_create_category(category_type: str) -> int:
        """Получить или создать категорию"""
        category_name = GoogleDocsParser.CATEGORY_MAPPING.get(category_type.lower(), category_type)
        
        async with AsyncSessionLocal() as session:
            # Проверяем существует ли категория
            result = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                # Создаем новую категорию
                category = Category(
                    name=category_name,
                    image='https://via.placeholder.com/300x200?text=' + category_name
                )
                session.add(category)
                await session.commit()
                await session.refresh(category)
            
            return category.id
    
    @staticmethod
    async def import_products(doc_url: str, category_type: str) -> Dict:
        """Импортировать товары из Google Docs"""
        try:
            # Извлекаем ID документа
            doc_id = GoogleDocsParser.extract_doc_id(doc_url)
            if not doc_id:
                return {'success': False, 'error': 'Неверная ссылка на документ'}
            
            # Получаем содержимое документа
            content = await GoogleDocsParser.fetch_doc_content(doc_id)
            
            # Парсим товары в зависимости от типа
            if category_type == 'одноразки':
                products = GoogleDocsParser.parse_disposables(content)
            elif category_type == 'жижи':
                products = GoogleDocsParser.parse_liquids(content)
            elif category_type == 'снюс':
                products = GoogleDocsParser.parse_snus(content)
            elif category_type == 'расходники':
                products = GoogleDocsParser.parse_accessories(content)
            else:
                return {'success': False, 'error': 'Неизвестный тип категории'}
            
            if not products:
                return {'success': False, 'error': 'Не удалось распознать товары в документе'}
            
            # Получаем или создаем категорию
            category_id = await GoogleDocsParser.get_or_create_category(category_type)
            
            # Добавляем товары в базу данных
            added_count = 0
            async with AsyncSessionLocal() as session:
                for product_data in products:
                    # Проверяем существует ли товар
                    result = await session.execute(
                        select(Item).where(Item.name == product_data['name'])
                    )
                    existing_item = result.scalar_one_or_none()
                    
                    if not existing_item:
                        item = Item(
                            name=product_data['name'],
                            description=product_data.get('description', ''),
                            price=product_data['price'],
                            category_id=category_id,
                            image='https://via.placeholder.com/300x300?text=' + product_data['name'].replace(' ', '+'),
                            strength=product_data.get('strength'),
                            puffs=product_data.get('puffs'),
                            tank_volume=product_data.get('tank_volume')
                        )
                        session.add(item)
                        added_count += 1
                
                await session.commit()
            
            return {
                'success': True,
                'added': added_count,
                'total': len(products),
                'category': category_type
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
