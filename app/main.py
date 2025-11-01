import asyncio
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

import uvicorn
from aiogram.utils.markdown import text
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Body,
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Path,
    UploadFile,
    status,
)
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.middleware.cors import CORSMiddleware

from bot.bot import ADMINS, COURIERS, bot, dp, format_order_info, get_courier_keyboard
from database.db import engine, get_db
from database.models import (
    Base,
    Basket,
    BasketItem,
    Category,
    DBUser,
    Item,
    Order,
    OrderItem,
    Promocode,
    Taste,
    item_taste_association,
)
from middlewares.ban import BannedUserMiddleware
from typization.models import (
    BasketItemCreate,
    BasketResponse,
    OrderFromBasketCreate,
    OrderResponse,
    Sale,
    SalesItem,
    SalesResponse,
    UserRegisterModel,
)

if not load_dotenv("./config/.env.local"):
    raise Exception("Failed to load .env file")

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(level=os.getenv("LOG_LEVEL", "ERROR"))

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


async def save_upload_file(upload_file: UploadFile) -> str:
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await upload_file.read()
        buffer.write(content)

    return f"/uploads/{unique_filename}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    bot_task = asyncio.create_task(dp.start_polling(bot))

    yield

    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BannedUserMiddleware)


@app.get("/")
async def root():
    return {"message": "hello world"}


@app.get("/users/{user_id}/orders/", response_model=List[OrderResponse])
async def get_user_orders(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await db.execute(select(DBUser).where(DBUser.id == user_id))
    if not user.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    response = []
    for order in orders:
        order_items = []
        for item in order.items:
            tastes = item.tastes.split(", ") if item.tastes else []

            order_items.append(
                {
                    "id": item.id,
                    "item_id": item.item_id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "price_per_item": item.price_per_item,
                    "total_price": item.total_price,
                    "tastes": tastes,
                }
            )

        order_data = {
            "id": order.id,
            "user_id": order.user_id,
            "items": order_items,
            "payment": order.payment,
            "delivery": order.delivery,
            "address": order.address,
            "telephone": order.telephone,
            "total_price": order.total_price,
            "discount": order.discount,
            "promocode": order.promocode,
            "created_at": order.created_at,
        }
        response.append(order_data)

    return response


@app.post("/users/register")
async def register_user(
    user_data: UserRegisterModel,
    authorization: str = Header(
        None, description="Bearer token from Telegram (optional for testing)"
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        logger.info(f"Registering user: {user_data.dict()}")

        if authorization and not authorization.startswith("Bearer "):
            error_msg = f"Invalid Authorization header format. Expected: 'Bearer <token>', got: {authorization}"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=error_msg
            )

        telegram_id = user_data.telegramId
        logger.info(f"Checking if user {telegram_id} exists")

        result = await db.execute(select(DBUser).where(DBUser.id == telegram_id))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info(f"User {telegram_id} already exists")
            return {"status": "success", "message": "User already registered"}

        logger.info(f"Creating new user with ID: {telegram_id}")
        new_user = DBUser(
            id=telegram_id, 
            telegram_id=telegram_id,
            username=user_data.username,
            stamps=0,
            loyalty_level="White",
            total_items_purchased=0
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"Successfully created user {telegram_id}")

        return {
            "status": "success",
            "message": "User registered successfully",
            "user": {
                "id": new_user.id, 
                "username": new_user.username,
                "stamps": new_user.stamps,
                "loyalty_level": new_user.loyalty_level
            },
        }

    except Exception as e:
        logger.error(f"Error in register_user: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while registering user: {str(e)}",
        )


@app.get("/users/{telegram_id}/loyalty")
async def get_user_loyalty(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get user loyalty information including stamps, level, and discount percentage"""
    try:
        result = await db.execute(select(DBUser).where(DBUser.id == telegram_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Calculate discount percentage based on loyalty level
        discount_map = {
            "White": 25,
            "Platinum": 30,
            "Black": 35
        }
        
        return {
            "telegram_id": user.id,
            "username": user.username,
            "stamps": user.stamps,
            "loyalty_level": user.loyalty_level,
            "discount_percentage": discount_map.get(user.loyalty_level, 25),
            "total_items_purchased": user.total_items_purchased,
            "stamps_until_discount": 6 - user.stamps if user.stamps < 6 else 0
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user loyalty: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while getting user loyalty: {str(e)}",
        )


@app.post("/basket/{user_id}", response_model=BasketResponse)
async def create_or_get_basket(
    user_id: int = Path(..., title="User ID", gt=0),
    db: AsyncSession = Depends(get_db),
):
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User ID must be an integer",
        )

    # Get user for loyalty information
    user = await db.get(DBUser, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    result = await db.execute(select(Basket).where(Basket.user_id == user_id))
    basket = result.scalar_one_or_none()

    if not basket:
        basket = Basket(
            user_id=user_id, total_price=0.0
        )  # Инициализируем с total_price=0
        db.add(basket)
        await db.commit()
        await db.refresh(basket)

    result = await db.execute(
        select(BasketItem, Item)
        .join(Item, BasketItem.item_id == Item.id)
        .where(BasketItem.basket_id == basket.id)
    )
    items = result.all()

    total_price = 0.0
    basket_items = []
    
    # Calculate total items in basket
    total_items_in_basket = sum(basket_item.quantity for basket_item, _ in items)
    
    # Calculate how many items qualify for discount
    # Every 6 items (stamps + items in basket) = 1 discounted item
    total_qualifying_items = user.stamps + total_items_in_basket
    num_discounted_items = total_qualifying_items // 6  # Number of items that get discount
    
    # Setup loyalty discount
    discount_map = {"White": 25, "Platinum": 30, "Black": 35}
    loyalty_discount_percentage = discount_map.get(user.loyalty_level, 25)
    loyalty_discount_applied = num_discounted_items > 0
    
    # Sort items by price (descending) to apply discount to most expensive first
    sorted_items = sorted(items, key=lambda x: x[1].price, reverse=True)
    
    # Track how many discounts we've applied
    remaining_discounts = num_discounted_items
    discount_allocation = {}  # basket_item_id -> quantity_with_discount

    # Distribute discounts across items, starting with most expensive
    for basket_item, item in sorted_items:
        if remaining_discounts <= 0:
            break
        
        # Apply discount to min(remaining_discounts, basket_item.quantity) units
        discounted_qty = min(remaining_discounts, basket_item.quantity)
        discount_allocation[basket_item.id] = discounted_qty
        remaining_discounts -= discounted_qty

    # Now build the basket items list with correct pricing
    for basket_item, item in items:
        discounted_quantity = discount_allocation.get(basket_item.id, 0)
        regular_quantity = basket_item.quantity - discounted_quantity
        
        # Calculate total price for this basket item
        regular_price = item.price * regular_quantity
        discounted_price_per_unit = item.price * (100 - loyalty_discount_percentage) / 100
        discounted_price = discounted_price_per_unit * discounted_quantity
        item_total = regular_price + discounted_price
        
        total_price += item_total
        basket_items.append(
            {
                "id": basket_item.id,
                "item_id": item.id,
                "name": item.name,
                "image": item.image,
                "price": item.price,
                "discounted_price": discounted_price_per_unit if discounted_quantity > 0 else None,
                "discount_percentage": loyalty_discount_percentage if discounted_quantity > 0 else 0,
                "discounted_quantity": discounted_quantity,
                "quantity": basket_item.quantity,
                "selected_taste": basket_item.selected_taste,
            }
        )

    basket.total_price = total_price
    await db.commit()
    await db.refresh(basket)

    return {
        "user_id": user_id, 
        "items": basket_items, 
        "total_price": total_price,
        "loyalty_discount_applied": loyalty_discount_applied,
        "loyalty_discount_percentage": loyalty_discount_percentage if loyalty_discount_applied else 0
    }


@app.post("/basket/{user_id}/items", response_model=BasketResponse)
async def add_to_basket(
    user_id: int = Path(..., title="User ID", gt=0),
    item_data: BasketItemCreate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await db.get(DBUser, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {user_id} не найден",
            )

        item = await db.get(Item, item_data.item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с ID {item_data.item_id} не найден",
            )

        basket = await db.scalar(
            select(Basket)
            .where(Basket.user_id == user_id)
            .options(selectinload(Basket.items))
        )

        if not basket:
            basket = Basket(user_id=user_id, total_price=0)
            db.add(basket)
            await db.commit()
            await db.refresh(basket)
            basket = await db.scalar(
                select(Basket)
                .where(Basket.user_id == user_id)
                .options(selectinload(Basket.items))
            )

        existing_item = None
        for bi in basket.items:
            if (
                bi.item_id == item_data.item_id
                and bi.selected_taste == item_data.selected_taste
            ):
                existing_item = bi
                break

        if existing_item:
            existing_item.quantity += item_data.quantity
        else:
            new_item = BasketItem(
                basket_id=basket.id,
                item_id=item_data.item_id,
                quantity=item_data.quantity,
                price=item.price,
                selected_taste=item_data.selected_taste,
            )
            db.add(new_item)

        basket.total_price = sum(item.quantity * item.price for item in basket.items)

        await db.commit()
        await db.refresh(basket)

        return await create_or_get_basket(user_id, db)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при добавлении товара в корзину: {str(e)}",
        )


@app.delete("/basket/{user_id}/items/{item_id}", response_model=BasketResponse)
async def remove_from_basket(
    user_id: int = Path(..., gt=0),
    item_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Basket).where(Basket.user_id == user_id))
    basket = result.scalar_one_or_none()

    if not basket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Basket not found"
        )

    result = await db.execute(
        select(BasketItem, Item)
        .join(Item, BasketItem.item_id == Item.id)
        .where(BasketItem.basket_id == basket.id)
        .where(BasketItem.item_id == item_id)
    )
    basket_item_with_item = result.first()

    if not basket_item_with_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in basket"
        )

    basket_item, item = basket_item_with_item
    basket.total_price -= item.price * basket_item.quantity

    await db.delete(basket_item)
    await db.commit()
    return await create_or_get_basket(user_id, db)


@app.get("/items/")
async def read_items(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Item).options(
            selectinload(Item.category),
            selectinload(Item.tastes),
        )
    )
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "image": item.image,
                "price": item.price,
                "category": {"id": item.category.id, "name": item.category.name}
                if item.category
                else None,
                "tastes": [
                    {
                        "id": taste.id,
                        "name": taste.name,
                        "image": taste.image,
                    }
                    for taste in item.tastes
                ]
                if item.tastes
                else None,
                "strength": item.strength,
                "puffs": item.puffs,
                "vg_pg": item.vg_pg,
                "tank_volume": item.tank_volume,
            }
            for item in items
        ]
    }


@app.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_data: dict,  # Например: {"status": "in_delivery"}
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    new_status = status_data.get("status")
    if new_status not in [
        "waiting_for_courier",
        "in_delivery",
        "delivered",
        "completed",
        "canceled",
    ]:
        raise HTTPException(status_code=400, detail="Некорректный статус")

    order.status = new_status
    await db.commit()

    # Отправляем уведомление пользователю
    status_messages = {
        "waiting_for_courier": "⏳ Ожидает курьера",
        "in_delivery": "🚗 В процессе доставки",
        "delivered": "✅ Доставлен",
        "completed": "🏁 Завершен",
        "canceled": "❌ Отменен",
    }

    try:
        await bot.send_message(
            chat_id=order.user_id,
            text=f"🔄 Статус вашего заказа #{order_id} изменен:\n{status_messages[new_status]}",
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {str(e)}")

    return {"message": "Статус обновлен"}


async def notify_couriers_about_new_order(order: Order, db: AsyncSession):
    """Отправляет уведомление всем курьерам о новом заказе"""
    try:
        logger.info(f"Processing notification for order {order.id}")

        # 1. Получаем информацию о пользователе
        user = await db.get(DBUser, order.user_id)
        if not user:
            logger.warning(f"User {order.user_id} not found for order {order.id}")
            return

        username = user.username
        logger.debug(f"Username: {username} for order {order.id}")

        # 2. Получаем количество заказов пользователя
        orders_count = (
            await db.scalar(
                select(func.count(Order.id)).where(Order.user_id == order.user_id)
            )
            if order.user_id
            else 0
        )
        logger.debug(f"User order count: {orders_count}")

        # 3. Получаем товары заказа
        order_items = await db.execute(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .options(selectinload(OrderItem.item))
        )
        order_items = order_items.scalars().all()

        if not order_items:
            logger.warning(f"No items in order {order.id}")
            return

        # 4. Функция для полного экранирования MarkdownV2
        def escape_markdown(text: str) -> str:
            """Экранирует спецсимволы для Telegram MarkdownV2"""

        escape_chars = r"\_*[]()~`>#+-=|{}.!"
        return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", str(text))

        # 5. Формируем текст состава заказа
        items_text = "\n".join(
            f"• {escape_markdown_v2(item.item.name)} x{escape_markdown_v2(str(item.quantity))} - {escape_markdown_v2(str(item.price_per_item))}₽"
            for item in order_items
        )
        logger.debug(f"Order items text: {items_text}")

        # 6. Определяем статус клиента (эмодзи не экранируем)
        if orders_count <= 1:
            client_status = "🆕 Новый клиент"
        elif 2 <= orders_count <= 5:
            client_status = f"🟢 Постоянный ({orders_count} заказов)"
        else:
            client_status = f"⭐ VIP клиент ({orders_count} заказов)"

        # Экранируем только текст в скобках
        client_status = client_status.replace("(", "\\(").replace(")", "\\)")

        # 7. Форматируем дату с экранированием точек
        order.created_at.strftime("%d\\.%m\\.%Y %H:%M")

        # 8. Формируем сообщение

        order_info = (
            f"📋 *ИНФОРМАЦИЯ О ЗАКАЗЕ*\n\n"
            f"🆔 *Номер:* {escape_markdown(str(order.id))}\n"
            f"👤 *Клиент:* @{escape_markdown(username)}\n"
            f"🔹 *Статус клиента:* {escape_markdown(client_status)}\n"
            f"📦 *Состав заказа:*\n"
            f"```\n{items_text}\n```\n"
            f"💰 *СУММА:* {escape_markdown(str(order.total_price))}₽\n"
            f"📊 *Статус:* {escape_markdown(status_emojis.get(order.status, order.status))}\n"
            f"📞 *Телефон:* {escape_markdown(order.telephone)}\n\n"
            f"📅 *Дата:* {escape_markdown(order.created_at.strftime('%d.%m.%Y %H:%M'))}\n"
            f"🏠 *Адрес:* {escape_markdown(order.address)}\n"
            f"🚚 *Способ доставки:* {escape_markdown(order.delivery)}\n\n"
        )

        # 9. Отправляем уведомление
        for courier_id in COURIERS:
            try:
                logger.info(f"Sending notification to courier {courier_id}")
                await bot.send_message(
                    chat_id=courier_id,
                    text=f"🚀 Поступил новый заказ\\!\n\n{order_info}",
                    parse_mode="MarkdownV2",
                    reply_markup=get_courier_keyboard(order.id, order.status),
                )
                logger.info(f"Notification sent to courier {courier_id}")
            except Exception as e:
                logger.error(f"Error sending to courier {courier_id}: {str(e)}")
                # Fallback без Markdown
                cleaned_client_status = client_status.replace("\\", "")
                try:
                    plain_text = (
                        f"Поступил новый заказ!\n\n"
                        f"Номер: {order.id}\n"
                        f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                        f"Сумма: {order.total_price}₽\n"
                        f"Статус: {order.status}\n\n"
                        f"Клиент: @{username or 'не указан'}\n"
                        f"Статус клиента: {cleaned_client_status}\n"
                        f"Телефон: {order.telephone}\n\n"
                        f"Адрес: {order.address}\n"
                        f"Способ доставки: {order.delivery}\n\n"
                        f"Состав заказа:\n{items_text.replace('`', '')}"
                    )
                    await bot.send_message(
                        chat_id=courier_id,
                        text=plain_text,
                        parse_mode=None,
                        reply_markup=get_courier_keyboard(order.id, order.status),
                    )
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback failed for courier {courier_id}: {str(fallback_error)}"
                    )

    except Exception as e:
        logger.error(
            f"Critical error in notify_couriers_about_new_order: {str(e)}",
            exc_info=True,
        )


async def notify_couriers_about_new_order(order: Order, db: AsyncSession):
    """Отправляет уведомление о новом заказе всем курьерам и админам"""
    try:
        # Объединяем списки админов и курьеров, убираем дубликаты
        recipients = set(COURIERS) | set(ADMINS)

        # Загружаем связанные данные в одном запросе
        order_with_items = await db.execute(
            select(Order)
            .where(Order.id == order.id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.item),
                selectinload(Order.user),
            )
        )
        order = order_with_items.scalar_one()

        # Получаем количество заказов пользователя
        orders_count = (
            await db.scalar(
                select(func.count(Order.id)).where(Order.user_id == order.user_id)
            )
            or 0
        )

        # Форматируем информацию о заказе
        order_info = format_order_info(
            order, orders_count, order.user.username if order.user else None
        )

        # Отправляем каждому получателю
        for recipient_id in recipients:
            try:
                await bot.send_message(
                    chat_id=recipient_id,
                    text=order_info,
                    parse_mode="MarkdownV2",
                    reply_markup=get_courier_keyboard(order.id, "waiting_for_courier"),
                )
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке уведомления о заказе {order.id} пользователю {recipient_id}: {e}"
                )
    except Exception as e:
        logger.error(f"Ошибка при подготовке уведомлений о заказе {order.id}: {e}")
        raise


@app.post("/orders/from_basket/{user_id}", response_model=OrderResponse)
async def create_order_from_basket(
    user_id: int,
    order_data: OrderFromBasketCreate,
    x_user_id: str = Header(None, description="ID user from Telegram"),
    db: AsyncSession = Depends(get_db),
):
    """
    Создает заказ из корзины пользователя с сохранением выбранных вкусов
    """
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header missing")

    try:
        # 1. Проверяем существование пользователя
        user = await db.get(DBUser, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с ID {user_id} не найден",
            )

        # 2. Получаем корзину с полной информацией о товарах и вкусах
        basket = await db.scalar(
            select(Basket)
            .where(Basket.user_id == user_id)
            .options(
                selectinload(Basket.items)
                .selectinload(BasketItem.item)
                .selectinload(Item.tastes)
            )
        )

        if not basket or not basket.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Корзина пользователя пуста",
            )

        # 3. Создаем новый заказ
        order = Order(
            user_id=user_id,
            username=user.username,
            basket_id=basket.id,
            payment=order_data.payment,
            delivery=order_data.delivery,
            address=order_data.address,
            telephone=f"@{user.username}" if user.username else None,
            metro_line=order_data.metro_line,
            metro_station=order_data.metro_station,
            preferred_time=order_data.preferred_time,
            time_slot=order_data.time_slot,
            delivery_cost=order_data.delivery_cost or 0.0,
            total_price=0,  # Временное значение, будет пересчитано
            discount=0,
            promocode=order_data.promocode,
            status="waiting_for_courier",
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

        # 4. Переносим товары из корзины в заказ с сохранением вкусов
        total_price = 0
        order_items = []

        for basket_item in basket.items:
            # Получаем полную информацию о товаре
            item = await db.get(Item, basket_item.item_id)
            if not item:
                continue  # Пропускаем если товар не найден

            # Рассчитываем стоимость позиции
            item_total = basket_item.price * basket_item.quantity

            # Создаем запись о товаре в заказе
            order_item = OrderItem(
                order_id=order.id,
                item_id=item.id,
                name=item.name,
                quantity=basket_item.quantity,
                price_per_item=basket_item.price,
                total_price=item_total,
                selected_taste=basket_item.selected_taste,  # Сохраняем выбранный вкус
            )
            db.add(order_item)

            # Формируем информацию о товаре для ответа
            order_items.append(
                {
                    "item_id": item.id,
                    "name": item.name,
                    "quantity": basket_item.quantity,
                    "price_per_item": basket_item.price,
                    "total_price": item_total,
                    "selected_taste": basket_item.selected_taste,
                    "tastes": [taste.name for taste in item.tastes]
                    if item.tastes
                    else [],
                }
            )

            total_price += item_total

        # 5. Применяем промокод если указан
        if order_data.promocode:
            promo = await db.scalar(
                select(Promocode)
                .where(Promocode.name == order_data.promocode)
                .where(Promocode.is_active)
            )
            if promo:
                order.discount = promo.percentage
                total_price = total_price * (100 - promo.percentage) / 100

        # 6. Добавляем стоимость доставки и обновляем итоговую стоимость заказа
        total_price += order.delivery_cost
        order.total_price = total_price
        await db.commit()

        # 7. Отправляем уведомление пользователю
        try:
            items_text = "\n".join(
                f"• {item['name']}"
                + (f" ({item['selected_taste']})" if item["selected_taste"] else "")
                + f" x{item['quantity']} - {item['total_price']}₽"
                for item in order_items
            )

            delivery_info = ""
            if order.delivery_cost > 0:
                delivery_info = f"🚚 Доставка: {order.delivery_cost} BYN\n"
            
            time_info = ""
            if order.preferred_time:
                time_info = f"⏰ Время: {order.preferred_time}\n"
            elif order.time_slot:
                time_info = f"⏰ Время: {order.time_slot}\n"
            
            message_text = (
                f"🛒 Ваш заказ №{order.id} принят!\n\n"
                f"📦 Состав заказа:\n{items_text}\n\n"
                f"{delivery_info}"
                f"💰 Итого: {order.total_price} BYN\n"
                f"🚚 Способ доставки: {order.delivery}\n"
                f"🏠 Адрес: {order.address}\n"
                f"{time_info}\n"
            )

            await bot.send_message(chat_id=user_id, text=message_text)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю: {str(e)}")

        # 8. Уведомляем курьеров и админов
        try:
            await notify_couriers_about_new_order(order, db)
        except Exception as e:
            logger.error(f"Ошибка при уведомлении курьеров: {str(e)}")

        # 9. Обновляем программу лояльности
        total_items_in_order = sum(item['quantity'] for item in order_items)
        user.total_items_purchased += total_items_in_order
        user.stamps += total_items_in_order
        
        # Проверяем, нужно ли повысить уровень лояльности
        while user.stamps >= 6:
            user.stamps -= 6  # Сбрасываем 6 штампов
            
            # Повышаем уровень лояльности
            if user.loyalty_level == "White":
                user.loyalty_level = "Platinum"
                logger.info(f"User {user_id} upgraded to Platinum level")
            elif user.loyalty_level == "Platinum":
                user.loyalty_level = "Black"
                logger.info(f"User {user_id} upgraded to Black level")
            # Black level остается навсегда
        
        await db.commit()

        # 10. Очищаем корзину
        await db.execute(delete(BasketItem).where(BasketItem.basket_id == basket.id))
        basket.total_price = 0
        await db.commit()

        # 11. Формируем ответ
        return {
            "id": order.id,
            "user_id": order.user_id,
            "items": order_items,
            "payment": order.payment,
            "delivery": order.delivery,
            "address": order.address,
            "telephone": order.telephone,
            "total_price": order.total_price,
            "discount": order.discount,
            "promocode": order.promocode,
            "created_at": order.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при создании заказа: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при создании заказа",
        )


@app.post("/promocodes/")
async def create_promocode(
    name: str, percentage: int, db: AsyncSession = Depends(get_db)
):
    # Проверяем, существует ли уже промокод с таким именем
    existing_promo = await db.execute(select(Promocode).where(Promocode.name == name))
    if existing_promo.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Promocode with this name already exists",
        )

    # Создаем новый промокод
    new_promo = Promocode(name=name, percentage=percentage)
    db.add(new_promo)
    await db.commit()
    await db.refresh(new_promo)

    return {
        "message": "Promocode created successfully",
        "promocode": {
            "id": new_promo.id,
            "name": new_promo.name,
            "percentage": new_promo.percentage,
        },
    }


@app.get("/get_promo")
async def read_promocodes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Promocode))
    promocodes = result.scalars().all()

    return {
        "status": "success",
        "data": {
            "promocodes": [
                {
                    "id": promocode.id,
                    "name": promocode.name,  # Исправлено с name на code
                    "percentage": promocode.percentage,
                }
                for promocode in promocodes
            ]
        },
    }


@app.post("/create_items/")
async def create_item(
    name: str = Form(...),
    description: str = Form(...),
    category_name: str = Form(...),
    price: int = Form(...),
    image: str = Form(""),
    tastes: str = Form("[]"),
    file_image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        import json

        # Обрабатываем изображение
        image_path = None
        if file_image:
            # Проверяем тип файла
            if not file_image.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400, detail="Файл должен быть изображением"
                )
            # Сохраняем файл
            image_path = await save_upload_file(file_image)
        else:
            # Если файл не загружен, используем строку из image
            image_path = image if image else ""

        # Парсим tastes из строки
        tastes_list = []
        if tastes:
            # Пробуем сначала как JSON
            try:
                tastes_list = json.loads(tastes)
            except json.JSONDecodeError:
                # Если не JSON, то парсим как строку с запятыми
                if "," in tastes:
                    tastes_list = [
                        taste.strip().strip('"').strip("'")
                        for taste in tastes.split(",")
                    ]
                else:
                    tastes_list = [tastes.strip().strip('"').strip("'")]

        async with db.begin_nested():
            category = await db.scalar(
                select(Category).where(Category.name == category_name)
            )
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")

        new_item = Item(
            name=name,
            description=description,
            price=price,
            category_id=category.id,
            image=image_path,
        )
        db.add(new_item)
        await db.flush()

        if tastes_list:
            existing_tastes = (
                (await db.execute(select(Taste).where(Taste.name.in_(tastes_list))))
                .scalars()
                .all()
            )

            existing_names = {t.name for t in existing_tastes}
            new_tastes = []
            for taste_name in tastes_list:
                if taste_name not in existing_names:
                    new_taste = Taste(name=taste_name)
                    new_tastes.append(new_taste)
                    db.add(new_taste)

            await db.flush()

            stmt = item_taste_association.insert().values(
                [
                    {"item_id": new_item.id, "taste_id": t.id}
                    for t in [*existing_tastes, *new_tastes]
                ]
            )
            await db.execute(stmt)

        await db.commit()

        result = await db.execute(
            select(Item)
            .where(Item.id == new_item.id)
            .options(selectinload(Item.tastes))
        )
        created_item = result.scalar_one()

        return {
            "message": "Item created successfully",
            "item": created_item,
            "image_path": image_path,
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")


@app.post("/make_category")
async def create_category(
    name: str, image: UploadFile = File(None), db: AsyncSession = Depends(get_db)
):
    try:
        # Обрабатываем изображение
        image_path = None
        if image:
            # Проверяем тип файла
            if not image.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400, detail="Файл должен быть изображением"
                )
            # Сохраняем файл
            image_path = await save_upload_file(image)
        else:
            # Если файл не загружен, используем пустую строку
            image_path = ""

        existing_category = await db.execute(
            select(Category).where(Category.name == name)
        )
        if existing_category.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail=f"Category '{name}' already exists"
            )

        new_category = Category(name=name, image=image_path)
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)

        return {
            "message": "Category created successfully",
            "category": {
                "id": new_category.id,
                "name": new_category.name,
                "image_path": image_path,
            },
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating category: {str(e)}"
        )


@app.put("/update_item_image/{item_id}")
async def update_item_image(
    item_id: int, image: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """
    Обновляет изображение существующего товара
    """
    try:
        # Проверяем тип файла
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")

        # Находим товар
        item = await db.execute(
            select(Item).where(Item.id == item_id).options(selectinload(Item.category))
        )
        item = item.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Сохраняем новый файл
        image_path = await save_upload_file(image)

        # Обновляем путь к изображению
        item.image = image_path
        await db.commit()
        await db.refresh(item)

        return {
            "message": "Item image updated successfully",
            "item": {"id": item.id, "name": item.name, "image_path": image_path},
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error updating item image: {str(e)}"
        )


@app.delete("/delete_item/{item_id}")
async def del_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.execute(
        select(Item).where(Item.id == item_id).options(selectinload(Item.category))
    )
    item = item.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        await db.delete(item)
        await db.commit()
        return {
            "message": "Category deleted successfully",
            "deleted_category": {"id": item.id, "name": item.name},
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


@app.put("/update_category_image/{category_id}")
async def update_category_image(
    category_id: int, image: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """
    Обновляет изображение существующей категории
    """
    try:
        # Проверяем тип файла
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")

        # Находим категорию
        category = await db.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.items))
        )
        category = category.scalar_one_or_none()

        if not category:
            raise HTTPException(
                status_code=404, detail=f"Category with ID {category_id} not found"
            )

        # Сохраняем новый файл
        image_path = await save_upload_file(image)

        # Обновляем путь к изображению
        category.image = image_path
        await db.commit()
        await db.refresh(category)

        return {
            "message": "Category image updated successfully",
            "category": {
                "id": category.id,
                "name": category.name,
                "image_path": image_path,
            },
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error updating category image: {str(e)}"
        )


@app.delete("/delete_category/{category_id}")
async def del_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await db.execute(
        select(Category)
        .where(Category.id == category_id)
        .options(selectinload(Category.items))
    )
    category = category.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=404, detail=f"Category with ID {category_id} not found"
        )

    if category.items:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete category with associated items. Delete items first.",
        )

    try:
        await db.delete(category)
        await db.commit()
        return {
            "message": "Category deleted successfully",
            "deleted_category": {"id": category.id, "name": category.name},
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error deleting category: {str(e)}"
        )


@app.get("/categories/")
async def read_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).options(selectinload(Category.items)))
    categories = result.scalars().all()

    return {
        "categories": [
            {
                "id": category.id,
                "name": category.name,
                "image": category.image,
                "items": [
                    {"id": item.id, "name": item.name, "price": item.price}
                    for item in category.items
                ],
            }
            for category in categories
        ]
    }


@app.get("/users/")
async def read_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBUser))
    users = result.scalars().all()
    return {"users": [{"id": user.id} for user in users]}


# ========================= Analytics helpers & endpoints =========================


def _period_bounds(
    period: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None
) -> tuple[datetime, datetime]:
    """Возвращает (start_dt, end_dt) в UTC по заданному периоду или явным датам.

    period: today | yesterday | week | month
    start, end: строки вида YYYY-MM-DD (включительно)
    """
    now = datetime.utcnow()

    # Нормализуем на начало суток
    def day_start(dt: datetime) -> datetime:
        return datetime(dt.year, dt.month, dt.day)

    if start and end:
        try:
            start_parts = [int(x) for x in start.split("-")]
            end_parts = [int(x) for x in end.split("-")]
            start_dt = datetime(start_parts[0], start_parts[1], start_parts[2])
            # конец дня включительно → +1 день не включая границу
            end_dt = datetime(end_parts[0], end_parts[1], end_parts[2]) + timedelta(
                days=1
            )
            return start_dt, end_dt
        except Exception:
            # Если формат неверный, по умолчанию сегодня
            s = day_start(now)
            return s, s + timedelta(days=1)

    p = (period or "today").lower()
    if p == "today":
        s = day_start(now)
        e = s + timedelta(days=1)
    elif p == "yesterday":
        e = day_start(now)
        s = e - timedelta(days=1)
    elif p == "week":
        e = day_start(now) + timedelta(days=1)
        s = e - timedelta(days=7)
    elif p == "month":
        s = datetime(now.year, now.month, 1)
        # следующий месяц
        if now.month == 12:
            e = datetime(now.year + 1, 1, 1)
        else:
            e = datetime(now.year, now.month + 1, 1)
    else:
        s = day_start(now)
        e = s + timedelta(days=1)
    return s, e


@app.get("/analytics/turnover")
async def analytics_turnover(
    period: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает оборот за период. По умолчанию: сегодня.
    Параметры:
      - period: today|yesterday|week|month
      - start, end: YYYY-MM-DD (если указаны, period игнорируется)
    Считаем только заказы со статусом delivered|completed.
    """
    start_dt, end_dt = _period_bounds(period, start, end)

    q = (
        select(func.coalesce(func.sum(Order.total_price), 0.0), func.count(Order.id))
        .where(Order.created_at >= start_dt)
        .where(Order.created_at < end_dt)
        .where(Order.status.in_(["delivered", "completed"]))
    )
    res = await db.execute(q)
    total, orders_count = res.first()
    return {
        "period": {"start": start_dt, "end": end_dt},
        "turnover": float(total or 0),
        "orders_count": int(orders_count or 0),
        "currency": "RUB",
    }


@app.get("/analytics/sales", response_model=SalesResponse)
async def analytics_sales(
    period: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Список продаж (заказы и позиции) за период. По умолчанию: сегодня.
    Считаем только заказы со статусом delivered|completed.
    """
    start_dt, end_dt = _period_bounds(period, start, end)

    orders_stmt = (
        select(Order)
        .where(Order.created_at >= start_dt)
        .where(Order.created_at < end_dt)
        .where(Order.status.in_(["delivered", "completed"]))
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(orders_stmt)
    orders = result.scalars().all()

    sales_payload: List[Sale] = []
    cumulative_total = 0.0
    for o in orders:
        items_stmt = select(OrderItem).where(OrderItem.order_id == o.id)
        items_res = await db.execute(items_stmt)
        order_items = items_res.scalars().all()
        items_payload: List[SalesItem] = []
        for it in order_items:
            items_payload.append(
                SalesItem(
                    name=it.name,
                    quantity=it.quantity,
                    selected_taste=it.selected_taste,
                    price_per_item=float(it.price_per_item),
                    total_price=float(it.total_price),
                )
            )
        cumulative_total += float(o.total_price or 0)
        sales_payload.append(
            Sale(
                id=o.id,
                created_at=o.created_at,
                user_id=o.user_id,
                username=o.username,
                status=o.status,
                total_price=float(o.total_price or 0),
                items=items_payload,
            )
        )

    return SalesResponse(
        period={"start": start_dt, "end": end_dt},
        turnover=float(cumulative_total),
        orders_count=len(sales_payload),
        sales=sales_payload,
    )


@app.get("/analytics/canceled_orders", response_model=SalesResponse)
async def analytics_canceled_orders(
    period: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Эндпоинт для получения отмененных заказов за период"""
    start_dt, end_dt = _period_bounds(period, start, end)

    orders_stmt = (
        select(Order)
        .where(Order.created_at >= start_dt)
        .where(Order.created_at < end_dt)
        .where(Order.status == "canceled")
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(orders_stmt)
    orders = result.scalars().all()

    sales_payload: List[Sale] = []
    cumulative_total = 0.0
    for o in orders:
        items_stmt = select(OrderItem).where(OrderItem.order_id == o.id)
        items_res = await db.execute(items_stmt)
        order_items = items_res.scalars().all()
        items_payload: List[SalesItem] = []
        for it in order_items:
            items_payload.append(
                SalesItem(
                    name=it.name,
                    quantity=it.quantity,
                    selected_taste=it.selected_taste,
                    price_per_item=float(it.price_per_item),
                    total_price=float(it.total_price),
                )
            )
        cumulative_total += float(o.total_price or 0)
        sales_payload.append(
            Sale(
                id=o.id,
                created_at=o.created_at,
                user_id=o.user_id,
                username=o.username,
                status=o.status,
                total_price=float(o.total_price or 0),
                items=items_payload,
            )
        )

    return SalesResponse(
        period={"start": start_dt, "end": end_dt},
        turnover=float(cumulative_total),
        orders_count=len(sales_payload),
        sales=sales_payload,
    )


@app.get("/analytics/completed_orders", response_model=SalesResponse)
async def analytics_completed_orders(
    period: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Эндпоинт для получения завершенных заказов за период"""
    start_dt, end_dt = _period_bounds(period, start, end)

    orders_stmt = (
        select(Order)
        .where(Order.created_at >= start_dt)
        .where(Order.created_at < end_dt)
        .where(Order.status == "completed")
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(orders_stmt)
    orders = result.scalars().all()

    sales_payload: List[Sale] = []
    cumulative_total = 0.0
    for o in orders:
        items_stmt = select(OrderItem).where(OrderItem.order_id == o.id)
        items_res = await db.execute(items_stmt)
        order_items = items_res.scalars().all()
        items_payload: List[SalesItem] = []
        for it in order_items:
            items_payload.append(
                SalesItem(
                    name=it.name,
                    quantity=it.quantity,
                    selected_taste=it.selected_taste,
                    price_per_item=float(it.price_per_item),
                    total_price=float(it.total_price),
                )
            )
        cumulative_total += float(o.total_price or 0)
        sales_payload.append(
            Sale(
                id=o.id,
                created_at=o.created_at,
                user_id=o.user_id,
                username=o.username,
                status=o.status,
                total_price=float(o.total_price or 0),
                items=items_payload,
            )
        )

    return SalesResponse(
        period={"start": start_dt, "end": end_dt},
        turnover=float(cumulative_total),
        orders_count=len(sales_payload),
        sales=sales_payload,
    )


async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=3000, log_level="info")
    server = uvicorn.Server(config)

    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
