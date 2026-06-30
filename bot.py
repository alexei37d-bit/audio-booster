import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Включаем логирование, чтобы видеть ошибки в панели хостинга
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки авторизации (если хостинг не передал переменные — берутся данные из кавычек)
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7548847926:AAHszy_asqXAOX6faKs6Z32FJLQYc1DOOdY"
ADMIN_ID = os.getenv("ADMIN_ID") or "7921743592"

# Инициализируем бота и диспетчер по стандартам aiogram 3.x
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Обработка команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n\n"
        "Я твой бот-загрузчик. Отправь мне ссылку на YouTube видео или Shorts, и я скачаю её!"
    )

# Обработка входящих сообщений со ссылками
@dp.message()
async def handle_message(message: types.Message):
    text = message.text or ""
    
    # Проверяем, есть ли в тексте намек на YouTube
    if "youtube.com" in text or "youtu.be" in text:
        await message.answer("⏳ Начинаю скачивание видео, подождите...")
        
        # СЮДА можно вставить твою функцию скачивания через yt-dlp, если она была готова.
        # Пока здесь просто текстовый ответ, чтобы бот не молчал.
        await message.answer("Видео успешно обработано! (Интегрируйте ваш код скачивания сюда)")
    else:
        await message.answer("Пожалуйста, отправь мне корректную ссылку на YouTube.")

# Главная функция запуска
async def main():
    logger.info("Бот подготавливается к запуску...")
    
    # Эта строчка обязательна для вывода в консоль, чтобы хостинг понял, что всё ОК
    print("Бот запущен!") 
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
