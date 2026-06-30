from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

class DownloadCB(CallbackData, prefix="dl"):
    video_id: str
    quality: str

def get_quality_kb(video_id: str, heights: list):
    builder = InlineKeyboardBuilder()
    for h in heights:
        builder.button(text=f"🎬 {h}p", callback_data=DownloadCB(video_id=video_id, quality=str(h)))
    builder.button(text="🎵 Аудио (MP3)", callback_data=DownloadCB(video_id=video_id, quality="audio"))
    builder.adjust(2)
    return builder.as_markup()

def get_admin_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="🚫 Забанить", callback_data="admin_ban")
    builder.button(text="✅ Разбанить", callback_data="admin_unban")
    builder.adjust(2)
    return builder.as_markup()
