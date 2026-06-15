import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

from app.config import settings
from app.database import engine
from app.database.base import Base
from app.handlers import main_router
from app.middlewares import DbSessionMiddleware, UserMiddleware
from app.repositories import AdminRepository
from app.database import async_session
from app.utils.scheduler import expire_subscriptions_task

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")


async def setup_default_data():
    async with async_session() as session:
        admin_repo = AdminRepository(session)
        await admin_repo.ensure_default_plans()
    logger.info("Default data initialized.")


async def main():
    await create_tables()
    await setup_default_data()

    storage = RedisStorage.from_url(settings.REDIS_URL)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=storage)

    # Register middlewares on each update type so event is the correct type
    for observer in [
        dp.message,
        dp.callback_query,
        dp.chat_member,
        dp.my_chat_member,
    ]:
        observer.middleware(DbSessionMiddleware())
        observer.middleware(UserMiddleware())

    dp.include_router(main_router)

    asyncio.create_task(expire_subscriptions_task())

    logger.info("Bot started.")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
