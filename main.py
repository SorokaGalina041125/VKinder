"""
Application entry point for VKinder.
"""
import logging
import sys

import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

from app.bot.handlers.message import handle_message
from app.config import settings
from app.database.engine import get_db, init_models


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def run_bot() -> None:
    """Start the community bot and listen for new messages."""
    if not settings.VK_GROUP_TOKEN:
        logger.error("VK_GROUP_TOKEN не найден")
        return
    if not settings.VK_USER_TOKEN:
        logger.error("VK_USER_TOKEN не найден")
        return

    vk_session = vk_api.VkApi(token=settings.VK_GROUP_TOKEN)
    vk = vk_session.get_api()

    group_id = settings.VK_GROUP_ID
    if not group_id:
        group_info = vk.groups.getById()[0]
        group_id = group_info["id"]

    longpoll = VkBotLongPoll(vk_session, group_id)
    logger.info("Бот запущен и готов к приему сообщений")

    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW or not getattr(event, "message", None):
            continue

        try:
            db_gen = get_db()
            db = next(db_gen)

            handle_message(db, vk, event)

            try:
                next(db_gen)
            except StopIteration:
                pass

        except Exception as e:
            user_id = getattr(getattr(event, "message", None), "from_id", None)
            logger.error(
                f"Ошибка при обработке сообщения от {user_id}: {e}",
                exc_info=True,
            )


if __name__ == "__main__":
    try:
        logger.info("Инициализация БД")
        init_models()
        logger.info("База данных готова")
        run_bot()
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}", exc_info=True)
        raise
