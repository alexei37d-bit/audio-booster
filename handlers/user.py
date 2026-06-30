import os
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
import database as db
from utils.downloader import get_video_metadata, download_video
from keyboards import get_quality_kb, DownloadCB

user_router = Router()
ANTIFLOOD_CACHE = {}

@user_router.message(CommandStart())
async def start_cmd(message: Message):
    if await db.is_banned(message.from_user.id): return
    await db.add_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Отправь мне ссылку на YouTube видео или Shorts, и я помогу его скачать.")

@user_router.message(F.text.regexp(r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([a-zA-Z0-9_-]+)"))
async def process_link(message: Message):
    user_id = message.from_user.id
    if await db.is_banned(user_id): return
    
    # Антифлуд (5 секунд)
    now = time.time()
    if user_id in ANTIFLOOD_CACHE and now - ANTIFLOOD_CACHE[user_id] < 5:
        await message.answer("⚠️ Подождите немного перед следующей ссылкой.")
        return
    ANTIFLOOD_CACHE[user_id] = now

    msg = await message.answer("🔍 Получаю информацию о видео...")
    meta = await get_video_metadata(message.text)
    
    if not meta:
        return await msg.edit_text("❌ Ошибка! Проверьте ссылку. Возможно, видео приватное или удалено.")

    kb = get_quality_kb(meta['id'], meta['heights'])
    text = f"🎬 **{meta['title']}**\n⏱ Длительность: {meta['duration']} сек."
    
    if meta['thumbnail']:
        await message.answer_photo(photo=meta['thumbnail'], caption=text, reply_markup=kb, parse_mode="Markdown")
        await msg.delete()
    else:
        await msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@user_router.callback_query(DownloadCB.filter())
async def process_download(call: CallbackQuery, callback_data: DownloadCB, bot: Bot):
    if await db.is_banned(call.from_user.id): return
    
    msg = await call.message.answer("📥 Скачиваю файл... Это может занять время.")
    await call.answer()
    
    file_path = await download_video(callback_data.video_id, callback_data.quality)
    
    if not file_path or not os.path.exists(file_path):
        return await msg.edit_text("❌ Ошибка при скачивании файла.")

    # Проверка размера файла (Лимит Telegram Bot API = 50MB)
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > 50:
        os.remove(file_path)
        return await msg.edit_text(
            f"⚠️ Файл слишком большой ({size_mb:.1f} МБ).\n"
            "Лимит Telegram для ботов — 50 МБ. Выберите меньшее разрешение.\n\n"
            "*Опционально:* Чтобы отправлять файлы до 2000 МБ, администратору необходимо "
            "поднять Local Bot API Server и указать его URL в инициализации бота."
        )

    await msg.edit_text("🚀 Отправляю файл...")
    
    try:
        doc = FSInputFile(file_path)
        if callback_data.quality == "audio":
            await bot.send_audio(call.message.chat.id, doc)
        else:
            await bot.send_video(call.message.chat.id, doc)
            
        await db.log_download(call.from_user.id, callback_data.video_id, callback_data.quality)
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка отправки: {e}")
    finally:
        await msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path) # Очистка временных файлов
