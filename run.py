import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.database.models import init_db, get_session
from bot.database.seed import seed_places, seed_real_libraries
from bot.services.admin import setup_admin
from bot.handlers import add_place, admin_panel, auth, booking, contact_admin, favorites, location, menu, places, reviews, search, start
from bot.middlewares.block import BlockMiddleware

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN .env faylida belgilanmagan!")
        sys.exit(1)

    init_db()
    seed_places()
    seed_real_libraries()

    session = get_session()
    try:
        setup_admin(session)
    finally:
        session.close()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(BlockMiddleware())
    dp.callback_query.middleware(BlockMiddleware())

    dp.include_router(start.router)
    dp.include_router(contact_admin.router)
    dp.include_router(menu.router)
    dp.include_router(auth.router)
    dp.include_router(favorites.router)
    dp.include_router(places.router)
    dp.include_router(location.router)
    dp.include_router(search.router)
    dp.include_router(booking.router)
    dp.include_router(reviews.router)
    dp.include_router(add_place.router)
    dp.include_router(admin_panel.router)

    logger.info("QuietSpace Tashkent bot ishga tushmoqda...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
