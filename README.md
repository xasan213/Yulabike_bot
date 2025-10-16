# Velobike Bot (Aiogram 3)

Minimal scaffold for a bicycle rental Telegram bot using Aiogram 3 and SQLite.

Files of interest:

- `bot.py` - entry point
- `config.py` - configuration
- `database/` - DB models and helpers
- `handlers/` - Telegram handlers (start, customer, partner, admin)

Quick start:

1. Create a virtual environment and install dependencies:

   python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt

2. Fill `.env` with your `TELEGRAM_TOKEN`.

3. Run the bot:

   python bot.py

This scaffold uses SQLAlchemy (async) with `aiosqlite`. It includes basic routers and a simple DB layer. Expand handlers and services as your app requires.

## Deploy to Render (quick guide)

1. Push your project to a GitHub repository.
2. Sign in to <https://render.com> and create a new **Background Worker** service.
   - Connect your GitHub repo, choose the branch.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
3. Add Environment Variables in Render dashboard:
   - `TELEGRAM_TOKEN` — your bot token
   - `ADMIN_IDS` — comma-separated admin Telegram IDs
4. Deploy. Render will run the worker and keep the bot polling.

Note: Do not commit your `.env` to the repo; use Render environment variables instead. If you accidentally exposed your token, rotate it from BotFather immediately.
