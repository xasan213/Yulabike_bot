import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
from database.db import init_db
from utils.logger import logger

load_dotenv()

def _read_token_from_file(path: str):
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            return fh.read().strip()
    except Exception:
        return None


def get_api_token():
    # 1) env vars
    token = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
    if token:
        return token.strip()

    # 2) token file path provided in env
    token_file = os.getenv('TOKEN_FILE')
    if token_file:
        t = _read_token_from_file(token_file)
        if t:
            return t

    # 3) common Docker secret locations
    for p in ('/run/secrets/TELEGRAM_TOKEN', '/run/secrets/telegram_token', '/var/run/secrets/telegram_token'):
        t = _read_token_from_file(p)
        if t:
            return t

    # 4) token.txt in repo root
    t = _read_token_from_file('token.txt')
    if t:
        return t

    # 5) last resort: try parse .env file manually if present
    try:
        import pathlib
        env_path = pathlib.Path('.') / '.env'
        if env_path.exists():
            for line in env_path.read_text(encoding='utf-8').splitlines():
                if line.strip().startswith('TELEGRAM_TOKEN') or line.strip().startswith('BOT_TOKEN'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        return parts[1].strip().strip('"').strip("'")
    except Exception:
        pass

    return None


API_TOKEN = get_api_token()

if not API_TOKEN:
    logger.error("Telegram token not found. Set TELEGRAM_TOKEN (or BOT_TOKEN) as an environment variable in your hosting provider (Railway/Render) or provide a token file via TOKEN_FILE.")
    logger.error("For local development you can place a .env file with TELEGRAM_TOKEN=... or create token.txt containing the token (not recommended for production).")
    raise RuntimeError("Telegram token not found. TELEGRAM_TOKEN (or BOT_TOKEN) must be set in the environment or provided via TOKEN_FILE/token.txt")

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # initialize database (create tables)
    await init_db()

    # import and include routers
    from handlers.start import router as start_router
    from handlers.customer import router as customer_router
    from handlers.partner import router as partner_router
    from handlers.admin import router as admin_router

    dp.include_router(start_router)
    dp.include_router(customer_router)
    dp.include_router(partner_router)
    dp.include_router(admin_router)

    try:
        logger.info("Bot starting")
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Unhandled exception in polling: %s", e)
        raise
    finally:
        try:
            await bot.session.close()
        except Exception:
            logger.exception("Failed to close bot session cleanly")

if __name__ == '__main__':
    asyncio.run(main())

