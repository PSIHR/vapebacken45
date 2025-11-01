from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Basket(Base):
    __tablename__ = "baskets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_price = Column(Float, default=0.0)

    # Связи
    items = relationship("BasketItem", back_populates="basket")
    user = relationship("DBUser", back_populates="basket")
    orders = relationship("Order", back_populates="basket")


class BasketItem(Base):
    __tablename__ = "basket_items"

    id = Column(Integer, primary_key=True, index=True)
    basket_id = Column(Integer, ForeignKey("baskets.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer, default=1)
    price = Column(Float)
    selected_taste = Column(String, nullable=True)

    basket = relationship("Basket", back_populates="items")
    item = relationship("Item")


class Taste(Base):
    __tablename__ = "tastes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    image = Column(String)


item_taste_association = Table(
    "item_taste_association",
    Base.metadata,
    Column("item_id", Integer, ForeignKey("items.id")),
    Column("taste_id", Integer, ForeignKey("tastes.id")),
)


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer)
    category_id = Column(Integer, ForeignKey("categories.id"))
    image = Column(String)

    # Связи
    category = relationship("Category", back_populates="items")
    tastes = relationship("Taste", secondary=item_taste_association)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    image = Column(String)

    # Связь с товарами
    items = relationship("Item", back_populates="category")


class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    point = Column(Integer, default=0)
    basket = relationship("Basket", back_populates="user", uselist=False)
    is_banned = Column(Boolean, default=False)

    orders = relationship("Order", back_populates="user")
    # Удаляем courier_orders, так как это создает циклическую зависимость
    # Вместо этого курьерские заказы можно получить через связь с Courier

    # Добавляем связь с Courier, если пользователь является курьером
    courier = relationship("Courier", back_populates="user", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_item = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    tastes = Column(String)
    selected_taste = Column(String)

    order = relationship("Order", back_populates="items")
    item = relationship("Item")


class Courier(Base):
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    username = Column(String)
    phone = Column(String, nullable=False)
    car_model = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    orders = relationship("Order", back_populates="courier")
    user = relationship("DBUser", back_populates="courier")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String, nullable=True)
    basket_id = Column(Integer, ForeignKey("baskets.id"), nullable=True)
    payment = Column(String, nullable=False)
    delivery = Column(String, nullable=False)
    address = Column(String, nullable=False)
    telephone = Column(String, nullable=False)
    total_price = Column(Float, nullable=False)
    discount = Column(Integer, default=0)
    promocode = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="waiting_for_courier")
    bot_message_ids = Column(JSON, default=list)
    courier_id = Column(
        Integer, ForeignKey("couriers.id")
    )  # Изменяем на ForeignKey к couriers.id

    user = relationship("DBUser", back_populates="orders")
    courier = relationship("Courier", back_populates="orders")

    items = relationship("OrderItem", back_populates="order")
    basket = relationship("Basket", back_populates="orders")


class OrderHistory(Base):
    __tablename__ = "orders_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Promocode(Base):
    __tablename__ = "promocodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    percentage = Column(Integer, nullable=False)
    is_active = Column(Boolean)
