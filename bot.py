import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
from database.db import init_db
from utils.logger import logger

load_dotenv()

# Support both TELEGRAM_TOKEN and BOT_TOKEN environment variable names.
API_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")

if not API_TOKEN:
    raise RuntimeError("Telegram token not found. Set TELEGRAM_TOKEN (or BOT_TOKEN) in the environment or .env file")

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

