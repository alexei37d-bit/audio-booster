from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import config
import database as db
from keyboards import get_admin_kb
from utils.states import AdminStates

admin_router = Router()

@admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != config.ADMIN_ID: return
    await message.answer("🔧 Админ-панель", reply_markup=get_admin_kb())

@admin_router.callback_query(F.data == "admin_stats")
async def show_stats(call: CallbackQuery):
    if call.from_user.id != config.ADMIN_ID: return
    total_u, total_d, today_d = await db.get_stats()
    text = f"📊 **Статистика:**\n👥 Юзеров: {total_u}\n📥 Скачиваний: {total_d}\n📅 Скачиваний сегодня: {today_d}"
    await call.message.answer(text, parse_mode="Markdown")
    await call.answer()

@admin_router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != config.ADMIN_ID: return
    await state.set_state(AdminStates.broadcast)
    await call.message.answer("Введите сообщение для рассылки:")
    await call.answer()

@admin_router.message(AdminStates.broadcast)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = await db.get_all_user_ids()
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, message.text)
            sent += 1
        except Exception:
            pass
    await message.answer(f"✅ Рассылка завершена. Доставлено: {sent}/{len(users)}")

@admin_router.callback_query(F.data.in_({"admin_ban", "admin_unban"}))
async def start_ban_system(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != config.ADMIN_ID: return
    if call.data == "admin_ban":
        await state.set_state(AdminStates.ban_user)
        await call.message.answer("Введите ID пользователя для БАНА:")
    else:
        await state.set_state(AdminStates.unban_user)
        await call.message.answer("Введите ID пользователя для РАЗБАНА:")
    await call.answer()

@admin_router.message(AdminStates.ban_user)
async def process_ban(message: Message, state: FSMContext):
    await state.clear()
    try:
        await db.set_ban_status(int(message.text), 1)
        await message.answer("Пользователь забанен.")
    except ValueError:
        await message.answer("❌ ID должен быть числом.")

@admin_router.message(AdminStates.unban_user)
async def process_unban(message: Message, state: FSMContext):
    await state.clear()
    try:
        await db.set_ban_status(int(message.text), 0)
        await message.answer("Пользователь разбанен.")
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
