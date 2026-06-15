import asyncio
import logging
from app.database import async_session
from app.repositories import SubscriptionRepository

logger = logging.getLogger(__name__)


async def expire_subscriptions_task():
    while True:
        try:
            async with async_session() as session:
                repo = SubscriptionRepository(session)
                count = await repo.expire_old()
                if count:
                    logger.info(f"Expired {count} subscriptions")
        except Exception as e:
            logger.error(f"Error in expire_subscriptions_task: {e}")
        await asyncio.sleep(3600)
