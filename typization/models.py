from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserRegisterModel(BaseModel):
    telegramId: int
    username: str | None = None


class ItemCreate(BaseModel):
    name: str
    description: str
    category_name: str
    price: int
    image: str
    tastes: List[str] = []


class BasketItemCreate(BaseModel):
    item_id: int
    quantity: int = 1
    selected_taste: Optional[str] = None


class BasketItemResponse(BaseModel):
    id: int
    item_id: int
    name: str
    image: str
    price: int
    quantity: int
    selected_taste: Optional[str] = None


class BasketResponse(BaseModel):
    user_id: int
    items: list[BasketItemResponse]
    total_price: float

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "items": [
                    {
                        "id": 1,
                        "item_id": 1,
                        "name": "Товар",
                        "image": "/image.jpg",
                        "price": 100,
                        "quantity": 2,
                        "selected_taste": "Клубника",  # Добавлено поле
                    }
                ],
                "total_price": 200,
            }
        }


class OrderItem(BaseModel):
    item_id: int
    name: str
    quantity: int
    price_per_item: float
    total_price: float


class OrderItemResponse(BaseModel):
    item_id: int
    name: str
    quantity: int
    price_per_item: int
    total_price: int
    tastes: List[str] = []


class OrderItemTaste(BaseModel):
    item_id: int
    selected_taste: Optional[str]


class OrderFromBasketCreate(BaseModel):
    payment: str
    delivery: str
    address: str
    telephone: str
    metro_line: Optional[str] = None
    metro_station: Optional[str] = None
    promocode: Optional[str] = None


class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItem]  # Список товаров в заказе
    payment: str
    delivery: str
    address: str  # Исправлено с "adress" на "address"
    telephone: str  # Изменено на String
    promocode: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    user_id: int
    items: List[OrderItemResponse]
    payment: str
    delivery: str
    address: str
    telephone: str
    metro_line: Optional[str] = None
    metro_station: Optional[str] = None
    total_price: int
    discount: int
    promocode: Optional[str] = None
    created_at: datetime


class SalesItem(BaseModel):
    name: str
    quantity: int
    selected_taste: Optional[str] = None
    price_per_item: float
    total_price: float


class Sale(BaseModel):
    id: int
    created_at: datetime
    user_id: int
    username: Optional[str]
    status: str
    total_price: float
    items: List[SalesItem]


class SalesResponse(BaseModel):
    period: dict
    turnover: float
    orders_count: int
    sales: List[Sale]
