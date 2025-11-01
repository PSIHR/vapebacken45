import asyncio
import logging
import os
from asyncio.log import logger
from datetime import datetime
from typing import List

import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import joinedload, selectinload

from database.db import AsyncSessionLocal
from database.models import (
    Category,
    Courier,
    DBUser,
    Item,
    Order,
    OrderItem,
    Promocode,
    Taste,
    item_taste_association,
)

if not load_dotenv("./config/.env.local"):
    raise Exception("Failed to load .env file")

# Настройка логирования
logging.basicConfig(level=os.getenv("LOG_LEVEL"))
logger = logging.getLogger(__name__)

# Конфигурация
IMAGES_DIR = "uploads"

ADMINS = list(map(int, os.getenv("ADMINS").split(",")))
COURIERS = list(map(int, os.getenv("COURIERS").split(",")))

os.makedirs(IMAGES_DIR, exist_ok=True)

bot = Bot(token=str(os.getenv("TOKEN")))
dp = Dispatcher()


class ItemStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_category = State()
    waiting_for_image = State()
    waiting_for_tastes = State()
    waiting_for_strength = State()
    waiting_for_puffs = State()
    waiting_for_vg_pg = State()
    waiting_for_tank_volume = State()


class AdminStates(StatesGroup):
    waiting_admin_id = State()
    waiting_courier_id = State()


class CategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_image = State()


class CourierStates(StatesGroup):
    waiting_for_problem_description = State()
    waiting_for_user_id = State()
    waiting_for_username = State()
    waiting_for_phone = State()
    waiting_for_car_model = State()


class DeleteStates(StatesGroup):
    waiting_for_item_delete_confirm = State()
    waiting_for_category_delete_confirm = State()


class PromocodeStates(StatesGroup):
    waiting_for_promocode_name = State()
    waiting_for_promocode_percentage = State()
    waiting_for_promocode_delete_confirm = State()


class BanUserStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_ban_reason = State()


class UnBanUserStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_unban_reason = State()


class TasteStates(StatesGroup):
    waiting_for_taste_name = State()
    waiting_for_taste_image = State()
    waiting_for_item_selection = State()
    waiting_for_taste_selection = State()
    waiting_for_taste_search = State()


class ItemNameEditStates(StatesGroup):
    waiting_for_item_name = State()


class ItemCharacteristicsEditStates(StatesGroup):
    waiting_for_item_characteristics = State()


class ItemImageEditStates(StatesGroup):
    waiting_for_item_image = State()


class ItemPriceEditStates(StatesGroup):
    waiting_for_item_price = State()


class AnalyticsStates(StatesGroup):
    waiting_for_period_input = State()


class LoyaltyManagementStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_loyalty_level = State()
    waiting_for_stamps = State()
    waiting_for_total_items = State()


def get_courier_keyboard(order_id: int, status: str):
    builder = InlineKeyboardBuilder()

    if status == "waiting_for_courier":
        builder.row(
            InlineKeyboardButton(
                text="🚀 Взять заказ", callback_data=f"start_delivery_{order_id}"
            ),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{order_id}"),
        )
    elif status == "in_delivery":
        builder.row(
            InlineKeyboardButton(
                text="✅ Доставлено", callback_data=f"complete_{order_id}"
            ),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{order_id}"),
        )
    elif status == "delivered":
        builder.row(
            InlineKeyboardButton(
                text="🏁 Завершить", callback_data=f"finish_{order_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отменить доставку", callback_data=f"cancel_{order_id}"
            ),
        )
    elif status == "completed" or status == "finished":
        # Для завершенных и отмененных заказов не показываем кнопки
        pass

    return builder.as_markup()


async def delete_bot_messages(chat_id: int, message_ids: list):
    """Удаляет сообщения бота по их ID"""
    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения {message_id}: {e}")


def format_order_info(order: Order, orders_count: int, username: str = None) -> str:
    """Форматирование информации о заказе"""

    def escape_markdown(text: str) -> str:
        escape_chars = "_*[]()~`>#+-=|{}.!"
        return "".join(
            f"\\{char}" if char in escape_chars else char for char in str(text)
        )

    # Формирование списка товаров
    items_text = "\n".join(
        f"• {escape_markdown(item.item.name)} x{escape_markdown(str(item.quantity))}, "
        f"Вкус: {escape_markdown(item.selected_taste if item.selected_taste else 'не указан')} - "
        f"{escape_markdown(str(item.price_per_item))}₽"
        for item in order.items
    )

    # Определение статуса клиента
    if orders_count <= 1:
        client_status = "🆕 Новый клиент"
    elif 2 <= orders_count <= 5:
        client_status = f"🟢 Постоянный ({orders_count} заказов)"
    else:
        client_status = f"⭐ VIP клиент ({orders_count} заказов)"

    status_emojis = {
        "waiting_for_courier": "⏳ Ожидает курьера",
        "in_delivery": "🚗 В процессе доставки",
        "delivered": "✅ Доставлен",
        "completed": "🏁 Завершен",
        "canceled": "❌ Отменен",
    }

    # Используем переданный username или значение из order, если username не передан
    display_username = (
        username if username is not None else getattr(order, "username", "не указан")
    )

    # Форматируем информацию о доставке
    if order.delivery == "По метро":
        delivery_info = (
            f"🚇 *Способ доставки:* {escape_markdown(order.delivery)}\n"
            f"🚇 *Линия метро:* {escape_markdown(order.metro_line or 'не указана')}\n"
            f"📍 *Станция метро:* {escape_markdown(order.metro_station or 'не указана')}\n\n"
        )
    else:
        delivery_info = (
            f"🏠 *Адрес:* {escape_markdown(order.address)}\n"
            f"🚚 *Способ доставки:* {escape_markdown(order.delivery)}\n\n"
        )
    
    return (
        f"📋 *ИНФОРМАЦИЯ О ЗАКАЗЕ*\n\n"
        f"📦 *Состав заказа:*\n"
        f"```\n{items_text}\n```\n\n"
        f"💰 *СУММА:* {escape_markdown(str(order.total_price))}₽\n"
        f"👤 *Клиент:* @{escape_markdown(display_username)}\n"
        f"🔹 *Статус клиента:* {escape_markdown(client_status)}\n"
        f"📊 *Статус:* {escape_markdown(status_emojis.get(order.status, order.status))}\n\n"
        f"{delivery_info}"
        f"📅 *Дата:* {escape_markdown(order.created_at.strftime('%d.%m.%Y %H:%M'))}\n"
        f"🆔 *Номер:* {escape_markdown(str(order.id))}\n"
    )


async def notify_user(order_id: int, message: str):
    """Отправляет уведомление пользователю о статусе заказа"""
    async with AsyncSessionLocal() as db:
        # Загружаем заказ с информацией о курьере
        order = await db.execute(
            select(Order).where(Order.id == order_id).options(joinedload(Order.courier))
        )
        order = order.scalars().first()

        if order and order.user_id:
            try:
                await bot.send_message(chat_id=order.user_id, text=message)
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке уведомления пользователю {order.user_id}: {e}"
                )


async def save_upload_file(upload_file: UploadFile) -> str:
    """Сохраняет загруженный файл в папку uploads и возвращает относительный путь к файлу"""
    try:
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{upload_file.filename}"
        file_path = os.path.join(IMAGES_DIR, filename)

        # Сохраняем файл
        with open(file_path, "wb") as out_file:
            content = await upload_file.read()
            out_file.write(content)

        # Возвращаем относительный путь для веб-доступа
        return f"/uploads/{filename}"
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла: {e}")
        raise HTTPException(status_code=500, detail="Не удалось сохранить файл")


@dp.message(F.text == "⛔ Забанить пользователя")
async def ban_user_start(message: Message, state: FSMContext):
    """Начало процесса бана пользователя"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    await state.set_state(BanUserStates.waiting_for_username)
    await message.answer("Введите юзернейм пользователя (без @):")


@dp.message(BanUserStates.waiting_for_username)
async def process_username_for_ban(message: Message, state: FSMContext):
    """Обработка юзернейма для бана"""
    username = message.text.strip().lower()

    async with AsyncSessionLocal() as session:
        # Ищем пользователя в базе
        user = await session.scalar(
            select(DBUser).where(func.lower(DBUser.username) == username)
        )

        if not user:
            await message.answer(f"❌ Пользователь @{username} не найден в базе")
            await state.clear()
            return

        if user.is_banned:
            await message.answer(f"ℹ️ Пользователь @{username} уже в черном списке")
            await state.clear()
            return

        await state.update_data(user_id=user.id, username=username)
        await state.set_state(BanUserStates.waiting_for_ban_reason)
        await message.answer(f"Введите причину бана для @{username}:")


@dp.message(BanUserStates.waiting_for_ban_reason)
async def process_ban_user(message: Message, state: FSMContext):
    """Завершение процесса бана пользователя"""
    reason = message.text.strip()
    data = await state.get_data()
    user_id = data["user_id"]
    username = data["username"]

    async with AsyncSessionLocal() as session:
        # Обновляем статус пользователя
        user = await session.get(DBUser, user_id)
        user.is_banned = True
        await session.commit()

        # Отправляем уведомление пользователю (если возможно)
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"⛔ Вы были добавлены в черный список!\nПричина: {reason}",
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя @{username}: {e}")

        await message.answer(
            f"✅ Пользователь @{username} добавлен в черный список\nПричина: {reason}"
        )

    await state.clear()


@dp.message(F.text == "✅ Разбанить пользователя")
async def unban_user_start(message: Message, state: FSMContext):
    """Начало процесса разбана пользователя"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    await state.set_state(UnBanUserStates.waiting_for_username)
    await message.answer("Введите юзернейм пользователя (без @):")


@dp.message(UnBanUserStates.waiting_for_username)
async def process_username_for_unban(message: Message, state: FSMContext):
    """Обработка юзернейма для разбана"""
    username = message.text.strip().lower()

    async with AsyncSessionLocal() as session:
        # Ищем пользователя в базе
        user = await session.scalar(
            select(DBUser).where(func.lower(DBUser.username) == username)
        )

        if not user:
            await message.answer(f"❌ Пользователь @{username} не найден в базе")
            await state.clear()
            return

        if not user.is_banned:
            await message.answer(f"ℹ️ Пользователь @{username} не в черном списке")
            await state.clear()
            return

        await state.update_data(user_id=user.id, username=username)
        await state.set_state(UnBanUserStates.waiting_for_unban_reason)
        await message.answer(f"Введите причину разбана для @{username}:")


@dp.message(UnBanUserStates.waiting_for_unban_reason)
async def process_unban_user(message: Message, state: FSMContext):
    """Завершение процесса разбана пользователя"""
    reason = message.text.strip()
    data = await state.get_data()
    user_id = data["user_id"]
    username = data["username"]

    async with AsyncSessionLocal() as session:
        # Обновляем статус пользователя
        user = await session.get(DBUser, user_id)
        user.is_banned = False
        await session.commit()

        # Отправляем уведомление пользователю (если возможно)
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ Вы были исключены из черного списка!\nПричина: {reason}",
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя @{username}: {e}")

        await message.answer(
            f"✅ Пользователь @{username} исключен из черного списка\nПричина: {reason}"
        )

    await state.clear()


async def get_banned_users(session):
    stmt = select(DBUser).where(DBUser.is_banned == True)
    result = await session.execute(stmt)
    return result.scalars().all()


@dp.message(F.text == "📋 Заблокированные пользователи")
async def list_banned_users(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    async with AsyncSessionLocal() as session:
        banned_users = await get_banned_users(session)

    if banned_users:
        user_lines = [f"{user.id}: {user.username}" for user in banned_users]
        message_text = "📋 Список заблокированных пользователей:\n" + "\n".join(
            user_lines
        )
    else:
        message_text = "❌ Нет заблокированных пользователей."

    await message.answer(message_text)


@dp.message(F.text == "📦 Новые заказы")
async def show_new_orders(message: types.Message):
    if not await is_courier_or_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде")
        return

    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(Order)
                .where(Order.status == "waiting_for_courier")
                .order_by(Order.created_at.asc())
                .options(
                    joinedload(Order.user),
                    selectinload(Order.items).joinedload(OrderItem.item),
                )
            )

            result = await db.execute(stmt)
            orders = result.unique().scalars().all()

            if not orders:
                await message.answer(
                    "📭 На данный момент нет новых заказов для доставки"
                )
                return

            for order in orders:
                try:
                    count_stmt = select(func.count(Order.id)).where(
                        Order.user_id == order.user_id
                    )
                    orders_count = (await db.execute(count_stmt)).scalar() or 0
                    order_info = format_order_info(order, orders_count)

                    # Отправляем сообщение и сохраняем его ID
                    sent_message = await message.answer(
                        order_info,
                        parse_mode="MarkdownV2",
                        reply_markup=get_courier_keyboard(order.id, order.status),
                    )

                    # Сохраняем ID сообщения бота в заказе
                    if not order.bot_message_ids:
                        order.bot_message_ids = []
                    # Добавляем новый ID только если его еще нет в списке
                    if sent_message.message_id not in order.bot_message_ids:
                        order.bot_message_ids.append(sent_message.message_id)
                        await db.commit()

                except Exception as order_error:
                    logger.error(
                        f"Ошибка при обработке заказа {order.id}: {str(order_error)}",
                        exc_info=True,
                    )
                    continue

    except Exception as e:
        logger.error(
            f"Критическая ошибка при получении заказов: {str(e)}", exc_info=True
        )
        await message.answer(
            "⚠️ Произошла критическая ошибка при загрузке заказов. Попробуйте позже."
        )


@dp.message(F.text == "🚗 Активные заказы")
async def show_active_orders(message: types.Message):
    if not await is_courier_or_admin(message.from_user.id):
        return
    courier_id = message.from_user.id

    async with AsyncSessionLocal() as db:
        try:
            # Получаем активные заказы курьера
            orders = await db.execute(
                select(Order)
                .where(
                    (Order.courier_id == courier_id)
                    & (
                        (Order.status == "in_delivery")
                        | (Order.status == "delivered")
                        | (Order.status == "waiting_for_courier")
                    )
                )
                .order_by(Order.status, Order.created_at.desc())
                .options(selectinload(Order.items))
            )
            orders = orders.scalars().all()

            if not orders:
                await message.answer("📭 У вас сейчас нет активных заказов")
                return

            for order in orders:
                # Получаем дополнительные данные о клиенте
                username = await db.scalar(
                    select(DBUser.username).where(DBUser.id == order.user_id)
                )

                orders_count = (
                    await db.scalar(
                        select(func.count(Order.id)).where(
                            Order.user_id == order.user_id
                        )
                    )
                    if order.user_id
                    else 0
                )

                # Форматируем информацию о заказе
                order_info = format_order_info(order, orders_count, username)

                # Определяем нужно ли показывать кнопки управления
                if (
                    order.status == "waiting_for_courier"
                    and order.courier_id != courier_id
                ):
                    await message.answer(order_info)
                else:
                    await message.answer(
                        order_info,
                        parse_mode="MarkdownV2",
                        reply_markup=get_courier_keyboard(order.id, order.status),
                    )

        except Exception as e:
            logger.error(f"Ошибка при получении активных заказов: {e}")
            await message.answer("⚠️ Произошла ошибка при загрузке активных заказов")


@dp.message(F.text == "✅ Завершенные заказы")
async def show_completed_orders(message: types.Message):
    if not await is_courier_or_admin(message.from_user.id):
        return

    # Показываем выбор между просмотром заказов и аналитикой
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 Показать заказы", callback_data="show_completed_orders"
        ),
        InlineKeyboardButton(
            text="📊 Аналитика", callback_data="analytics_completed_orders"
        ),
    )

    await message.answer(
        "✅ Завершенные заказы\n\nВыберите действие:", reply_markup=builder.as_markup()
    )


# Обработчики для показа заказов
@dp.callback_query(F.data == "show_completed_orders")
async def show_completed_orders_list(callback: CallbackQuery):
    if not await is_courier_or_admin(callback.from_user.id):
        await callback.answer()
        return

    user_id = callback.from_user.id
    is_admin = user_id in ADMINS

    try:
        async with AsyncSessionLocal() as db:
            if is_admin:
                # Для админов показываем все завершенные заказы
                stmt = (
                    select(Order)
                    .where(Order.status == "completed")
                    .order_by(Order.created_at.desc())
                    .limit(100)  # Увеличиваем лимит для отображения всех заказов
                    .options(
                        joinedload(Order.user),
                        joinedload(Order.courier),
                        selectinload(Order.items).joinedload(OrderItem.item),
                    )
                )
            else:
                # Для курьеров показываем только их завершенные заказы
                courier = await db.execute(
                    select(Courier).where(Courier.user_id == user_id)
                )
                courier = courier.scalars().first()

                if not courier:
                    await callback.message.answer(
                        "❌ Вы не зарегистрированы как курьер"
                    )
                    await callback.answer()
                    return

                stmt = (
                    select(Order)
                    .where(
                        (Order.status == "completed") & (Order.courier_id == courier.id)
                    )
                    .order_by(Order.created_at.desc())
                    .limit(50)  # Увеличиваем лимит для курьеров
                    .options(
                        joinedload(Order.user),
                        joinedload(Order.courier),
                        selectinload(Order.items).joinedload(OrderItem.item),
                    )
                )

            result = await db.execute(stmt)
            orders = result.unique().scalars().all()

            if not orders:
                if is_admin:
                    await callback.message.answer("📭 Нет завершенных заказов")
                else:
                    await callback.message.answer(
                        "📭 У вас пока нет завершенных заказов"
                    )
                await callback.answer()
                return

            for order in orders:
                try:
                    # Получаем количество заказов пользователя
                    count_stmt = select(func.count(Order.id)).where(
                        Order.user_id == order.user_id
                    )
                    orders_count = (await db.execute(count_stmt)).scalar() or 0

                    # Получаем username пользователя
                    username = order.user.username if order.user else None

                    # Форматируем информацию о заказе
                    order_info = format_order_info(order, orders_count, username)

                    await callback.message.answer(
                        order_info,
                        parse_mode="MarkdownV2",
                        reply_markup=get_courier_keyboard(order.id, "completed"),
                    )
                except Exception as order_error:
                    logger.error(
                        f"Ошибка при обработке заказа {order.id}: {order_error}"
                    )
                    continue

    except Exception as e:
        logger.error(f"Ошибка при получении завершенных заказов: {e}", exc_info=True)
        await callback.message.answer(
            "⚠️ Произошла ошибка при загрузке завершенных заказов"
        )

    await callback.answer()


@dp.callback_query(F.data == "show_canceled_orders")
async def show_canceled_orders_list(callback: CallbackQuery):
    if not await is_courier_or_admin(callback.from_user.id):
        await callback.answer()
        return

    user_id = callback.from_user.id
    is_admin = user_id in ADMINS

    try:
        async with AsyncSessionLocal() as db:
            # Для админов показываем все отмененные заказы
            # Для курьеров - только те, что были назначены им
            if is_admin:
                stmt = (
                    select(Order)
                    .where(Order.status == "canceled")
                    .order_by(Order.created_at.desc())
                    .limit(100)  # Увеличиваем лимит для отображения всех заказов
                    .options(
                        joinedload(Order.user),
                        joinedload(Order.courier),
                        selectinload(Order.items).joinedload(OrderItem.item),
                    )
                )
            else:
                # Для курьеров показываем только их отмененные заказы
                courier = await db.execute(
                    select(Courier).where(Courier.user_id == user_id)
                )
                courier = courier.scalars().first()

                if not courier:
                    await callback.message.answer(
                        "❌ Вы не зарегистрированы как курьер"
                    )
                    await callback.answer()
                    return

                stmt = (
                    select(Order)
                    .where(
                        (Order.status == "canceled") & (Order.courier_id == courier.id)
                    )
                    .order_by(Order.created_at.desc())
                    .limit(50)  # Увеличиваем лимит для курьеров
                    .options(
                        joinedload(Order.user),
                        joinedload(Order.courier),
                        selectinload(Order.items).joinedload(OrderItem.item),
                    )
                )

            result = await db.execute(stmt)
            orders = result.unique().scalars().all()

            if not orders:
                if is_admin:
                    await callback.message.answer("📭 Нет отмененных заказов")
                else:
                    await callback.message.answer("📭 У вас нет отмененных заказов")
                await callback.answer()
                return

            # Функция для экранирования markdown
            def escape_markdown(text: str) -> str:
                escape_chars = "_*[]()~`>#+-=|{}.!"
                return "".join(
                    f"\\{char}" if char in escape_chars else char for char in str(text)
                )

            # Группируем заказы по дате для лучшего отображения
            from collections import defaultdict

            orders_by_date = defaultdict(list)

            for order in orders:
                date_str = order.created_at.strftime("%d.%m.%Y")
                orders_by_date[date_str].append(order)

            # Отправляем заказы по датам
            for date_str, date_orders in orders_by_date.items():
                await callback.message.answer(f"📅 **{date_str}**")

                for order in date_orders:
                    try:
                        # Получаем количество заказов пользователя
                        count_stmt = select(func.count(Order.id)).where(
                            Order.user_id == order.user_id
                        )
                        orders_count = (await db.execute(count_stmt)).scalar() or 0

                        # Получаем username пользователя
                        username = order.user.username if order.user else None

                        # Получаем информацию о курьере
                        courier_info = ""
                        if order.courier:
                            courier_info = f"\n🚴 *Курьер:* @{escape_markdown(order.courier.username)}"

                        # Формирование списка товаров
                        items_text = "\n".join(
                            f"• {escape_markdown(item.item.name)} x{escape_markdown(str(item.quantity))}, "
                            f"Вкус: {escape_markdown(item.selected_taste if item.selected_taste else 'не указан')} - "
                            f"{escape_markdown(str(item.price_per_item))}₽"
                            for item in order.items
                        )

                        # Определение статуса клиента
                        if orders_count <= 1:
                            client_status = "🆕 Новый клиент"
                        elif 2 <= orders_count <= 5:
                            client_status = f"🟢 Постоянный ({orders_count} заказов)"
                        else:
                            client_status = f"⭐ VIP клиент ({orders_count} заказов)"

                        # Используем переданный username или значение из order
                        display_username = (
                            username
                            if username is not None
                            else getattr(order, "username", "не указан")
                        )

                        order_info = (
                            f"📋 *ОТМЕНЕННЫЙ ЗАКАЗ*\n\n"
                            f"📦 *Состав заказа:*\n"
                            f"```\n{items_text}\n```\n\n"
                            f"💰 *СУММА:* {escape_markdown(str(order.total_price))}₽\n"
                            f"👤 *Клиент:* @{escape_markdown(display_username)}\n"
                            f"🔹 *Статус клиента:* {escape_markdown(client_status)}\n\n"
                            f"🏠 *Адрес:* {escape_markdown(order.address)}\n"
                            f"🚚 *Способ доставки:* {escape_markdown(order.delivery)}\n"
                            f"{courier_info}\n\n"
                            f"📅 *Дата:* {escape_markdown(order.created_at.strftime('%d.%m.%Y %H:%M'))}\n"
                            f"🆔 *Номер:* {escape_markdown(str(order.id))}\n"
                            f"❌ *Статус:* Отменен"
                        )

                        await callback.message.answer(
                            order_info, parse_mode="MarkdownV2"
                        )

                    except Exception as order_error:
                        logger.error(
                            f"Ошибка при обработке отмененного заказа {order.id}: {order_error}"
                        )
                        continue

    except Exception as e:
        logger.error(f"Ошибка при получении отмененных заказов: {e}", exc_info=True)
        await callback.message.answer(
            "⚠️ Произошла ошибка при загрузке отмененных заказов"
        )

    await callback.answer()


# Обработчики для аналитики
@dp.callback_query(F.data == "analytics_completed_orders")
async def analytics_completed_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer()
        return
    await callback.message.answer(
        "Выберите период для отчета по завершенным заказам:",
        reply_markup=_period_buttons(),
    )
    await callback.answer()


@dp.callback_query(F.data == "analytics_canceled_orders")
async def analytics_canceled_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer()
        return
    await callback.message.answer(
        "Выберите период для отчета по отмененным заказам:",
        reply_markup=_period_buttons(),
    )
    await callback.answer()


@dp.message(F.text == "❌ Отмененные заказы")
async def show_canceled_orders(message: types.Message):
    if not await is_courier_or_admin(message.from_user.id):
        return

    # Показываем выбор между просмотром заказов и аналитикой
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 Показать заказы", callback_data="show_canceled_orders"
        ),
        InlineKeyboardButton(
            text="📊 Аналитика", callback_data="analytics_canceled_orders"
        ),
    )

    await message.answer(
        "❌ Отмененные заказы\n\nВыберите действие:", reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("start_delivery_"))
async def start_delivery(callback: types.CallbackQuery):
    if not await is_courier_or_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    order_id = int(callback.data.split("_")[2])
    courier_id = callback.from_user.id

    async with AsyncSessionLocal() as db:
        # Получаем курьера
        courier = await db.execute(select(Courier).where(Courier.user_id == courier_id))
        courier = courier.scalars().first()

        if not courier:
            await callback.answer("Вы не зарегистрированы как курьер", show_alert=True)
            return

        # Получаем заказ с предзагруженными данными
        order = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                joinedload(Order.user),
                selectinload(Order.items).joinedload(OrderItem.item),
            )
        )
        order = order.scalars().first()

        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        if order.status != "waiting_for_courier":
            await callback.answer(
                "Этот заказ уже взят другим курьером", show_alert=True
            )
            return

        # Обновляем заказ
        order.status = "in_delivery"
        order.courier_id = courier.id
        await db.commit()

        # Получаем информацию о пользователе для уведомления
        username = order.user.username if order.user else None

        # Формируем информацию о заказе ДО закрытия сессии
        order_info = format_order_info(order, 0, username)

        # Уведомляем пользователя
        await notify_user(
            order_id,
            f"🚀 Ваш заказ #{order_id} взят в доставку!\n"
            f"Курьер: @{courier.username}\n"
            f"Телефон курьера: {courier.phone}\n"
            f"Машина: {courier.car_model}\n\n"
            f"Статус: В процессе доставки",
        )

    # После закрытия сессии работаем с уже полученными данными
    try:
        await callback.message.edit_text(
            order_info,
            parse_mode="MarkdownV2",
            reply_markup=get_courier_keyboard(order_id, "in_delivery"),
        )
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        await callback.message.answer(
            order_info,
            parse_mode="MarkdownV2",
            reply_markup=get_courier_keyboard(order_id, "in_delivery"),
        )

    await callback.answer("✅ Вы взяли заказ в доставку!", show_alert=True)


@dp.callback_query(F.data.startswith("complete_"))
async def complete_delivery(callback: types.CallbackQuery):
    if not await is_courier_or_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    order_id = int(callback.data.split("_")[1])
    courier_id = callback.from_user.id

    async with AsyncSessionLocal() as db:
        # Получаем курьера
        courier = await db.execute(select(Courier).where(Courier.user_id == courier_id))
        courier = courier.scalars().first()

        if not courier:
            await callback.answer("Вы не зарегистрированы как курьер", show_alert=True)
            return

        # Получаем заказ с предзагруженными данными
        order = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                joinedload(Order.user),
                selectinload(Order.items).joinedload(OrderItem.item),
            )
        )
        order = order.scalars().first()

        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        if order.courier_id != courier.id:
            await callback.answer("Это не ваш заказ", show_alert=True)
            return

        if order.status != "in_delivery":
            await callback.answer("Невозможно завершить этот заказ", show_alert=True)
            return

        # Обновляем статус заказа
        order.status = "delivered"
        await db.commit()

        # Получаем информацию о пользователе
        username = order.user.username if order.user else None

        # Формируем информацию о заказе ДО закрытия сессии
        order_info = format_order_info(order, 0, username)

        # Уведомляем пользователя
        await notify_user(
            order_id,
            f"✅ Ваш заказ #{order_id} доставлен!\n"
            f"Курьер: @{courier.username}\n"
            f"Телефон курьера: {courier.phone}\n"
            f"Машина: {courier.car_model}\n\n"
            f"Пожалуйста, проверьте его целостность.\n"
            f"Статус: Доставлен",
        )

    # После закрытия сессии работаем с уже полученными данными
    try:
        await callback.message.edit_text(
            order_info,
            parse_mode="MarkdownV2",
            reply_markup=get_courier_keyboard(order_id, "delivered"),
        )
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        await callback.message.answer(
            order_info,
            parse_mode="MarkdownV2",
            reply_markup=get_courier_keyboard(order_id, "delivered"),
        )

    await callback.answer("✅ Заказ доставлен!", show_alert=True)


@dp.callback_query(F.data.startswith("finish_"))
async def finish_order(callback: types.CallbackQuery):
    if not await is_courier_or_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    order_id = int(callback.data.split("_")[1])
    courier_id = callback.from_user.id

    async with AsyncSessionLocal() as db:
        # Получаем курьера
        courier = await db.execute(select(Courier).where(Courier.user_id == courier_id))
        courier = courier.scalars().first()

        if not courier:
            await callback.answer("Вы не зарегистрированы как курьер", show_alert=True)
            return

        # Получаем заказ
        order = await db.get(Order, order_id)
        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        if order.courier_id != courier.id:
            await callback.answer("Это не ваш заказ", show_alert=True)
            return

        if order.status != "delivered":
            await callback.answer("Невозможно завершить этот заказ", show_alert=True)
            return

        # Сохраняем список ID сообщений и получаем список всех курьеров для удаления сообщений
        message_ids_to_delete = (
            order.bot_message_ids.copy() if order.bot_message_ids else []
        )

        # Получаем всех курьеров и админов для удаления сообщений из их чатов
        all_couriers = await db.execute(select(Courier))
        courier_user_ids = [c.user_id for c in all_couriers.scalars().all()]
        all_user_ids = courier_user_ids + ADMINS  # Добавляем админов

        # Меняем статус заказа на завершенный и очищаем bot_message_ids
        order.status = "completed"
        order.bot_message_ids = []
        await db.commit()

        # Уведомляем пользователя
        await notify_user(
            order_id, f"🏁 Ваш заказ #{order_id} успешно завершен!\nСпасибо за покупку!"
        )

    # Удаляем сообщения из всех чатов курьеров и админов
    if message_ids_to_delete:
        for user_id in all_user_ids:
            try:
                await delete_bot_messages(user_id, message_ids_to_delete)
            except Exception as e:
                logger.error(
                    f"Ошибка при удалении сообщений у пользователя {user_id}: {e}"
                )

    # Удаляем текущее сообщение с кнопками
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения с кнопками: {e}")

    await callback.answer("✅ Заказ успешно завершен", show_alert=True)


async def is_courier(user_id: int) -> bool:
    """Проверяет, является ли пользователь курьером"""
    async with AsyncSessionLocal() as session:
        courier = await session.scalar(
            select(Courier).where(Courier.user_id == user_id)
        )
        return courier is not None


@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Проверка прав доступа
        user_id = callback.from_user.id
        if not await is_courier_or_admin(user_id):
            await callback.answer("Доступ запрещен", show_alert=True)
            return

        # Безопасное извлечение order_id
        parts = callback.data.split("_")
        if len(parts) < 2:
            await callback.answer("Неверный формат команды", show_alert=True)
            return

        try:
            order_id = int(parts[1])
        except ValueError:
            await callback.answer("Неверный ID заказа", show_alert=True)
            return

        async with AsyncSessionLocal() as db:
            # Получаем заказ с дополнительной информацией
            order = await db.execute(
                select(Order)
                .where(Order.id == order_id)
                .options(
                    joinedload(Order.courier),
                    joinedload(Order.user),
                    selectinload(Order.items).joinedload(OrderItem.item),
                )
            )
            order = order.scalars().first()

            if not order:
                await callback.answer("Заказ не найден", show_alert=True)
                return

            # Проверяем права на отмену
            is_admin = user_id in ADMINS
            is_assigned_courier = order.courier and order.courier.user_id == user_id

            # Разрешаем отмену если:
            # - это админ
            # - или это назначенный курьер и заказ не завершен/отменен
            # - или заказ ожидает курьера и пользователь - курьер
            can_cancel = (
                is_admin
                or (
                    is_assigned_courier
                    and order.status not in ["completed", "canceled"]
                )
                or (order.status == "waiting_for_courier" and await is_courier(user_id))
            )

            if not can_cancel:
                await callback.answer(
                    f"Вы не можете отменить этот заказ (статус: {order.status})",
                    show_alert=True,
                )
                return

            # Сохраняем данные для последующего удаления сообщений
            chat_id = callback.message.chat.id
            message_ids_to_delete = []

            # Добавляем текущее сообщение в список для удаления
            message_ids_to_delete.append(callback.message.message_id)

            # Добавляем все сообщения бота о заказе
            if order.bot_message_ids:
                message_ids_to_delete.extend(order.bot_message_ids)

            # Для админов - сразу отменяем без запроса причины
            if is_admin:
                # Получаем всех курьеров для удаления сообщений из их чатов
                all_couriers = await db.execute(select(Courier))
                courier_user_ids = [c.user_id for c in all_couriers.scalars().all()]
                all_user_ids = courier_user_ids + ADMINS  # Добавляем админов

                order.status = "canceled"
                order.bot_message_ids = []  # Очищаем список сообщений
                await db.commit()

                # Удаляем все связанные сообщения из всех чатов
                for user_id in all_user_ids:
                    try:
                        await delete_bot_messages(user_id, message_ids_to_delete)
                    except Exception as e:
                        logger.error(
                            f"Ошибка при удалении сообщений у пользователя {user_id}: {e}"
                        )

                # Уведомления
                notification_text = f"❌ Заказ #{order_id} отменен администратором"
                if order.user_id:
                    await notify_user(order_id, notification_text)
                if order.courier and order.courier.user_id != user_id:
                    await bot.send_message(
                        chat_id=order.courier.user_id, text=notification_text
                    )

                await callback.answer("Заказ отменен администратором", show_alert=True)
                return

            # Для курьеров - запрашиваем причину
            await state.update_data(
                order_id=order_id,
                chat_id=chat_id,
                message_ids_to_delete=message_ids_to_delete,
                is_admin=is_admin,
            )
            await state.set_state(CourierStates.waiting_for_problem_description)

            try:
                reason_msg = await callback.message.answer(
                    f"📝 Укажите причину отмены заказа #{order_id}:"
                )
                # Добавляем сообщение с запросом причины в список для удаления
                await state.update_data(reason_message_id=reason_msg.message_id)
                await callback.answer()
            except Exception as e:
                logger.error(f"Ошибка запроса причины: {e}")
                await state.clear()
                await callback.answer("Ошибка при обработке", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка в cancel_order: {str(e)}", exc_info=True)
        try:
            await callback.answer("Произошла ошибка", show_alert=True)
        except:
            pass


@dp.message(CourierStates.waiting_for_problem_description)
async def process_cancel_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data["order_id"]
    data["chat_id"]
    message_ids_to_delete = data.get("message_ids_to_delete", [])
    reason_message_id = data.get("reason_message_id")
    is_admin = data.get("is_admin", False)

    async with AsyncSessionLocal() as db:
        order = await db.get(Order, order_id)
        if order:
            try:
                # Добавляем текущее сообщение с причиной в список для удаления
                if message.message_id not in message_ids_to_delete:
                    message_ids_to_delete.append(message.message_id)

                if reason_message_id and reason_message_id not in message_ids_to_delete:
                    message_ids_to_delete.append(reason_message_id)

                # Получаем всех курьеров для удаления сообщений из их чатов
                all_couriers = await db.execute(select(Courier))
                courier_user_ids = [c.user_id for c in all_couriers.scalars().all()]
                all_user_ids = courier_user_ids + ADMINS  # Добавляем админов

                # Удаляем все связанные сообщения из всех чатов
                for user_id in all_user_ids:
                    try:
                        await delete_bot_messages(user_id, message_ids_to_delete)
                    except Exception as e:
                        logger.error(
                            f"Ошибка при удалении сообщений у пользователя {user_id}: {e}"
                        )

                # Обновляем статус заказа
                order.status = "canceled"
                order.bot_message_ids = []  # Очищаем список сообщений
                await db.commit()

                # Уведомляем пользователя
                await notify_user(
                    order_id,
                    f"❌ Ваш заказ #{order_id} отменен.\nПричина: {message.text}",
                )

                # Для админов отправляем дополнительное уведомление
                if is_admin:
                    await message.answer(
                        f"✅ Заказ #{order_id} отменен администратором",
                        reply_markup=ReplyKeyboardRemove(),
                    )
                else:
                    # Для курьеров отправляем подтверждение отмены
                    confirm_msg = await message.answer(
                        f"✅ Заказ #{order_id} отменен",
                        reply_markup=ReplyKeyboardRemove(),
                    )
                    # Удаляем подтверждение через 3 секунды
                    await asyncio.sleep(3)
                    try:
                        await confirm_msg.delete()
                    except Exception as e:
                        logger.error(f"Ошибка при удалении подтверждения: {e}")

            except Exception as e:
                logger.error(f"Ошибка при отмене заказа: {e}")
                await message.answer("❌ Произошла ошибка при отмене заказа")

    await state.clear()


async def save_photo(file_id: str) -> str:
    """Сохранение фото на диск и возврат относительного пути к файлу"""
    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_id}.jpg"
    save_path = os.path.join(IMAGES_DIR, file_name)

    # Скачиваем файл
    await bot.download_file(file_path, save_path)

    # Возвращаем относительный путь для веб-доступа
    return f"/uploads/{file_name}"


@dp.callback_query(F.data.startswith("cancel_delivered_"))
async def cancel_delivered_order(callback: CallbackQuery, state: FSMContext):
    """Обработка отмены доставленного заказа"""
    try:
        # Безопасное извлечение order_id
        parts = callback.data.split("_")
        if len(parts) < 3:
            await callback.answer("Неверный формат команды", show_alert=True)
            return

        order_id = int(parts[2])
        user_id = callback.from_user.id

        if not await is_courier_or_admin(user_id):
            await callback.answer("Доступ запрещен", show_alert=True)
            return

        async with AsyncSessionLocal() as db:
            # Получаем заказ с дополнительной информацией
            order = await db.execute(
                select(Order)
                .where(Order.id == order_id)
                .options(joinedload(Order.courier), joinedload(Order.user))
            )
            order = order.scalars().first()

            if not order:
                await callback.answer("Заказ не найден", show_alert=True)
                return

            if order.status != "delivered":
                await callback.answer(
                    "Этот заказ не в статусе 'доставлен'", show_alert=True
                )
                return

            # Проверяем права (только админ или назначенный курьер)
            is_admin = user_id in ADMINS
            is_assigned_courier = order.courier and order.courier.user_id == user_id

            if not (is_admin or is_assigned_courier):
                await callback.answer(
                    "Вы не можете отменить этот заказ", show_alert=True
                )
                return

            # Обновляем статус
            order.status = "canceled"
            await db.commit()

            # Уведомляем пользователя
            await notify_user(
                order_id, f"❌ Ваш заказ #{order_id} был отменен после доставки!"
            )

            # Удаляем сообщение с кнопками
            try:
                await callback.message.delete()
            except Exception as e:
                logger.error(f"Error deleting message: {e}")

            await callback.answer("✅ Заказ отменен", show_alert=True)

    except Exception as e:
        logger.error(f"Error in cancel_delivered: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    async with AsyncSessionLocal() as session:
        existing_user = await session.get(DBUser, user_id)

        if not existing_user:
            new_user = DBUser(id=user_id, username=username)
            session.add(new_user)
            await session.commit()
        else:
            if existing_user.username != username:
                existing_user.username = username
                await session.commit()

    # Получаем URL веб-приложения из переменной окружения
    webapp_url = f"https://{os.getenv('REPLIT_DEV_DOMAIN', 'localhost:5000')}"
    
    # Создаем inline клавиатуру с кнопкой для открытия Web App
    webapp_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]
    ])

    if user_id in ADMINS:  # Проверяем, что пользователь - админ
        builder = ReplyKeyboardBuilder()
        builder.row(
            types.KeyboardButton(text="➕ Создать товар"),
            types.KeyboardButton(text="📁 Создать категорию"),
            types.KeyboardButton(text="🎫 Создать промокод"),
        )
        builder.row(
            types.KeyboardButton(text="🛍️ Список товаров"),
            types.KeyboardButton(text="🗂️ Список категорий"),
            types.KeyboardButton(text="📜 Список промокодов"),
        )
        builder.row(
            types.KeyboardButton(text="❌ Удалить товар"),
            types.KeyboardButton(text="❌ Удалить категорию"),
            types.KeyboardButton(text="❌ Удалить промокод"),
        )
        builder.row(
            types.KeyboardButton(text="📦 Новые заказы"),
            types.KeyboardButton(text="🚗 Активные заказы"),
        )
        builder.row(
            types.KeyboardButton(text="✅ Завершенные заказы"),
            types.KeyboardButton(text="❌ Отмененные заказы"),
        )
        builder.row(types.KeyboardButton(text="🍓 Управление вкусами товара"))
        builder.row(types.KeyboardButton(text="📦 Редактировать товар"))
        builder.row(
            types.KeyboardButton(text="👑 Управление персоналом"),
        )
        # Кнопки аналитики
        builder.row(
            types.KeyboardButton(text="📈 Продажи"),
            types.KeyboardButton(text="💵 Оборот"),
        )
        builder.row(
            types.KeyboardButton(text="❌ Отмененные"),
            types.KeyboardButton(text="✅ Завершенные"),
        )
        builder.row(
            types.KeyboardButton(text="📋 Заблокированные пользователи"),
            types.KeyboardButton(text="⛔ Забанить пользователя"),
            types.KeyboardButton(text="✅ Разбанить пользователя"),
        )
        await message.answer(
            "👨‍💻 Панель администратора:",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
        # Отправляем кнопку для открытия Web App
        await message.answer(
            "🛍 Откройте магазин, чтобы посмотреть товары и сделать заказ:",
            reply_markup=webapp_keyboard
        )
    elif user_id in COURIERS:
        builder = ReplyKeyboardBuilder()
        builder.row(
            types.KeyboardButton(text="📦 Новые заказы"),
            types.KeyboardButton(text="🚗 Активные заказы"),
        )
        builder.row(
            types.KeyboardButton(text="✅ Завершенные заказы"),
            types.KeyboardButton(text="❌ Отмененные заказы"),
        )
        await message.answer(
            "🚴 Панель курьера:", reply_markup=builder.as_markup(resize_keyboard=True)
        )
        # Отправляем кнопку для открытия Web App
        await message.answer(
            "🛍 Откройте магазин, чтобы посмотреть товары:",
            reply_markup=webapp_keyboard
        )
    else:
        await message.answer(
            """<b>💨 VAPE PLUG</b> - ваш магазин вейп-продукции в Минске

        <b>🛒 Как сделать заказ:</b>
        1. Нажмите кнопку "Открыть магазин" ниже
        2. Выберите товары в каталоге
        3. Оформите заказ в корзине

        <b>🚚 Доставка:</b>
        • По Минску
        • По метро (Московская, Автозаводская, Зеленолужская линии)
        • Самовывоз

        <b>📍 Мы находимся:</b>
        • Минск, Беларусь

        <b>📞 По всем вопросам:</b>
        @vapepluggmanager""",
            parse_mode="HTML",
            reply_markup=webapp_keyboard,
        )


# Реализация админ-панели
@dp.message(F.text == "➕ Создать товар")
async def create_item_start(message: Message, state: FSMContext):
    """Начало создания товара"""
    await state.set_state(ItemStates.waiting_for_name)
    await message.answer("📝 Введите название товара:")


@dp.message(ItemStates.waiting_for_name)
async def process_item_name(message: Message, state: FSMContext):
    """Обработка названия товара"""
    await state.update_data(name=message.text)
    await state.set_state(ItemStates.waiting_for_description)
    await message.answer("📄 Введите описание товара:")


@dp.message(ItemStates.waiting_for_description)
async def process_item_description(message: Message, state: FSMContext):
    """Обработка описания товара"""
    await state.update_data(description=message.text)
    await state.set_state(ItemStates.waiting_for_price)
    await message.answer("💰 Введите цену товара (в рублях):")


@dp.message(ItemStates.waiting_for_price)
async def process_item_price(message: Message, state: FSMContext):
    """Обработка цены товара"""
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError
        await state.update_data(price=price)
        await state.set_state(ItemStates.waiting_for_category)

        async with AsyncSessionLocal() as session:
            categories = await session.execute(select(Category))
            categories = categories.scalars().all()

            if not categories:
                await message.answer(
                    "ℹ️ Нет доступных категорий. Сначала создайте категорию."
                )
                await state.clear()
                return

            builder = InlineKeyboardBuilder()
            for category in categories:
                builder.add(
                    InlineKeyboardButton(
                        text=category.name, callback_data=f"category_{category.id}"
                    )
                )
            builder.adjust(2)

            await message.answer(
                "🏷️ Выберите категорию:", reply_markup=builder.as_markup()
            )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректную цену (целое число больше 0)"
        )


@dp.callback_query(F.data.startswith("category_"), ItemStates.waiting_for_category)
async def process_item_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=category_id)
    await state.set_state(ItemStates.waiting_for_image)
    await callback.message.answer("🖼️ Отправьте изображение товара:")
    await callback.answer()


@dp.message(ItemStates.waiting_for_image, F.photo)
async def process_item_image(message: Message, state: FSMContext):
    """Обработка изображения товара"""
    try:
        photo = message.photo[-1]
        image_path = await save_photo(photo.file_id)
        await state.update_data(image_path=image_path)
        await state.set_state(ItemStates.waiting_for_tastes)
        await message.answer(
            "🍓 Введите вкусы товара через запятую (если это под, испаритель или товар без вкуса введи нет, 0 или без вкусов):"
        )
    except Exception as e:
        logger.error(f"Error saving photo: {e}")
        await message.answer(
            "❌ Ошибка при сохранении изображения. Попробуйте еще раз."
        )
        await state.set_state(ItemStates.waiting_for_image)


@dp.message(ItemStates.waiting_for_tastes)
async def process_item_tastes(message: Message, state: FSMContext):
    """Обработка вкусов"""
    # Получаем текст сообщения и очищаем от лишних пробелов
    tastes_text = message.text.strip() if message.text else ""

    # Если строка пустая или пользователь явно указал "нет" или "0"
    if not tastes_text or tastes_text.lower() in ("нет", "0", "без вкусов"):
        tastes = []
        await message.answer("ℹ️ Вкусы не будут добавлены к товару")
    else:
        # Разделяем вкусы по запятым и очищаем от пробелов
        tastes = [taste.strip() for taste in tastes_text.split(",") if taste.strip()]
    
    # Сохраняем вкусы в state
    await state.update_data(tastes=tastes)
    
    # Переходим к запросу крепкости
    await state.set_state(ItemStates.waiting_for_strength)
    await message.answer("💪 Введите крепкость (например: 20 мг, 50 мг) или 'нет' чтобы пропустить:")


@dp.message(ItemStates.waiting_for_strength)
async def process_item_strength(message: Message, state: FSMContext):
    """Обработка крепкости товара"""
    strength = message.text.strip() if message.text else ""
    
    # Если пользователь ввел "нет", сохраняем как None
    if strength.lower() in ("нет", "0", "-"):
        strength = None
    
    await state.update_data(strength=strength)
    await state.set_state(ItemStates.waiting_for_puffs)
    await message.answer("💨 Введите количество тяг (например: 800, 1500) или 'нет' чтобы пропустить:")


@dp.message(ItemStates.waiting_for_puffs)
async def process_item_puffs(message: Message, state: FSMContext):
    """Обработка количества тяг"""
    puffs = message.text.strip() if message.text else ""
    
    if puffs.lower() in ("нет", "0", "-"):
        puffs = None
    
    await state.update_data(puffs=puffs)
    await state.set_state(ItemStates.waiting_for_vg_pg)
    await message.answer("🧪 Введите VG/PG соотношение (например: 50/50, 70/30) или 'нет' чтобы пропустить:")


@dp.message(ItemStates.waiting_for_vg_pg)
async def process_item_vg_pg(message: Message, state: FSMContext):
    """Обработка VG/PG соотношения"""
    vg_pg = message.text.strip() if message.text else ""
    
    if vg_pg.lower() in ("нет", "0", "-"):
        vg_pg = None
    
    await state.update_data(vg_pg=vg_pg)
    await state.set_state(ItemStates.waiting_for_tank_volume)
    await message.answer("📦 Введите объем бака (например: 2 мл, 3.5 мл) или 'нет' чтобы пропустить:")


@dp.message(ItemStates.waiting_for_tank_volume)
async def process_item_tank_volume(message: Message, state: FSMContext):
    """Обработка объема бака и завершение создания товара"""
    tank_volume = message.text.strip() if message.text else ""
    
    if tank_volume.lower() in ("нет", "0", "-"):
        tank_volume = None
    
    await state.update_data(tank_volume=tank_volume)
    
    # Получаем все данные
    data = await state.get_data()
    tastes = data.get("tastes", [])

    try:
        async with AsyncSessionLocal() as session:
            # Создаем товар со всеми характеристиками
            new_item = Item(
                name=data["name"],
                description=data["description"],
                price=data["price"],
                category_id=data["category_id"],
                image=data["image_path"],
                strength=data.get("strength"),
                puffs=data.get("puffs"),
                vg_pg=data.get("vg_pg"),
                tank_volume=tank_volume,
            )
            session.add(new_item)
            await session.flush()

            # Обрабатываем вкусы только если они есть
            if tastes:
                # Получаем существующие вкусы
                existing_tastes = (
                    (await session.execute(select(Taste).where(Taste.name.in_(tastes))))
                    .scalars()
                    .all()
                )

                existing_names = {t.name for t in existing_tastes}
                new_tastes = []

                # Создаем новые вкусы
                for taste_name in tastes:
                    if taste_name not in existing_names:
                        new_taste = Taste(name=taste_name)
                        new_tastes.append(new_taste)
                        session.add(new_taste)

                await session.flush()

                # Связываем товар с вкусами
                all_tastes = existing_tastes + new_tastes
                for taste in all_tastes:
                    await session.execute(
                        insert(item_taste_association).values(
                            item_id=new_item.id, taste_id=taste.id
                        )
                    )
            else:
                logger.info(f"Товар {new_item.name} создан без вкусов")

            await session.commit()
            await message.answer("✅ Товар успешно создан!")

    except Exception as e:
        logger.error(f"Error creating item: {e}")
        await message.answer("❌ Произошла ошибка при создании товара")
    finally:
        await state.clear()


@dp.message(F.text == "👑 Управление персоналом")
async def manage_staff(message: Message):
    if message.from_user.id not in ADMINS:
        return

    keyboard = [
        [KeyboardButton(text="➕ Добавить админа")],
        [KeyboardButton(text="➕ Добавить курьера")],
        [KeyboardButton(text="📝 Редактировать курьера")],  # Новая кнопка
        [KeyboardButton(text="❌ Удалить админа")],
        [KeyboardButton(text="❌ Удалить курьера")],
        [KeyboardButton(text="📋 Список админов")],
        [KeyboardButton(text="📋 Список курьеров")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    await message.answer("Выберите действие:", reply_markup=reply_markup)


@dp.message(F.text == "📝 Редактировать курьера")
async def edit_courier_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    async with AsyncSessionLocal() as session:
        couriers = await session.execute(select(Courier))
        couriers = couriers.scalars().all()

        if not couriers:
            await message.answer("Нет зарегистрированных курьеров")
            return

        builder = InlineKeyboardBuilder()
        for courier in couriers:
            builder.add(
                InlineKeyboardButton(
                    text=f"{courier.username} (ID: {courier.user_id})",
                    callback_data=f"edit_courier_{courier.user_id}",
                )
            )
        builder.adjust(1)

        await message.answer(
            "Выберите курьера для редактирования:", reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data.startswith("edit_courier_"))
async def select_courier_to_edit(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[2])
    await state.update_data(user_id=user_id)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📱 Телефон", callback_data="edit_phone"),
        InlineKeyboardButton(text="🚗 Машина", callback_data="edit_car"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Username", callback_data="edit_username"),
        InlineKeyboardButton(text="✅ Активность", callback_data="toggle_active"),
    )

    await callback.message.edit_text(
        "Что вы хотите изменить?", reply_markup=builder.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "edit_phone")
async def edit_courier_phone(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CourierStates.waiting_for_phone)
    await callback.message.edit_text("Введите новый телефон курьера:")
    await callback.answer()


@dp.message(CourierStates.waiting_for_phone)
async def process_courier_phone(message: Message, state: FSMContext):
    try:
        phone = message.text.strip()
        if not phone:
            await message.answer(
                "Телефон не может быть пустым. Введите телефон курьера:"
            )
            return

        await state.update_data(phone=phone)
        await state.set_state(CourierStates.waiting_for_car_model)
        await message.answer("Введите модель машины курьера:")

    except Exception as e:
        logger.error(f"Ошибка при обработке телефона курьера: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
        await state.clear()


@dp.callback_query(F.data == "edit_car")
async def edit_courier_car(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CourierStates.waiting_for_car_model)
    await callback.message.edit_text("Введите новую модель машины курьера:")
    await callback.answer()


@dp.message(CourierStates.waiting_for_car_model)
async def process_courier_car_model(message: Message, state: FSMContext):
    try:
        data = await state.get_data()

        # Проверяем наличие всех необходимых данных
        required_fields = ["user_id", "username", "phone"]
        if not all(field in data for field in required_fields):
            await message.answer("Ошибка: недостаточно данных. Начните процесс заново.")
            await state.clear()
            return

        car_model = message.text.strip()
        if not car_model:
            await message.answer("Модель машины не может быть пустой. Введите снова:")
            return

        async with AsyncSessionLocal() as session:
            # Проверяем, не существует ли уже курьер с таким user_id
            existing = await session.scalar(
                select(Courier).where(Courier.user_id == data["user_id"])
            )

            if existing:
                await message.answer(
                    "⚠️ Этот пользователь уже зарегистрирован как курьер"
                )
                await state.clear()
                return

            # Создаем нового курьера
            new_courier = Courier(
                user_id=data["user_id"],
                username=data["username"],
                phone=data["phone"],
                car_model=car_model,
                is_active=True,
            )

            session.add(new_courier)
            await session.commit()

            # Добавляем ID в список COURIERS, если его там нет
            if new_courier.user_id not in COURIERS:
                COURIERS.append(new_courier.user_id)

            await message.answer(
                "✅ Курьер успешно создан!\n"
                f"ID: {new_courier.user_id}\n"
                f"Username: @{new_courier.username}\n"
                f"Телефон: {new_courier.phone}\n"
                f"Машина: {new_courier.car_model}"
            )

    except Exception as e:
        logger.error(f"Ошибка при создании курьера: {str(e)}")
        await message.answer(
            "❌ Произошла ошибка при создании курьера. Попробуйте снова."
        )
    finally:
        await state.clear()


@dp.callback_query(F.data == "toggle_active")
async def toggle_courier_active(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data["user_id"]

    async with AsyncSessionLocal() as session:
        courier = await session.scalar(
            select(Courier).where(Courier.user_id == user_id)
        )
        if courier:
            courier.is_active = not courier.is_active
            await session.commit()
            status = "активен" if courier.is_active else "неактивен"
            await callback.message.edit_text(
                f"Статус курьера {courier.username} изменен на {status}!"
            )
        else:
            await callback.message.edit_text("Курьер не найден")

    await callback.answer()


# Добавление админа
@dp.message(F.text == "➕ Добавить админа")
async def add_admin_start(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_admin_id)
    await message.answer("Отправьте ID нового админа:")


@dp.message(AdminStates.waiting_admin_id)
async def add_admin_process(message: Message, state: FSMContext):
    try:
        new_id = int(message.text)
        if new_id in ADMINS:
            await message.answer("Этот пользователь уже админ!")
        else:
            ADMINS.append(new_id)
            await message.answer(f"✅ Пользователь {new_id} добавлен в админы")
    except ValueError:
        await message.answer("ID должен быть числом!")
    await state.clear()


# ===================== АНАЛИТИКА (бот) =====================


def _period_buttons() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Сегодня", callback_data="an_period_today"),
        InlineKeyboardButton(text="Вчера", callback_data="an_period_yesterday"),
    )
    builder.row(
        InlineKeyboardButton(text="7 дней", callback_data="an_period_week"),
        InlineKeyboardButton(text="Месяц", callback_data="an_period_month"),
    )
    builder.row(
        InlineKeyboardButton(text="Выбрать период", callback_data="an_period_custom"),
    )
    return builder.as_markup()


@dp.message(F.text == "📈 Продажи")
async def analytics_sales_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer(
        "Выберите период для отчета по продажам:", reply_markup=_period_buttons()
    )


@dp.message(F.text == "💵 Оборот")
async def analytics_turnover_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer(
        "Выберите период для отчета по обороту:", reply_markup=_period_buttons()
    )


@dp.message(F.text == "❌ Отмененные")
async def analytics_cancelled_orders(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer(
        "Выберите период для отчета по отмененным заказам:",
        reply_markup=_period_buttons(),
    )


@dp.message(F.text == "✅ Завершенные")
async def analytics_end_orders(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer(
        "Выберите период для отчета по завершенным заказам:",
        reply_markup=_period_buttons(),
    )


async def _fetch_json(url: str, params: dict | None = None) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()


def _format_sales(
    response: dict,
    offset: int = 0,
    limit: int = 20,
    is_canceled: bool = False,
    is_completed: bool = False,
) -> tuple[str, int]:
    period = response.get("period", {})
    start = period.get("start", "")
    end = period.get("end", "")
    turnover = response.get("turnover", 0)
    orders_count = response.get("orders_count", 0)
    sales = response.get("sales", [])

    if is_canceled:
        title = "❌ Отчет по отмененным заказам"
    elif is_completed:
        title = "✅ Отчет по завершенным заказам"
    else:
        title = "📈 Отчет по продажам"

    lines = [
        title,
        f"Период: {start} — {end}",
        f"Заказов: {orders_count}",
        f"Оборот: {turnover}₽",
        "",
    ]

    for s in sales[offset : offset + limit]:
        # Форматируем дату если она в формате datetime
        created_at = s.get("created_at", "")
        if isinstance(created_at, str) and "T" in created_at:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_at = dt.strftime("%d.%m.%Y %H:%M")
            except:
                pass

        lines.append(
            f"№{s['id']} • {created_at} • {s.get('username') or s['user_id']} • {s['total_price']}₽"
        )
        for it in s.get("items", [])[:10]:
            taste = f" ({it['selected_taste']})" if it.get("selected_taste") else ""
            lines.append(
                f"  - {it['name']}{taste} x{it['quantity']} = {it['total_price']}₽"
            )

    remaining = max(len(sales) - (offset + limit), 0)
    if remaining:
        lines.append(f"… и еще {remaining} заказов")

    return "\n".join(lines), remaining


def _format_turnover(response: dict) -> str:
    period = response.get("period", {})
    start = period.get("start", "")
    end = period.get("end", "")
    turnover = response.get("turnover", 0)
    orders_count = response.get("orders_count", 0)
    return (
        f"💵 Оборот\n"
        f"Период: {start} — {end}\n"
        f"Заказов: {orders_count}\n"
        f"Сумма: {turnover}₽"
    )


async def _handle_analytics(
    callback: CallbackQuery, endpoint: str, period_key: str | None, state: FSMContext
):
    base_url = os.getenv("BACKEND_URL", "https://tgifts.space")
    params = {"period": period_key} if period_key else None
    try:
        data = await _fetch_json(f"{base_url}{endpoint}", params)
        if (
            endpoint.endswith("/sales")
            or endpoint.endswith("/canceled_orders")
            or endpoint.endswith("/completed_orders")
        ):
            is_canceled = endpoint.endswith("/canceled_orders")
            is_completed = endpoint.endswith("/completed_orders")
            text, remaining = _format_sales(
                data, is_canceled=is_canceled, is_completed=is_completed
            )
            kb = None
            if remaining:
                if endpoint.endswith("/canceled_orders"):
                    callback_prefix = "an_canceled_more"
                elif endpoint.endswith("/completed_orders"):
                    callback_prefix = "an_completed_more"
                else:
                    callback_prefix = "an_sales_more"
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Показать ещё",
                                callback_data=f"{callback_prefix}_20_{period_key or 'custom'}",
                            )
                        ]
                    ]
                )
            await callback.message.answer(text, reply_markup=kb)
        else:
            await callback.message.answer(_format_turnover(data))
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка запроса аналитики: {e}")
    finally:
        await callback.answer()


@dp.callback_query(F.data.startswith("an_sales_more_"))
async def on_sales_more(callback: CallbackQuery):
    try:
        # Парсим callback_data: an_sales_more_20_custom
        parts = callback.data.split("_")
        offset = int(parts[3])  # parts[3] = "20"
        period = (
            "_".join(parts[4:]) if len(parts) > 4 else "custom"
        )  # parts[4:] = ["custom"]
        base_url = os.getenv("BACKEND_URL", "https://tgifts.space")

        params = {"period": None if period == "custom" else period}
        data = await _fetch_json(f"{base_url}/analytics/sales", params)

        text, remaining = _format_sales(
            data, offset=offset, limit=20, is_canceled=False, is_completed=False
        )

        kb = None
        buttons = []
        if remaining:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="Показать ещё",
                        callback_data=f"an_sales_more_{offset + 20}_{period}",
                    )
                ]
            )
        if offset > 0:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data=f"an_sales_more_{max(0, offset - 20)}_{period}",
                    )
                ]
            )

        if buttons:
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Редактируем существующее сообщение вместо создания нового
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()


@dp.callback_query(
    F.data.in_(
        {"an_period_today", "an_period_yesterday", "an_period_week", "an_period_month"}
    )
)
async def on_period_quick(callback: CallbackQuery, state: FSMContext):
    # Определяем, что именно запросил пользователь: продажи, оборот, отмененные или завершенные заказы
    last_text = callback.message.text or ""
    is_sales = "продаж" in last_text.lower()
    is_canceled = "отменен" in last_text.lower()
    is_completed = "завершен" in last_text.lower()
    period_map = {
        "an_period_today": "today",
        "an_period_yesterday": "yesterday",
        "an_period_week": "week",
        "an_period_month": "month",
    }
    period = period_map.get(callback.data, "today")

    if is_canceled:
        endpoint = "/analytics/canceled_orders"
    elif is_completed:
        endpoint = "/analytics/completed_orders"
    elif is_sales:
        endpoint = "/analytics/sales"
    else:
        endpoint = "/analytics/turnover"

    await _handle_analytics(callback, endpoint, period, state)


@dp.callback_query(F.data == "an_period_custom")
async def on_period_custom(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AnalyticsStates.waiting_for_period_input)
    await callback.message.answer("Введите период в формате YYYY-MM-DD YYYY-MM-DD")
    await callback.answer()


@dp.message(AnalyticsStates.waiting_for_period_input)
async def on_period_input(message: Message, state: FSMContext):
    try:
        parts = (message.text or "").split()
        if len(parts) != 2:
            await message.answer("Формат: YYYY-MM-DD YYYY-MM-DD")
            return
        start, end = parts
        # По умолчанию показываем продажи. Для оборота — отправьте команду «💵 Оборот» и выберите произвольный период.
        # Определяем тип отчета по последнему запросному сообщению пользователя не всегда надежно, поэтому выводим все варианты кнопками.
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Показать продажи",
                        callback_data=f"an_custom_sales_{start}_{end}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Показать оборот",
                        callback_data=f"an_custom_turnover_{start}_{end}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Показать отмененные",
                        callback_data=f"an_custom_canceled_{start}_{end}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Показать завершенные",
                        callback_data=f"an_custom_completed_{start}_{end}",
                    )
                ],
            ]
        )
        await message.answer("Выберите тип отчета:", reply_markup=kb)
    finally:
        await state.clear()


@dp.callback_query(F.data.startswith("an_custom_sales_"))
async def on_custom_sales(callback: CallbackQuery):
    _, _, start, end = callback.data.split("_", 3)
    base_url = os.getenv("BACKEND_URL", "https://tgifts.space")
    try:
        data = await _fetch_json(
            f"{base_url}/analytics/sales", {"start": start, "end": end}
        )
        text, remaining = _format_sales(data, is_canceled=False, is_completed=False)
        kb = None
        if remaining:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Показать ещё",
                            callback_data="an_sales_more_20_custom",
                        )
                    ]
                ]
            )
        await callback.message.answer(text, reply_markup=kb)
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()


@dp.callback_query(F.data.startswith("an_custom_turnover_"))
async def on_custom_turnover(callback: CallbackQuery):
    _, _, start, end = callback.data.split("_", 3)
    base_url = os.getenv("BACKEND_URL", "https://tgifts.space")
    try:
        data = await _fetch_json(
            f"{base_url}/analytics/turnover", {"start": start, "end": end}
        )
        await callback.message.answer(_format_turnover(data))
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()


@dp.callback_query(F.data.startswith("an_custom_canceled_"))
async def on_custom_canceled(callback: CallbackQuery):
    _, _, start, end = callback.data.split("_", 3)
    base_url = os.getenv("BACKEND_URL", "https://tgifts.space")
    try:
        data = await _fetch_json(
            f"{base_url}/analytics/canceled_orders", {"start": start, "end": end}
        )
        text, remaining = _format_sales(data, is_canceled=True, is_completed=False)
        kb = None
        if remaining:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Показать ещё",
                            callback_data="an_canceled_more_20_custom",
                        )
                    ]
                ]
            )
        await callback.message.answer(text, reply_markup=kb)
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()


@dp.callback_query(F.data.startswith("an_custom_completed_"))
async def on_custom_completed(callback: CallbackQuery):
    _, _, start, end = callback.data.split("_", 3)
    base_url = os.getenv("BACKEND_URL", "https://tgifts.space")
    try:
        data = await _fetch_json(
            f"{base_url}/analytics/completed_orders", {"start": start, "end": end}
        )
        text, remaining = _format_sales(data, is_completed=True)
        kb = None
        if remaining:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Показать ещё",
                            callback_data="an_completed_more_20_custom",
                        )
                    ]
                ]
            )
        await callback.message.answer(text, reply_markup=kb)
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()


@dp.callback_query(F.data.startswith("an_canceled_more_"))
async def on_canceled_more(callback: CallbackQuery):
    try:
        # Парсим callback_data: an_canceled_more_20_custom
        parts = callback.data.split("_")
        offset = int(parts[3])  # parts[3] = "20"
        period = (
            "_".join(parts[4:]) if len(parts) > 4 else "custom"
        )  # parts[4:] = ["custom"]
        base_url = os.getenv("BACKEND_URL", "https://tgifts.space")

        params = {"period": None if period == "custom" else period}
        data = await _fetch_json(f"{base_url}/analytics/canceled_orders", params)

        text, remaining = _format_sales(
            data, offset=offset, limit=20, is_canceled=True, is_completed=False
        )

        kb = None
        buttons = []
        if remaining:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="Показать ещё",
                        callback_data=f"an_canceled_more_{offset + 20}_{period}",
                    )
                ]
            )
        if offset > 0:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data=f"an_canceled_more_{max(0, offset - 20)}_{period}",
                    )
                ]
            )

        if buttons:
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Редактируем существующее сообщение вместо создания нового
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()


@dp.callback_query(F.data.startswith("an_completed_more_"))
async def on_completed_more(callback: CallbackQuery):
    try:
        # Парсим callback_data: an_completed_more_20_custom
        parts = callback.data.split("_")
        offset = int(parts[3])  # parts[3] = "20"
        period = (
            "_".join(parts[4:]) if len(parts) > 4 else "custom"
        )  # parts[4:] = ["custom"]
        base_url = os.getenv("BACKEND_URL", "https://tgifts.space")

        params = {"period": None if period == "custom" else period}
        data = await _fetch_json(f"{base_url}/analytics/completed_orders", params)

        text, remaining = _format_sales(
            data, offset=offset, limit=20, is_completed=True
        )

        kb = None
        buttons = []
        if remaining:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="Показать ещё",
                        callback_data=f"an_completed_more_{offset + 20}_{period}",
                    )
                ]
            )
        if offset > 0:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data=f"an_completed_more_{max(0, offset - 20)}_{period}",
                    )
                ]
            )

        if buttons:
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
    finally:
        await callback.answer()


@dp.message(F.text == "🍓 Управление вкусами товара")
async def manage_item_tastes_start(message: Message):
    if message.from_user.id not in ADMINS:
        return

    async with AsyncSessionLocal() as session:
        items = (
            (await session.execute(select(Item).order_by(Item.name))).scalars().all()
        )
        if not items:
            await message.answer("ℹ️ Нет товаров для управления вкусами")
            return
        builder = InlineKeyboardBuilder()
        for item in items:
            builder.add(
                InlineKeyboardButton(
                    text=f"{item.name} (ID: {item.id})",
                    callback_data=f"manage_tastes_item_{item.id}",
                )
            )
        builder.adjust(1)
        await message.answer("Выберите товар:", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("manage_tastes_item_"))
async def manage_item_tastes(callback: CallbackQuery):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        item = (
            (
                await session.execute(
                    select(Item)
                    .where(Item.id == item_id)
                    .options(selectinload(Item.tastes))
                )
            )
            .scalars()
            .first()
        )
        if not item:
            await callback.answer("Товар не найден", show_alert=True)
            return

        add_builder = InlineKeyboardBuilder()
        add_builder.row(
            InlineKeyboardButton(
                text="🆕 Создать новый вкус",
                callback_data=f"create_new_taste_{item.id}",
            ),
            InlineKeyboardButton(
                text="🔍 Поиск вкуса", callback_data=f"search_taste_{item.id}"
            ),
            InlineKeyboardButton(
                text="🗑 Удалить вкус", callback_data=f"taste_remove_{item.id}"
            ),
        )

        await callback.message.answer(
            f"Выберите что вы хотите сделать с вкусами для {item.name}:",
            reply_markup=add_builder.as_markup(),
        )

    await callback.answer()


@dp.callback_query(F.data.startswith("taste_add_"))
async def taste_add(callback: CallbackQuery):
    try:
        _, _, item_id_str, taste_id_str = callback.data.split("_", 3)
        item_id = int(item_id_str)
        taste_id = int(taste_id_str)
    except Exception:
        await callback.answer("Неверные параметры", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(item_taste_association).where(
                item_taste_association.c.item_id == item_id,
                item_taste_association.c.taste_id == taste_id,
            )
        )
        if existing.first() is None:
            await session.execute(
                insert(item_taste_association).values(
                    item_id=item_id, taste_id=taste_id
                )
            )
            await session.commit()
            await callback.answer("Вкус добавлен", show_alert=False)
        else:
            await callback.answer("Вкус уже добавлен", show_alert=True)


@dp.callback_query(F.data.startswith("taste_remove_"))
async def taste_remove(callback: CallbackQuery):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        item = (
            (
                await session.execute(
                    select(Item)
                    .where(Item.id == item_id)
                    .options(selectinload(Item.tastes))
                )
            )
            .scalars()
            .first()
        )
        if not item:
            await callback.answer("Товар не найден", show_alert=True)
            return

    all_tastes = (
        (await session.execute(select(Taste).order_by(Taste.name))).scalars().all()
    )
    attached_ids = {t.id for t in (item.tastes or [])}
    attached = [t for t in all_tastes if t.id in attached_ids]

    MAX_BUTTONS_PER_PAGE = 90
    if attached:
        rm_builder = InlineKeyboardBuilder()
        attached_to_show = attached[:MAX_BUTTONS_PER_PAGE]
        for t in attached_to_show:
            rm_builder.add(
                InlineKeyboardButton(
                    text=f"❌ {t.name}",
                    callback_data=f"taste_delete_{item.id}_{t.id}",
                )
            )
            rm_builder.adjust(2)

        # Если вкусов больше чем лимит, показываем предупреждение
        if len(attached) > MAX_BUTTONS_PER_PAGE:
            rm_builder.row(
                InlineKeyboardButton(
                    text=f"⚠️ Показано {MAX_BUTTONS_PER_PAGE} из {len(attached)} вкусов",
                    callback_data="noop",
                )
            )

        await callback.message.answer(
            f"Удалить вкусы у «{item.name}»:",
            reply_markup=rm_builder.as_markup(),
        )
    else:
        await callback.message.answer("У товара пока нет прикрепленных вкусов")


@dp.callback_query(F.data.startswith("taste_delete_"))
async def delete_taste_start(callback: CallbackQuery):
    try:
        _, _, item_id_str, taste_id_str = callback.data.split("_", 3)
        item_id = int(item_id_str)
        taste_id = int(taste_id_str)
    except Exception:
        await callback.answer("Неверные параметры", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(item_taste_association).where(
                item_taste_association.c.item_id == item_id,
                item_taste_association.c.taste_id == taste_id,
            )
        )
        await session.commit()
        await callback.answer("Вкус удален", show_alert=False)


@dp.callback_query(F.data.startswith("create_new_taste_"))
async def create_new_taste_start(callback: CallbackQuery, state: FSMContext):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID товара", show_alert=True)
        return

    await state.update_data(item_id=item_id)
    await state.set_state(TasteStates.waiting_for_taste_name)

    await callback.message.answer("Введите название нового вкуса:")
    await callback.answer()


@dp.message(TasteStates.waiting_for_taste_name)
async def create_new_taste_process(message: Message, state: FSMContext):
    taste_name = message.text.strip()
    if not taste_name:
        await message.answer("Название вкуса не может быть пустым. Попробуйте еще раз:")
        return

    await state.update_data(taste_name=taste_name)

    await state.set_state(TasteStates.waiting_for_taste_image)
    await message.answer("🖼️ Отправьте изображение вкуса:")


@dp.message(TasteStates.waiting_for_taste_image, F.photo)
async def process_item_image(message: Message, state: FSMContext):
    try:
        photo = message.photo[-1]
        image_path = await save_photo(photo.file_id)

    except Exception as e:
        logger.error(f"Error saving photo: {e}")
        await message.answer(
            "❌ Ошибка при сохранении изображения. Попробуйте еще раз."
        )
        await state.set_state(TasteStates.waiting_for_taste_image)

    data = await state.get_data()
    item_id = data.get("item_id")
    taste_name = data.get("taste_name")

    if not item_id:
        await message.answer("Ошибка: не найден ID товара. Попробуйте заново.")
        await state.clear()
        return

    async with AsyncSessionLocal() as session:
        # Проверяем, не существует ли уже вкус с таким названием
        existing_taste = (
            (await session.execute(select(Taste).where(Taste.name == taste_name)))
            .scalars()
            .first()
        )

        if existing_taste:
            await message.answer(
                f"Вкус «{taste_name}» уже существует. Попробуйте другое название:"
            )
            return

        new_taste = Taste(name=taste_name, image=image_path)
        session.add(new_taste)
        await session.flush()

        await session.execute(
            insert(item_taste_association).values(
                item_id=item_id,
                taste_id=new_taste.id,
            )
        )

        await session.commit()

        item = (
            (await session.execute(select(Item).where(Item.id == item_id)))
            .scalars()
            .first()
        )

        item_name = item.name if item else f"товар ID {item_id}"

        await message.answer(
            f"✅ Вкус «{taste_name}» создан и добавлен к товару «{item_name}»"
        )


@dp.callback_query(F.data.startswith("search_taste_"))
async def search_taste_start(callback: CallbackQuery, state: FSMContext):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    # Сохраняем ID товара в состоянии
    await state.update_data(item_id=item_id)
    await state.set_state(TasteStates.waiting_for_taste_search)

    await callback.message.answer(
        "🔍 Введите название вкуса для поиска (можно частично):"
    )
    await callback.answer()


@dp.message(TasteStates.waiting_for_taste_search)
async def search_taste_process(message: Message, state: FSMContext):
    search_query = message.text.strip()
    if not search_query:
        await message.answer("Введите название вкуса для поиска:")
        return

    data = await state.get_data()
    item_id = data.get("item_id")

    if not item_id:
        await message.answer("Ошибка: не найден ID товара. Попробуйте заново.")
        await state.clear()
        return

    async with AsyncSessionLocal() as session:
        # Загружаем товар с его вкусами
        item = (
            (
                await session.execute(
                    select(Item)
                    .where(Item.id == item_id)
                    .options(selectinload(Item.tastes))
                )
            )
            .scalars()
            .first()
        )
        if not item:
            await message.answer("Товар не найден")
            await state.clear()
            return

        # Ищем вкусы по частичному совпадению
        search_pattern = f"%{search_query}%"
        found_tastes = (
            (
                await session.execute(
                    select(Taste)
                    .where(Taste.name.ilike(search_pattern))
                    .order_by(Taste.name)
                )
            )
            .scalars()
            .all()
        )

        attached_ids = {t.id for t in (item.tastes or [])}
        available = [t for t in found_tastes if t.id not in attached_ids]
        attached = [t for t in found_tastes if t.id in attached_ids]

        if not found_tastes:
            await message.answer(f"❌ Вкусы по запросу «{search_query}» не найдены")
            await state.clear()
            return

        # Показываем найденные вкусы для добавления
        if available:
            add_builder = InlineKeyboardBuilder()
            add_builder.row(
                InlineKeyboardButton(
                    text="🆕 Создать новый вкус",
                    callback_data=f"create_new_taste_{item_id}",
                )
            )

            # Ограничиваем количество кнопок
            MAX_BUTTONS_PER_PAGE = 90
            tastes_to_show = available[:MAX_BUTTONS_PER_PAGE]
            for t in tastes_to_show:
                add_builder.add(
                    InlineKeyboardButton(
                        text=f"➕ {t.name}", callback_data=f"taste_add_{item_id}_{t.id}"
                    )
                )
            add_builder.adjust(2)

            if len(available) > MAX_BUTTONS_PER_PAGE:
                add_builder.row(
                    InlineKeyboardButton(
                        text=f"⚠️ Показано {MAX_BUTTONS_PER_PAGE} из {len(available)} найденных вкусов",
                        callback_data="noop",
                    )
                )

            await message.answer(
                f"🔍 Найденные вкусы по запросу «{search_query}» для добавления к «{item.name}»:",
                reply_markup=add_builder.as_markup(),
            )

        # Показываем найденные вкусы для удаления
        if attached:
            rm_builder = InlineKeyboardBuilder()
            attached_to_show = attached[:MAX_BUTTONS_PER_PAGE]
            for t in attached_to_show:
                rm_builder.add(
                    InlineKeyboardButton(
                        text=f"❌ {t.name}",
                        callback_data=f"taste_remove_{item_id}_{t.id}",
                    )
                )
            rm_builder.adjust(2)

            if len(attached) > MAX_BUTTONS_PER_PAGE:
                rm_builder.row(
                    InlineKeyboardButton(
                        text=f"⚠️ Показано {MAX_BUTTONS_PER_PAGE} из {len(attached)} найденных вкусов",
                        callback_data="noop",
                    )
                )

            await message.answer(
                f"🔍 Найденные вкусы по запросу «{search_query}» для удаления у «{item.name}»:",
                reply_markup=rm_builder.as_markup(),
            )

    await state.clear()


@dp.message(F.text == "📦 Редактировать товар")
async def manage_item_start(message: Message):
    if message.from_user.id not in ADMINS:
        return

    async with AsyncSessionLocal() as session:
        items = (
            (await session.execute(select(Item).order_by(Item.name))).scalars().all()
        )
        if not items:
            await message.answer("ℹ️ Нет товаров")
            return
        builder = InlineKeyboardBuilder()
        for item in items:
            builder.add(
                InlineKeyboardButton(
                    text=f"{item.name} (ID: {item.id})",
                    callback_data=f"manage_item_{item.id}",
                )
            )
        builder.adjust(1)
        await message.answer("Выберите товар:", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("manage_item_"))
async def manage_item(callback: CallbackQuery):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    add_builder = InlineKeyboardBuilder()
    add_builder.row(
        InlineKeyboardButton(
            text="Название",
            callback_data=f"edit_item_name_{item_id}",
        ),
        InlineKeyboardButton(
            text="Характеристики",
            callback_data=f"edit_item_characteristics_{item_id}",
        ),
        InlineKeyboardButton(
            text="Фото",
            callback_data=f"edit_item_photo_{item_id}",
        ),
        InlineKeyboardButton(
            text="Цена",
            callback_data=f"edit_item_price_{item_id}",
        ),
    )

    await callback.message.answer(
        "Выберите пункт для редактирования:",
        reply_markup=add_builder.as_markup(),
    )


@dp.callback_query(F.data.startswith("edit_item_name_"))
async def edit_item_name(callback: CallbackQuery, state: FSMContext):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    await state.update_data(item_id=item_id)
    await state.set_state(ItemNameEditStates.waiting_for_item_name)

    await callback.message.answer(
        f"Введите новое название для товара с ID {item_id}:",
    )


@dp.message(ItemNameEditStates.waiting_for_item_name)
async def renaming_item(message: Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("Введите корректное новое название товара:")
        return

    data = await state.get_data()
    item_id = data.get("item_id")

    if not item_id:
        await message.answer("Ошибка: не найден ID товара. Попробуйте заново.")
        await state.clear()
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Item).where(Item.id == item_id))
        item = result.scalars().first()

        if not item:
            await message.answer("Товар не найден.")
            await state.clear()
            return
        item.name = new_name
        await session.commit()

    await message.answer(
        f"✅ Товар успешно переименован в: <b>{new_name}</b>", parse_mode="HTML"
    )
    await state.clear()


@dp.callback_query(F.data.startswith("edit_item_characteristics_"))
async def edit_item_characteristics(callback: CallbackQuery, state: FSMContext):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    await state.update_data(item_id=item_id)
    await state.set_state(
        ItemCharacteristicsEditStates.waiting_for_item_characteristics
    )

    await callback.message.answer(
        f"Введите новые характеристики для товара с ID {item_id}:",
    )


@dp.message(ItemCharacteristicsEditStates.waiting_for_item_characteristics)
async def renaming_characteristics(message: Message, state: FSMContext):
    new_description = message.text.strip()
    if not new_description:
        await message.answer("Введите корректные характеристики товара:")
        return

    data = await state.get_data()
    item_id = data.get("item_id")

    if not item_id:
        await message.answer("Ошибка: не найден ID товара. Попробуйте заново.")
        await state.clear()
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Item).where(Item.id == item_id))
        item = result.scalars().first()

        if not item:
            await message.answer("Товар не найден.")
            await state.clear()
            return

        item.description = new_description
        await session.commit()

    await message.answer("✅ Характеристики успешно изменены.")
    await state.clear()


@dp.callback_query(F.data.startswith("edit_item_photo_"))
async def edit_item_photo(callback: CallbackQuery, state: FSMContext):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    await state.update_data(item_id=item_id)
    await state.set_state(ItemImageEditStates.waiting_for_item_image)

    await callback.message.answer(
        f"Отправьте новое изображение для товара с ID {item_id}:",
    )


@dp.message(ItemImageEditStates.waiting_for_item_image, F.photo)
async def process_item_photo(message: Message, state: FSMContext):
    try:
        photo = message.photo[-1]
        image_path = await save_photo(photo.file_id)
        data = await state.get_data()

        item_id = data.get("item_id")
        if not item_id:
            await message.answer("❌ Ошибка: не найден ID товара. Попробуйте заново.")
            await state.clear()
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Item).where(Item.id == item_id))
            item = result.scalar_one_or_none()

            if not item:
                await message.answer("❌ Товар не найден.")
                await state.clear()
                return

            if item.image:
                old_path = item.image.lstrip("/")
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass

            item.image = image_path
            await session.commit()

            await message.answer("✅ Фото товара успешно обновлено!")
            await state.clear()

    except Exception as e:
        await message.answer(f"⚠️ Ошибка при обновлении фото: {e}")
        await state.clear()


@dp.callback_query(F.data.startswith("edit_item_price_"))
async def edit_item_price(callback: CallbackQuery, state: FSMContext):
    try:
        item_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("Неверный ID", show_alert=True)
        return

    await state.update_data(item_id=item_id)
    await state.set_state(ItemPriceEditStates.waiting_for_item_price)

    await callback.message.answer(
        f"Отправьте новую цену для товара с ID {item_id}:",
    )


@dp.message(ItemPriceEditStates.waiting_for_item_price)
async def change_item_price(message: Message, state: FSMContext):
    try:
        new_price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Введите корректное число для цены:")
        return

    data = await state.get_data()
    item_id = data.get("item_id")

    if not item_id:
        await message.answer("Ошибка: не найден ID товара. Попробуйте заново.")
        await state.clear()
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Item).where(Item.id == item_id))
        item = result.scalars().first()

        if not item:
            await message.answer("Товар не найден.")
            await state.clear()
            return

        item.price = new_price
        await session.commit()

    await message.answer(
        f"✅ Цена успешно изменена на: <b>{new_price:.2f}</b>", parse_mode="HTML"
    )
    await state.clear()


@dp.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Обработчик для информационных кнопок, которые не должны выполнять действий"""
    await callback.answer()


# Добавление курьера
@dp.message(F.text == "➕ Добавить курьера")
async def add_courier_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return

    await state.set_state(CourierStates.waiting_for_user_id)
    await message.answer("Отправьте ID нового курьера:")


@dp.message(CourierStates.waiting_for_user_id)
async def process_courier_user_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        await state.set_state(CourierStates.waiting_for_username)
        await message.answer("Введите username курьера (без @):")
    except ValueError:
        await message.answer("ID должен быть числом!")


@dp.message(CourierStates.waiting_for_username)
async def process_courier_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(CourierStates.waiting_for_phone)
    await message.answer("Введите телефон курьера:")


@dp.message(CourierStates.waiting_for_phone)
async def process_courier_phone(message: Message, state: FSMContext):
    try:
        phone = message.text
        if not phone:  # Проверка на пустое значение
            await message.answer(
                "Телефон не может быть пустым. Введите телефон курьера:"
            )
            return

        await state.update_data(phone=phone)
        await state.set_state(CourierStates.waiting_for_car_model)
        await message.answer("Введите модель машины курьера:")

    except Exception as e:
        logger.error(f"Ошибка при обработке телефона курьера: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
        await state.clear()


@dp.message(CourierStates.waiting_for_car_model)
async def process_courier_car_model(message: Message, state: FSMContext):
    try:
        data = await state.get_data()

        # Проверяем, что все данные есть
        if not all(k in data for k in ["user_id", "username", "phone"]):
            await message.answer("Ошибка: не все данные получены. Начните заново.")
            await state.clear()
            return

        car_model = message.text
        if not car_model:
            await message.answer("Модель машины не может быть пустой. Введите снова:")
            return

        async with AsyncSessionLocal() as session:
            # Проверяем существование курьера
            existing = await session.scalar(
                select(Courier).where(Courier.user_id == data["user_id"])
            )

            if existing:
                await message.answer("Этот пользователь уже зарегистрирован как курьер")
                await state.clear()
                return

            # Создаем курьера
            courier = Courier(
                user_id=data["user_id"],
                username=data["username"],
                phone=data["phone"],
                car_model=car_model,
                is_active=True,
            )

            session.add(courier)
            await session.commit()

            # Обновляем список COURIERS
            if courier.user_id not in COURIERS:
                COURIERS.append(courier.user_id)

            await message.answer(
                "✅ Курьер успешно добавлен!\n"
                f"ID: {courier.user_id}\n"
                f"Username: @{courier.username}\n"
                f"Телефон: {courier.phone}\n"
                f"Машина: {courier.car_model}"
            )

    except Exception as e:
        logger.error(f"Ошибка при создании курьера: {e}")
        await message.answer("Произошла ошибка при создании курьера. Попробуйте снова.")
    finally:
        await state.clear()


@dp.message(AdminStates.waiting_courier_id)
async def add_courier_process(message: Message, state: FSMContext):
    try:
        new_id = int(message.text)
        if new_id in COURIERS:
            await message.answer("Этот пользователь уже курьер!")
        else:
            COURIERS.append(new_id)
            await message.answer(f"✅ Пользователь {new_id} добавлен в курьеры")
    except ValueError:
        await message.answer("ID должен быть числом!")
    await state.clear()


# Удаление админа
@dp.message(F.text == "❌ Удалить админа")
async def remove_admin(message: Message):
    if len(ADMINS) <= 1:
        return await message.answer("Нельзя удалить последнего админа!")

    buttons = []
    for admin_id in ADMINS:
        if admin_id != message.from_user.id:  # Нельзя удалить себя
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"Удалить админа {admin_id}",
                        callback_data=f"remove_admin_{admin_id}",
                    )
                ]
            )

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите админа для удаления:", reply_markup=markup)


# Удаление курьера
@dp.message(F.text == "❌ Удалить курьера")
async def remove_courier(message: Message):
    buttons = []
    for courier_id in COURIERS:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Удалить курьера {courier_id}",
                    callback_data=f"remove_courier_{courier_id}",
                )
            ]
        )

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите курьера для удаления:", reply_markup=markup)


# Обработчики удаления
@dp.callback_query(F.data.startswith("remove_admin_"))
async def confirm_remove_admin(callback: CallbackQuery):
    admin_id = int(callback.data.split("_")[2])
    ADMINS.remove(admin_id)
    await callback.message.answer(f"Админ {admin_id} удалён")
    await callback.answer()


@dp.callback_query(F.data.startswith("remove_courier_"))
async def confirm_remove_courier(callback: CallbackQuery):
    courier_id = int(callback.data.split("_")[2])

    async with AsyncSessionLocal() as session:
        courier = await session.scalar(
            select(Courier).where(Courier.user_id == courier_id)
        )
        if courier:
            await session.delete(courier)
            await session.commit()

        if courier_id in COURIERS:
            COURIERS.remove(courier_id)

        await callback.message.answer(f"Курьер {courier_id} удалён")

    await callback.answer()


# Просмотр списков
@dp.message(F.text == "📋 Список админов")
async def show_admins(message: Message):
    text = "👑 Админы:\n" + "\n".join(str(id) for id in ADMINS)
    await message.answer(text)


@dp.message(F.text == "📋 Список курьеров")
async def show_couriers(message: Message):
    async with AsyncSessionLocal() as session:
        couriers = await session.execute(select(Courier).order_by(Courier.username))
        couriers = couriers.scalars().all()

        if not couriers:
            await message.answer("ℹ️ Нет зарегистрированных курьеров")
            return  # Исправлено: добавлен return

        for courier in couriers:
            status = "🟢 Активен" if courier.is_active else "🔴 Неактивен"
            await message.answer(
                f"🚴 Курьер: @{courier.username}\n"
                f"🆔 ID: {courier.user_id}\n"
                f"📱 Телефон: {courier.phone}\n"
                f"🚗 Машина: {courier.car_model}\n"
                f"Статус: {status}"
            )


# Создание категории
@dp.message(F.text == "📁 Создать категорию")
async def create_category_start(message: Message, state: FSMContext):
    """Начало создания категории"""
    await state.set_state(CategoryStates.waiting_for_name)
    await message.answer("📝 Введите название категории:")


@dp.message(CategoryStates.waiting_for_name)
async def process_category_name(message: Message, state: FSMContext):
    """Обработка названия категории"""
    await state.update_data(name=message.text)
    await state.set_state(CategoryStates.waiting_for_image)
    await message.answer("🖼️ Отправьте изображение категории:")


@dp.message(CategoryStates.waiting_for_image, F.photo)
async def process_category_image(message: Message, state: FSMContext):
    """Обработка изображения категории"""
    try:
        photo = message.photo[-1]
        image_path = await save_photo(photo.file_id)
        data = await state.get_data()

        async with AsyncSessionLocal() as session:
            # Проверяем, существует ли категория с таким именем
            existing_category = (
                await session.execute(
                    select(Category).where(Category.name == data["name"])
                )
            ).scalar_one_or_none()

            if existing_category:
                await message.answer("ℹ️ Категория с таким названием уже существует")
                await state.clear()
                return

            # Создаем новую категорию
            new_category = Category(name=data["name"], image=image_path)
            session.add(new_category)
            await session.commit()

            await message.answer(f"✅ Категория '{data['name']}' успешно создана!")

    except Exception as e:
        logger.error(f"Error creating category: {e}")
        await message.answer("❌ Произошла ошибка при создании категории")
    finally:
        await state.clear()


# Просмотр товаров и категорий
@dp.message(F.text == "🛍️ Список товаров")
async def list_items(message: Message):
    """Получение списка товаров"""
    try:
        async with AsyncSessionLocal() as session:
            items = (
                (
                    await session.execute(
                        select(Item).options(
                            selectinload(Item.category), selectinload(Item.tastes)
                        )
                    )
                )
                .scalars()
                .all()
            )

            if not items:
                await message.answer("ℹ️ Список товаров пуст")
                return

            for item in items:
                tastes = (
                    ", ".join([taste.name for taste in item.tastes])
                    if item.tastes
                    else "нет"
                )
                text = (
                    f"📌 {item.name}\n"
                    f"💰 Цена: {item.price} руб.\n"
                    f"📝 Описание: {item.description}\n"
                    f"🏷️ Категория: {item.category.name}\n"
                    f"🍓 Вкусы: {tastes}"
                )

                if item.image:
                    # Преобразуем относительный путь в полный путь для проверки существования файла
                    full_image_path = os.path.join(os.getcwd(), item.image.lstrip("/"))
                    if os.path.exists(full_image_path):
                        photo = FSInputFile(full_image_path)
                        await message.answer_photo(photo, caption=text)
                    else:
                        await message.answer(text)
                else:
                    await message.answer(text)

    except Exception as e:
        logger.error(f"Error getting items: {e}")
        await message.answer("❌ Произошла ошибка при получении списка товаров")


@dp.message(F.text == "🗂️ Список категорий")
async def list_categories(message: Message):
    """Получение списка категорий"""
    try:
        async with AsyncSessionLocal() as session:
            categories = (await session.execute(select(Category))).scalars().all()

            if not categories:
                await message.answer("ℹ️ Список категорий пуст")
                return

            for category in categories:
                text = f"🏷️ {category.name}"

                if category.image:
                    # Преобразуем относительный путь в полный путь для проверки существования файла
                    full_image_path = os.path.join(
                        os.getcwd(), category.image.lstrip("/")
                    )
                    if os.path.exists(full_image_path):
                        photo = FSInputFile(full_image_path)
                        await message.answer_photo(photo, caption=text)
                    else:
                        await message.answer(text)
                else:
                    await message.answer(text)

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        await message.answer("❌ Произошла ошибка при получении списка категорий")


# Обработчик кнопки удаления товара
@dp.message(F.text == "❌ Удалить товар")
async def delete_item_start(message: Message, state: FSMContext):
    """Начало процесса удаления товара"""
    async with AsyncSessionLocal() as session:
        items = await session.execute(select(Item))
        items = items.scalars().all()

        if not items:
            await message.answer("ℹ️ Нет товаров для удаления")
            return

        builder = InlineKeyboardBuilder()
        for item in items:
            builder.add(
                InlineKeyboardButton(
                    text=f"{item.name} (ID: {item.id})",
                    callback_data=f"delete_item_{item.id}",
                )
            )
        builder.adjust(1)

        await message.answer(
            "Выберите товар для удаления:", reply_markup=builder.as_markup()
        )


# Обработчик выбора товара для удаления
@dp.callback_query(F.data.startswith("delete_item_"))
async def confirm_delete_item(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара"""
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id)
    await state.set_state(DeleteStates.waiting_for_item_delete_confirm)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="confirm_delete_item"),
        InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete"),
    )

    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить товар с ID {item_id}?",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


# Обработчик подтверждения удаления товара
@dp.callback_query(
    F.data == "confirm_delete_item", DeleteStates.waiting_for_item_delete_confirm
)
async def process_delete_item(callback: CallbackQuery, state: FSMContext):
    """Процесс удаления товара"""
    data = await state.get_data()
    item_id = data["item_id"]

    try:
        async with AsyncSessionLocal() as session:
            # Получаем товар
            item = await session.get(Item, item_id)
            if not item:
                await callback.answer("Товар не найден")
                return

            # Удаляем связи с вкусами
            await session.execute(
                delete(item_taste_association).where(
                    item_taste_association.c.item_id == item_id
                )
            )

            # Удаляем сам товар
            await session.delete(item)
            await session.commit()

            await callback.message.edit_text(f"✅ Товар с ID {item_id} успешно удален!")
    except Exception as e:
        logger.error(f"Ошибка удаления товара: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении товара")
    finally:
        await state.clear()
        await callback.answer()


# Обработчик кнопки удаления категории
@dp.message(F.text == "❌ Удалить категорию")
async def delete_category_start(message: Message, state: FSMContext):
    """Начало процесса удаления категории"""
    async with AsyncSessionLocal() as session:
        categories = await session.execute(select(Category))
        categories = categories.scalars().all()

        if not categories:
            await message.answer("ℹ️ Нет категорий для удаления")
            return

        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.add(
                InlineKeyboardButton(
                    text=f"{category.name} (ID: {category.id})",
                    callback_data=f"delete_category_{category.id}",
                )
            )
        builder.adjust(1)

        await message.answer(
            "Выберите категорию для удаления:", reply_markup=builder.as_markup()
        )


# Обработчик выбора категории для удаления
@dp.callback_query(F.data.startswith("delete_category_"))
async def confirm_delete_category(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления категории"""
    category_id = int(callback.data.split("_")[2])

    async with AsyncSessionLocal() as session:
        # Проверяем есть ли товары в категории
        items_count = await session.scalar(
            select(func.count(Item.id)).where(Item.category_id == category_id)
        )

        if items_count > 0:
            await callback.answer(
                "❌ В категории есть товары. Сначала удалите их.", show_alert=True
            )
            return

    await state.update_data(category_id=category_id)
    await state.set_state(DeleteStates.waiting_for_category_delete_confirm)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="confirm_delete_category"),
        InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete"),
    )

    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить категорию с ID {category_id}?",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


# Обработчик подтверждения удаления категории
@dp.callback_query(
    F.data == "confirm_delete_category",
    DeleteStates.waiting_for_category_delete_confirm,
)
async def process_delete_category(callback: CallbackQuery, state: FSMContext):
    """Процесс удаления категории"""
    data = await state.get_data()
    category_id = data["category_id"]

    try:
        async with AsyncSessionLocal() as session:
            category = await session.get(Category, category_id)
            if not category:
                await callback.answer("Категория не найдена")
                return

            await session.delete(category)
            await session.commit()

            await callback.message.edit_text(
                f"✅ Категория с ID {category_id} успешно удалена!"
            )
    except Exception as e:
        logger.error(f"Ошибка удаления категории: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении категории")
    finally:
        await state.clear()
        await callback.answer()


# Обработчик отмены удаления
@dp.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса удаления"""
    await state.clear()
    await callback.message.edit_text("❌ Удаление отменено")
    await callback.answer()


# Обработчик создания промокода
@dp.message(F.text == "🎫 Создать промокод")
async def create_promocode_start(message: Message, state: FSMContext):
    """Начало создания промокода"""
    await state.set_state(PromocodeStates.waiting_for_promocode_name)
    await message.answer("📝 Введите название промокода:")


@dp.message(PromocodeStates.waiting_for_promocode_name)
async def process_promocode_name(message: Message, state: FSMContext):
    """Обработка названия промокода"""
    name = message.text.strip()
    if not name:
        await message.answer("❌ Название промокода не может быть пустым")
        return

    async with AsyncSessionLocal() as session:
        # Проверяем, существует ли промокод с таким именем
        existing = await session.scalar(select(Promocode).where(Promocode.name == name))

        if existing:
            await message.answer("❌ Промокод с таким названием уже существует")
            await state.clear()
            return

        await state.update_data(name=name)
        await state.set_state(PromocodeStates.waiting_for_promocode_percentage)
        await message.answer("💯 Введите размер скидки в процентах (1-100):")


@dp.message(PromocodeStates.waiting_for_promocode_percentage)
async def process_promocode_percentage(message: Message, state: FSMContext):
    """Обработка процента скидки промокода"""
    try:
        percentage = int(message.text)
        if not 1 <= percentage <= 100:
            raise ValueError

        data = await state.get_data()
        name = data["name"]

        async with AsyncSessionLocal() as session:
            new_promo = Promocode(name=name, percentage=percentage)
            session.add(new_promo)
            await session.commit()

            await message.answer(
                f"✅ Промокод создан!\nНазвание: {name}\nСкидка: {percentage}%"
            )

    except ValueError:
        await message.answer("❌ Пожалуйста, введите число от 1 до 100")
        return

    await state.clear()


# Просмотр списка промокодов
@dp.message(F.text == "📜 Список промокодов")
async def list_promocodes(message: Message):
    """Отображение списка всех промокодов"""
    async with AsyncSessionLocal() as session:
        promocodes = await session.execute(select(Promocode))
        promocodes = promocodes.scalars().all()

        if not promocodes:
            await message.answer("ℹ️ Нет созданных промокодов")
            return

        text = "📜 Список промокодов:\n\n"
        for promo in promocodes:
            text += (
                f"🎫 Название: {promo.name}\n"
                f"🔹 Скидка: {promo.percentage}%\n"
                f"🔹 ID: {promo.id}\n\n"
            )

        await message.answer(text)


# Удаление промокода
@dp.message(F.text == "❌ Удалить промокод")
async def delete_promocode_start(message: Message, state: FSMContext):
    """Начало процесса удаления промокода"""
    async with AsyncSessionLocal() as session:
        promocodes = await session.execute(select(Promocode))
        promocodes = promocodes.scalars().all()

        if not promocodes:
            await message.answer("ℹ️ Нет промокодов для удаления")
            return

        builder = InlineKeyboardBuilder()
        for promo in promocodes:
            builder.add(
                InlineKeyboardButton(
                    text=f"{promo.name} (ID: {promo.id})",
                    callback_data=f"delete_promo_{promo.id}",
                )
            )
        builder.adjust(1)

        await message.answer(
            "Выберите промокод для удаления:", reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data.startswith("delete_promo_"))
async def confirm_delete_promocode(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления промокода"""
    promo_id = int(callback.data.split("_")[2])
    await state.update_data(promo_id=promo_id)
    await state.set_state(PromocodeStates.waiting_for_promocode_delete_confirm)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="confirm_delete_promo"),
        InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete"),
    )

    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить промокод с ID {promo_id}?",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@dp.callback_query(
    F.data == "confirm_delete_promo",
    PromocodeStates.waiting_for_promocode_delete_confirm,
)
async def process_delete_promocode(callback: CallbackQuery, state: FSMContext):
    """Процесс удаления промокода"""
    data = await state.get_data()
    promo_id = data["promo_id"]

    try:
        async with AsyncSessionLocal() as session:
            promo = await session.get(Promocode, promo_id)
            if not promo:
                await callback.answer("Промокод не найден")
                return

            await session.delete(promo)
            await session.commit()

            await callback.message.edit_text(
                f"✅ Промокод с ID {promo_id} успешно удален!"
            )
    except Exception as e:
        logger.error(f"Ошибка удаления промокода: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении промокода")
    finally:
        await state.clear()
        await callback.answer()


async def is_courier_or_admin(user_id: int) -> bool:
    return user_id in COURIERS or user_id in ADMINS


# ============= УПРАВЛЕНИЕ ПРОФИЛЕМ ЛОЯЛЬНОСТИ =============

@dp.message(Command("set_loyalty"))
async def set_loyalty_start(message: Message, state: FSMContext):
    """Начало процесса настройки профиля лояльности пользователя"""
    if message.from_user.id not in ADMINS:
        await message.answer("❌ Эта команда доступна только для администраторов")
        return
    
    await state.set_state(LoyaltyManagementStates.waiting_for_user_id)
    await message.answer(
        "🎯 Управление профилем лояльности\n\n"
        "Введите @username пользователя:"
    )


@dp.message(LoyaltyManagementStates.waiting_for_user_id)
async def set_loyalty_get_user(message: Message, state: FSMContext):
    """Получение username пользователя и вывод текущих данных"""
    # Убираем @ если есть и пробелы
    username = message.text.strip().lstrip('@')
    
    async with AsyncSessionLocal() as session:
        # Находим пользователя по username
        result = await session.execute(
            select(DBUser).where(DBUser.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                f"❌ Пользователь @{username} не найден в базе.\n"
                "Попробуйте другой username:"
            )
            return
        
        # Сохраняем telegram_id в состояние
        await state.update_data(user_telegram_id=user.telegram_id)
        
        # Показываем текущие данные
        await message.answer(
            f"👤 Пользователь: @{user.username or 'нет username'}\n"
            f"🆔 ID: {user.telegram_id}\n\n"
            f"📊 Текущие данные лояльности:\n"
            f"🎴 Уровень карты: {user.loyalty_level}\n"
            f"⭐ Штампов: {user.stamps}/6\n"
            f"📦 Всего куплено товаров: {user.total_items_purchased}\n\n"
            "Выберите, что хотите изменить:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎴 Уровень карты", callback_data="loyalty_set_level")],
                [InlineKeyboardButton(text="⭐ Количество штампов", callback_data="loyalty_set_stamps")],
                [InlineKeyboardButton(text="📦 Всего товаров", callback_data="loyalty_set_total")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="loyalty_cancel")]
            ])
        )


@dp.callback_query(F.data == "loyalty_set_level")
async def set_loyalty_level_menu(callback: CallbackQuery, state: FSMContext):
    """Выбор уровня карты лояльности"""
    await state.set_state(LoyaltyManagementStates.waiting_for_loyalty_level)
    await callback.message.edit_text(
        "🎴 Выберите уровень карты лояльности:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚪ White (25%)", callback_data="level_White")],
            [InlineKeyboardButton(text="💜 Platinum (30%)", callback_data="level_Platinum")],
            [InlineKeyboardButton(text="⚫ Black (35%)", callback_data="level_Black")],
            [InlineKeyboardButton(text="« Назад", callback_data="loyalty_back")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("level_"))
async def process_loyalty_level(callback: CallbackQuery, state: FSMContext):
    """Сохранение выбранного уровня карты"""
    level = callback.data.split("_")[1]
    data = await state.get_data()
    user_telegram_id = data.get("user_telegram_id")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DBUser).where(DBUser.telegram_id == user_telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.loyalty_level = level
            await session.commit()
            
            level_emoji = {"White": "⚪", "Platinum": "💜", "Black": "⚫"}
            await callback.message.edit_text(
                f"✅ Уровень карты изменен на {level_emoji.get(level, '')} {level}\n\n"
                "Что еще хотите изменить?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⭐ Количество штампов", callback_data="loyalty_set_stamps")],
                    [InlineKeyboardButton(text="📦 Всего товаров", callback_data="loyalty_set_total")],
                    [InlineKeyboardButton(text="✅ Завершить", callback_data="loyalty_finish")]
                ])
            )
    
    await callback.answer()


@dp.callback_query(F.data == "loyalty_set_stamps")
async def set_loyalty_stamps_menu(callback: CallbackQuery, state: FSMContext):
    """Выбор количества штампов"""
    await state.set_state(LoyaltyManagementStates.waiting_for_stamps)
    await callback.message.edit_text(
        "⭐ Введите количество штампов (0-5):"
    )
    await callback.answer()


@dp.message(LoyaltyManagementStates.waiting_for_stamps)
async def process_loyalty_stamps(message: Message, state: FSMContext):
    """Сохранение количества штампов"""
    try:
        stamps = int(message.text.strip())
        
        if stamps < 0 or stamps > 5:
            await message.answer("❌ Количество штампов должно быть от 0 до 5. Попробуйте снова:")
            return
        
        data = await state.get_data()
        user_telegram_id = data.get("user_telegram_id")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DBUser).where(DBUser.telegram_id == user_telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.stamps = stamps
                await session.commit()
                
                await message.answer(
                    f"✅ Количество штампов установлено: {stamps}/6\n\n"
                    "Что еще хотите изменить?",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎴 Уровень карты", callback_data="loyalty_set_level")],
                        [InlineKeyboardButton(text="📦 Всего товаров", callback_data="loyalty_set_total")],
                        [InlineKeyboardButton(text="✅ Завершить", callback_data="loyalty_finish")]
                    ])
                )
    
    except ValueError:
        await message.answer("❌ Неверный формат. Введите число от 0 до 5:")


@dp.callback_query(F.data == "loyalty_set_total")
async def set_loyalty_total_menu(callback: CallbackQuery, state: FSMContext):
    """Установка общего количества купленных товаров"""
    await state.set_state(LoyaltyManagementStates.waiting_for_total_items)
    await callback.message.edit_text(
        "📦 Введите общее количество купленных товаров:"
    )
    await callback.answer()


@dp.message(LoyaltyManagementStates.waiting_for_total_items)
async def process_loyalty_total(message: Message, state: FSMContext):
    """Сохранение общего количества товаров"""
    try:
        total_items = int(message.text.strip())
        
        if total_items < 0:
            await message.answer("❌ Количество должно быть положительным числом. Попробуйте снова:")
            return
        
        data = await state.get_data()
        user_telegram_id = data.get("user_telegram_id")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DBUser).where(DBUser.telegram_id == user_telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.total_items_purchased = total_items
                await session.commit()
                
                await message.answer(
                    f"✅ Общее количество товаров установлено: {total_items}\n\n"
                    "Что еще хотите изменить?",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎴 Уровень карты", callback_data="loyalty_set_level")],
                        [InlineKeyboardButton(text="⭐ Количество штампов", callback_data="loyalty_set_stamps")],
                        [InlineKeyboardButton(text="✅ Завершить", callback_data="loyalty_finish")]
                    ])
                )
    
    except ValueError:
        await message.answer("❌ Неверный формат. Введите положительное число:")


@dp.callback_query(F.data == "loyalty_back")
async def loyalty_back(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору параметров"""
    data = await state.get_data()
    user_telegram_id = data.get("user_telegram_id")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DBUser).where(DBUser.telegram_id == user_telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            await callback.message.edit_text(
                f"👤 Пользователь: @{user.username or 'нет username'}\n"
                f"🆔 ID: {user.telegram_id}\n\n"
                f"📊 Текущие данные лояльности:\n"
                f"🎴 Уровень карты: {user.loyalty_level}\n"
                f"⭐ Штампов: {user.stamps}/6\n"
                f"📦 Всего куплено товаров: {user.total_items_purchased}\n\n"
                "Выберите, что хотите изменить:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎴 Уровень карты", callback_data="loyalty_set_level")],
                    [InlineKeyboardButton(text="⭐ Количество штампов", callback_data="loyalty_set_stamps")],
                    [InlineKeyboardButton(text="📦 Всего товаров", callback_data="loyalty_set_total")],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="loyalty_cancel")]
                ])
            )
    
    await callback.answer()


@dp.callback_query(F.data == "loyalty_finish")
async def loyalty_finish(callback: CallbackQuery, state: FSMContext):
    """Завершение настройки профиля лояльности"""
    data = await state.get_data()
    user_telegram_id = data.get("user_telegram_id")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DBUser).where(DBUser.telegram_id == user_telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            await callback.message.edit_text(
                f"✅ Профиль лояльности обновлен!\n\n"
                f"👤 Пользователь: @{user.username or 'нет username'}\n"
                f"🆔 ID: {user.telegram_id}\n\n"
                f"📊 Новые данные:\n"
                f"🎴 Уровень карты: {user.loyalty_level}\n"
                f"⭐ Штампов: {user.stamps}/6\n"
                f"📦 Всего куплено товаров: {user.total_items_purchased}"
            )
    
    await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "loyalty_cancel")
async def loyalty_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена настройки профиля лояльности"""
    await callback.message.edit_text("❌ Настройка профиля лояльности отменена")
    await state.clear()
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
