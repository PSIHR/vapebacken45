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
    def clean_text(text: str) -> str:
        """Очистка текста от лишних символов и пробелов"""
        # Убираем переводы строк и табуляции
        text = re.sub(r'[\n\t]+', ' ', text)
        # Убираем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        # Убираем пробелы в начале и конце
        return text.strip()
    
    @staticmethod
    def parse_disposables(content: str) -> List[Dict]:
        """Парсинг одноразок"""
        products = []
        
        # Очищаем контент
        content = GoogleDocsParser.clean_text(content)
        
        # Паттерн для одноразок: название, тяги, цена
        # Пример: "HQD Cuvie Plus 1200 тяг 15 BYN"
        pattern = r'([A-Za-zА-Яа-я0-9\s\-]+?)\s+(\d+)\s*(?:тяг|тяги|puffs?)\s+(\d+(?:\.\d+)?)\s*BYN'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            name = GoogleDocsParser.clean_text(match.group(1))
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
        
        # Очищаем контент
        content = GoogleDocsParser.clean_text(content)
        
        # Паттерн для жидкостей: название, крепость, объем, цена
        # Пример: "MACKINTOSH 20mg 30ml 15 BYN"
        pattern = r'([A-Za-zА-Яа-я0-9\s\-]+?)\s+(\d+)\s*mg\s+(\d+)\s*ml\s+(\d+(?:\.\d+)?)\s*BYN'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            name = GoogleDocsParser.clean_text(match.group(1))
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
        
        # Очищаем контент
        content = GoogleDocsParser.clean_text(content)
        
        # Паттерн для снюса: название, крепость, цена
        pattern = r'([A-Za-zА-Яа-я0-9\s\-]+?)\s+(\d+)\s*mg\s+(\d+(?:\.\d+)?)\s*BYN'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            name = GoogleDocsParser.clean_text(match.group(1))
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
        
        # Разбиваем на строки
        lines = content.split('\n')
        
        current_name = None
        current_resistance = None
        
        # Паттерны для пропуска служебных строк
        skip_patterns = [
            'наименование', 'цена', 'фото', 'совместим', 'инструкция',
            'актуальный', 'ассортимент', 'никобустер', 'картриджи',
            'испарители', 'прочее', 'внешний вид', 'от изображения', 'om:', 'цена:'
        ]
        
        for line in lines:
            line = GoogleDocsParser.clean_text(line)
            
            if not line or len(line) < 3:
                continue
            
            # Пропускаем служебные строки
            if any(pattern in line.lower() for pattern in skip_patterns):
                continue
            
            # ПРИОРИТЕТ 1: Проверяем, есть ли в строке и название, и цена (single-line формат)
            # Паттерн: "Vaporesso XROS 0.6Ω 12 BYN" или "Vaporesso XROS 12 BYN"
            single_line_match = re.search(
                r'([A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9\s\-/]+?)\s+(?:([\d\.]+)\s*(?:Ω|Ohm|Om|ml|mg)\s+)?(\d+(?:\.\d+)?)\s*BYN',
                line,
                re.IGNORECASE
            )
            
            if single_line_match:
                name = GoogleDocsParser.clean_text(single_line_match.group(1))
                resistance = single_line_match.group(2) if single_line_match.group(2) else None
                price = float(single_line_match.group(3))
                
                # Проверяем что название валидное
                if name and len(name) > 3 and re.search(r'[A-Za-zА-Яа-я]{2,}', name):
                    if not re.match(r'^[\d\.\s]+(?:ml|mg|Ом|Ohm|Om)?$', name, re.IGNORECASE):
                        products.append({
                            'name': name,
                            'description': f'{name}' + (f' {resistance}' if resistance else ''),
                            'price': price
                        })
                
                # Сбрасываем состояние для multi-line парсинга
                current_name = None
                current_resistance = None
                continue
            
            # ПРИОРИТЕТ 2: Multi-line формат - проверяем, есть ли цена в строке
            price_match = re.search(r'(\d+(?:\.\d+)?)\s*BYN', line, re.IGNORECASE)
            
            if price_match:
                price = float(price_match.group(1))
                
                # Добавляем товар только если есть валидное название из предыдущих строк
                if current_name and len(current_name) > 3:
                    # Проверяем что название не является чисто характеристикой
                    if not re.match(r'^[\d\.\s]+(?:ml|mg|Ом|Ohm|Om)?$', current_name, re.IGNORECASE):
                        products.append({
                            'name': current_name,
                            'description': f'{current_name}' + (f' {current_resistance}' if current_resistance else ''),
                            'price': price
                        })
                
                current_name = None
                current_resistance = None
                    
            # ПРИОРИТЕТ 3: Проверяем, это чистая характеристика
            # Распознаем различные форматы: "0.6", "0.6Ω", "0.6 Ohm", "0.6Ω Mesh pod", "30ml", "20mg"
            elif re.match(r'^[\d\.\s]+(?:Ω|Ω|Ом|Ohm|Om|ml|mg)?(?:\s+(?:Mesh|pod|coil|Pod|Coil))?$', line, re.IGNORECASE):
                # Это характеристика - сохраняем ПОЛНОСТЬЮ (с единицами измерения)
                current_resistance = line  # Сохраняем полную строку, не только число
            
            # ПРИОРИТЕТ 4: Это название товара - должно содержать буквы и не быть чисто числовым
            elif re.search(r'[A-Za-zА-Яа-я]{2,}', line):
                # Дополнительная проверка: строка должна содержать хотя бы 2 буквы подряд
                if len(line) > 3:
                    current_name = line
        
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
