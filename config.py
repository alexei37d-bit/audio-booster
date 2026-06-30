import os
from dotenv import load_dotenv

load_dotenv()

# Бот сначала ищет переменные от хостинга, а если их нет — берет данные из кавычек
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7548847926:AAHszy_asqXAOX6faKs6Z32FJLQYc1DOOdY"
ADMIN_ID = int(os.getenv("ADMIN_ID") or 7921743592)

DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
