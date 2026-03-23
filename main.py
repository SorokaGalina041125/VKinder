"""
Точка входа в приложение VKinder
"""
import sys
import logging
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from app.config import settings
from app.database.engine import init_models, get_db
from app.bot.handlers.message import handle_message

# Принудительно устанавливаем UTF-8 для вывода в консоль (Windows)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_bot():
    """Запуск бота"""
    if not settings.VK_GROUP_TOKEN:
        logger.error("VK_GROUP_TOKEN не найден")
        return

    vk_session = vk_api.VkApi(token=settings.VK_GROUP_TOKEN)
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    
    logger.info("Бот запущен и готов к приему сообщений")
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                # Получаем сессию БД
                db_gen = get_db()
                db = next(db_gen)
                
                handle_message(db, vk, event)
                
                # Закрываем сессию
                try:
                    next(db_gen)
                except StopIteration:
                    pass
                    
            except Exception as e:
                logger.error(f"Ошибка при обработке сообщения от {event.user_id}: {e}")
                # Бот не падает, а продолжает слушать


if __name__ == "__main__":
    try:
        logger.info("Инициализация БД")
        init_models()
        logger.info("База данных готова")
        run_bot()
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
        exit(1)