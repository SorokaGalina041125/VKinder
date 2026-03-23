"""
Общие утилиты для бота.
Вынесены в отдельный модуль для избежания циклических импортов.
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def send_msg(vk, user_id: int, message: str, keyboard=None, attachment: Optional[str] = None):
    """
    Отправка сообщения в ВК.
    
    Args:
        vk: VK API объект
        user_id: ID пользователя
        message: текст сообщения
        keyboard: объект клавиатуры VkKeyboard
        attachment: вложение (фото, документ и т.д.)
    """
    post_params = {
        "user_id": user_id,
        "message": message,
        "random_id": 0
    }
    
    if keyboard:
        post_params["keyboard"] = keyboard.get_keyboard()
    if attachment:
        post_params["attachment"] = attachment
    
    try:
        vk.messages.send(**post_params)
        logger.debug(f"Message sent to {user_id}: {message[:50]}...")
    except Exception as e:
        logger.error(f"Error sending message to {user_id}: {e}")


def format_age(age: int) -> str:
    """
    Форматирование возраста с правильным склонением.
    
    Args:
        age: возраст (число)
    
    Returns:
        str: возраст с правильным окончанием (например, "21 год", "25 лет")
    """
    if age is None:
        return "возраст не указан"
    
    if 10 <= age % 100 <= 20:
        suffix = "лет"
    elif age % 10 == 1:
        suffix = "год"
    elif 2 <= age % 10 <= 4:
        suffix = "года"
    else:
        suffix = "лет"
    
    return f"{age} {suffix}"


def format_candidate_name(first_name: str, last_name: str) -> str:
    """
    Форматирование имени кандидата.
    
    Args:
        first_name: имя
        last_name: фамилия
    
    Returns:
        str: отформатированное имя
    """
    return f"{first_name} {last_name}".strip()


def extract_number_from_text(text: str) -> Optional[int]:
    """
    Извлечение числа из текста.
    
    Args:
        text: текст сообщения
    
    Returns:
        Optional[int]: извлеченное число или None
    """
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return None


def format_photo_attachment(owner_id: int, photo_id: str) -> str:
    """
    Форматирование фото для attachment.
    
    Args:
        owner_id: ID владельца фото
        photo_id: ID фото
    
    Returns:
        str: строка для attachment (photo123456_789)
    """
    return f"photo{owner_id}_{photo_id}"


def format_photos_attachment(photos: list) -> str:
    """
    Форматирование списка фото для attachment.
    
    Args:
        photos: список словарей с ключами owner_id и photo_id
    
    Returns:
        str: строка для attachment, фото через запятую
    """
    return ",".join([format_photo_attachment(p['owner_id'], p['photo_id']) for p in photos])


def get_last_candidate_id(db, user_id: int) -> Optional[int]:
    """
    Получить ID последнего показанного кандидата.
    
    Args:
        db: сессия базы данных
        user_id: ID пользователя
    
    Returns:
        Optional[int]: ID последнего показанного кандидата или None
    """
    from app.database.models import ViewedUser
    
    last_viewed = db.query(ViewedUser).filter_by(
        user_vk_id=user_id
    ).order_by(ViewedUser.id.desc()).first()
    
    return last_viewed.viewed_user_vk_id if last_viewed else None


def get_last_candidate(db, user_id: int):
    """
    Получить объект последнего показанного кандидата.
    
    Args:
        db: сессия базы данных
        user_id: ID пользователя
    
    Returns:
        Optional[User]: объект последнего показанного кандидата или None
    """
    from app.database.models import User
    
    candidate_id = get_last_candidate_id(db, user_id)
    if candidate_id:
        return db.get(User, candidate_id)
    return None