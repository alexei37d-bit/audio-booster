import asyncio
import os
import yt_dlp
from config import DOWNLOAD_DIR

def _extract_info(url: str) -> dict:
    opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.sanitize_info(ydl.extract_info(url, download=False))

async def get_video_metadata(url: str):
    try:
        meta = await asyncio.to_thread(_extract_info, url)
        formats = meta.get('formats', [])
        
        # Собираем доступные разрешения (исключаем аудио-only треки из списка видео)
        heights = {f['height'] for f in formats if f.get('vcodec') != 'none' and f.get('height') in [144, 360, 480, 720, 1080]}
        
        return {
            'id': meta.get('id'),
            'title': meta.get('title', 'Video'),
            'duration': meta.get('duration', 0),
            'thumbnail': meta.get('thumbnail'),
            'heights': sorted(list(heights))
        }
    except Exception:
        return None

def _download_media(url: str, format_spec: str, out_tmpl: str) -> str:
    opts = {'format': format_spec, 'outtmpl': out_tmpl, 'quiet': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def download_video(video_id: str, quality: str) -> str:
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    if quality == 'audio':
        fmt = 'bestaudio/best'
        out = os.path.join(DOWNLOAD_DIR, f"{video_id}_audio.%(ext)s")
    else:
        fmt = f"bestvideo[height<={quality}]+bestaudio/best"
        out = os.path.join(DOWNLOAD_DIR, f"{video_id}_{quality}.%(ext)s")
        
    try:
        file_path = await asyncio.to_thread(_download_media, url, fmt, out)
        
        # yt-dlp может менять расширение файла после склейки (например, на .mkv или .mp4)
        base_path, _ = os.path.splitext(file_path)
        for ext in ['.mp4', '.mkv', '.webm', '.m4a', '.mp3']:
            if os.path.exists(base_path + ext):
                return base_path + ext
        return file_path
    except Exception:
        return None
