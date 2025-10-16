import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).parent
DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite+aiosqlite:///{BASE_DIR / 'velobike.db'}")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS','').split(',') if x.strip()]

