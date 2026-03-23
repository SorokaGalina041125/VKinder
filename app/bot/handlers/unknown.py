"""
Обработка неизвестных команд
"""
from app.bot.utils import send_msg
from app.bot.keyboards import get_main_keyboard


def handle_unknown(vk, user_id, send_msg_func=None):
    """
    Обработка неизвестных команд.
    
    Args:
        vk: VK API объект
        user_id: ID пользователя
        send_msg_func: функция отправки сообщения (опционально)
    """
    msg_func = send_msg_func or send_msg
    msg_func(vk, user_id, "Используйте кнопки меню.", get_main_keyboard())