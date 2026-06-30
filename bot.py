import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN") or "7548847926:AAHszy_asqXAOX6faKs6Z32FJLQYc1DOOdY"
ADMIN_ID = os.getenv("ADMIN_ID") or "7921743592"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()  # Память для состояний (FSM) включается автоматически

# Определяем шаги опроса пользователя
class DownloadStates(StatesGroup):
    choosing_format = State()   # Шаг 1: Выбор Видео или Аудио
    choosing_quality = State()  # Шаг 2: Выбор разрешения (только для видео)

# Функция скачивания (без жесткого требования ffmpeg на сервере)
def download_media(url, media_type, quality):
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
        
    outtmpl = 'downloads/%(id)s.%(ext)s'
    
    if media_type == "audio":
        ydl_opts = {
            # Скачиваем аудио в формате m4a (Telegram воспроизводит его идеально как музыку)
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': outtmpl,
            'no_warnings': True,
            'quiet': True,
        }
    else:
        # Настройка качества видео (выбираем готовые mp4 стримы, чтобы серверу не требовался ffmpeg для склейки)
        if quality == "360":
            fmt_str = 'best[height<=360][ext=mp4]/best'
        elif quality == "720":
            fmt_str = 'best[height<=720][ext=mp4]/best'
        else:
            fmt_str = 'best[ext=mp4]/best'
            
        ydl_opts = {
            'format': fmt_str,
            'outtmpl': outtmpl,
            'no_warnings': True,
            'quiet': True,
        }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_id = info['id']
        
        # Находим реальный скачанный файл в папке по его ID
        for file in os.listdir("downloads"):
            if file.startswith(file_id):
                return os.path.join("downloads", file)
        return ydl.prepare_filename(info)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n\n"
        "Отправь мне ссылку на YouTube видео или Shorts, и ты сможешь сам выбрать формат и качество загрузки!"
    )

# 1. Ловим ссылку на YouTube
@dp.message(F.text.contains("youtube.com") | F.text.contains("youtu.be"))
async def handle_youtube_link(message: types.Message, state: FSMContext):
    url = message.text.strip()
    await state.update_data(url=url) # Запоминаем ссылку во временную память бота
    
    # Строим клавиатуру выбора формата
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Видео (MP4)", callback_data="fmt_video")
    builder.button(text="🎵 Аудио (Музыка)", callback_data="fmt_audio")
    builder.adjust(2)
    
    await message.answer("Что именно ты хочешь скачать?", reply_markup=builder.as_markup())
    await state.set_state(DownloadStates.choosing_format)

# 2. Обрабатываем выбор формата
@dp.callback_query(DownloadStates.choosing_format, F.data.startswith("fmt_"))
async def process_format(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    chosen_fmt = callback.data.split("_")[1]
    
    if chosen_fmt == "audio":
        # Для аудио качество выбирать не нужно — качаем сразу
        data = await state.get_data()
        url = data['url']
        await state.clear() # Очищаем состояние памяти
        
        status_msg = await callback.message.edit_text("⏳ Скачиваю аудиодорожку, пожалуйста, подождите...")
        asyncio.create_task(run_download(callback.message, status_msg, url, "audio", "best"))
    else:
        # Для видео предлагаем выбрать качество
        builder = InlineKeyboardBuilder()
        builder.button(text="📉 360p (Низкое)", callback_data="q_360")
        builder.button(text="📺 720p (Среднее)", callback_data="q_720")
        builder.button(text="🚀 Максимальное", callback_data="q_best")
        builder.adjust(1)
        
        await callback.message.edit_text("В каком качестве скачать видео?", reply_markup=builder.as_markup())
        await state.set_state(DownloadStates.choosing_quality)

# 3. Обрабатываем выбор качества видео
@dp.callback_query(DownloadStates.choosing_quality, F.data.startswith("q_"))
async def process_quality(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    chosen_quality = callback.data.split("_")[1]
    
    data = await state.get_data()
    url = data['url']
    await state.clear() # Очищаем состояние памяти
    
    status_msg = await callback.message.edit_text(f"⏳ Скачиваю видео в качестве ({chosen_quality}p)...")
    asyncio.create_task(run_download(callback.message, status_msg, url, "video", chosen_quality))

# Фоновая задача для скачивания и отправки файла
async def run_download(user_message: types.Message, status_message: types.Message, url: str, media_type: str, quality: str):
    try:
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_media, url, media_type, quality)
        
        if os.path.exists(file_path):
            await status_message.edit_text("🚀 Файл успешно загружен на сервер! Отправляю тебе...")
            
            input_file = FSInputFile(file_path)
            if media_type == "audio":
                await user_message.answer_audio(audio=input_file, caption="Твое аудио готово! 🎵")
            else:
                await user_message.answer_video(video=input_file, caption="Твое видео готово! 🎬")
                
            os.remove(file_path)  # Удаляем за собой файл, чтобы не забивать диск хостинга
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Ошибка: не удалось найти созданный файл.")
            
    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        await status_message.edit_text(f"❌ Произошла ошибка при обработке: {e}\nВозможно, видео слишком весит.")

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
