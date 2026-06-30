import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
import yt_dlp

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN") or "7548847926:AAHszy_asqXAOX6faKs6Z32FJLQYc1DOOdY"
ADMIN_ID = os.getenv("ADMIN_ID") or "7921743592"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Функция для скачивания видео (работает в фоновом потоке)
def download_video(url):
    # Создаем папку для загрузок, если её нет
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    outtmpl = 'downloads/%(id)s.%(ext)s'
    
    ydl_opts = {
        # Ищем лучшее качество, но строго в формате mp4, чтобы Telegram мог его воспроизвести
        'format': 'best[ext=mp4]/best',
        'outtmpl': outtmpl,
        'no_warnings': True,
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        # На всякий случай проверяем расширение файла
        base, _ = os.path.splitext(filename)
        real_filename = base + ".mp4"
        
        if os.path.exists(real_filename):
            return real_filename
        return filename

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n\n"
        "Отправь мне ссылку на YouTube видео или Shorts, и я пришлю тебе его в формате MP4!"
    )

@dp.message()
async def handle_message(message: types.Message):
    text = message.text or ""
    
    if "youtube.com" in text or "youtu.be" in text:
        status_msg = await message.answer("⏳ Скачиваю видео, пожалуйста, подождите...")
        
        try:
            # Запускаем скачивание в отдельном потоке, чтобы бот не "усыпал"
            loop = asyncio.get_event_loop()
            file_path = await loop.run_in_executor(None, download_video, text)
            
            if os.path.exists(file_path):
                await status_msg.edit_text("🚀 Видео скачано! Отправляю в чат...")
                
                # Отправляем видеофайл
                video_file = FSInputFile(file_path)
                await message.answer_video(video=video_file, caption="Твое видео готово! 🎬")
                
                # Удаляем файл с сервера хостинга, чтобы не забивать память
                os.remove(file_path)
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Ошибка: не удалось найти скачанный файл на сервере.")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке: {e}")
            await status_msg.edit_text(f"❌ Произошла ошибка при скачивании: {e}")
    else:
        await message.answer("Пожалуйста, отправь мне рабочую ссылку на YouTube.")

async def main():
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    print("Бот запущен!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
