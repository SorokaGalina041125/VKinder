"""
Модуль для работы с интересами пользователей
"""
import logging
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Кэш для интересов (чтобы не запрашивать повторно)
_interests_cache = {}


def get_user_groups(vk, user_id: int) -> List[dict]:
    """Получение групп пользователя из VK"""
    try:
        groups = vk.groups.get(
            user_id=user_id,
            extended=1,
            fields='name, members_count',
            count=100
        )
        return groups.get('items', [])
    except Exception as e:
        logger.error(f"Ошибка получения групп для {user_id}: {e}")
        return []


def get_user_music(vk, user_id: int) -> List[str]:
    """Получение любимой музыки пользователя (из аудиозаписей)"""
    try:
        audio = vk.audio.get(owner_id=user_id, count=50)
        return [item.get('artist') + ' - ' + item.get('title') 
                for item in audio.get('items', [])]
    except Exception as e:
        logger.debug(f"Не удалось получить музыку для {user_id}: {e}")
        return []


def get_user_books(vk, user_id: int) -> List[str]:
    """Получение любимых книг пользователя из профиля"""
    try:
        user = vk.users.get(
            user_ids=user_id,
            fields='books'
        )[0]
        books = user.get('books', '')
        if books:
            return [b.strip() for b in books.split(',') if b.strip()]
        return []
    except Exception as e:
        logger.debug(f"Не удалось получить книги для {user_id}: {e}")
        return []


def get_user_interests_from_profile(vk, user_id: int) -> List[str]:
    """Получение интересов из профиля пользователя"""
    try:
        user = vk.users.get(
            user_ids=user_id,
            fields='interests'
        )[0]
        interests = user.get('interests', '')
        if interests:
            return [i.strip() for i in interests.split(',') if i.strip()]
        return []
    except Exception as e:
        logger.debug(f"Не удалось получить интересы для {user_id}: {e}")
        return []


def collect_user_interests(vk, user_id: int, use_cache: bool = True) -> Dict:
    """
    Сбор всех интересов пользователя.
    
    Args:
        vk: VK API объект
        user_id: ID пользователя
        use_cache: использовать ли кэш
    
    Returns:
        Dict: словарь с интересами {'music': [], 'books': [], 'groups': []}
    """
    # Проверяем кэш
    if use_cache and user_id in _interests_cache:
        logger.debug(f"Возвращаем интересы из кэша для {user_id}")
        return _interests_cache[user_id]
    
    logger.info(f"Сбор интересов для пользователя {user_id}")
    
    interests = {
        'music': [],
        'books': [],
        'groups': [],
        'interests': []  # дополнительные интересы из профиля
    }
    
    # Получаем группы
    groups = get_user_groups(vk, user_id)
    interests['groups'] = [g.get('name') for g in groups if g.get('name')]
    
    # Получаем музыку (если доступно)
    music = get_user_music(vk, user_id)
    interests['music'] = music
    
    # Получаем книги
    books = get_user_books(vk, user_id)
    interests['books'] = books
    
    # Получаем интересы из профиля
    profile_interests = get_user_interests_from_profile(vk, user_id)
    interests['interests'] = profile_interests
    
    # Небольшая задержка, чтобы избежать rate limiting
    time.sleep(0.3)
    
    # Сохраняем в кэш
    if use_cache:
        _interests_cache[user_id] = interests
    
    logger.info(f"Собрано для {user_id}: групп={len(interests['groups'])}, "
                f"музыки={len(interests['music'])}, книг={len(interests['books'])}")
    
    return interests


def get_interest_weight(interest_type: str) -> float:
    """
    Получение веса для типа интереса (требование 12).
    
    Веса определяют важность каждого типа интереса при расчете совместимости.
    """
    weights = {
        'groups': 0.4,      # Общие группы важнее всего
        'music': 0.35,      # Музыка чуть менее важна
        'books': 0.25,      # Книги наименее важны
        'interests': 0.3,   # Дополнительные интересы
    }
    return weights.get(interest_type, 0.3)


def calculate_interest_similarity(
    user_interests: Dict,
    candidate_interests: Dict
) -> Dict[str, int]:
    """
    Вычисление пересечений интересов между двумя пользователями.
    
    Returns:
        Dict: {'music': count, 'books': count, 'groups': count, 'total': count}
    """
    overlap = {
        'music': 0,
        'books': 0,
        'groups': 0,
        'interests': 0,
        'total': 0
    }
    
    # Пересечение по музыке
    user_music = set(user_interests.get('music', []))
    candidate_music = set(candidate_interests.get('music', []))
    overlap['music'] = len(user_music & candidate_music)
    
    # Пересечение по книгам
    user_books = set(user_interests.get('books', []))
    candidate_books = set(candidate_interests.get('books', []))
    overlap['books'] = len(user_books & candidate_books)
    
    # Пересечение по группам
    user_groups = set(user_interests.get('groups', []))
    candidate_groups = set(candidate_interests.get('groups', []))
    overlap['groups'] = len(user_groups & candidate_groups)
    
    # Пересечение по дополнительным интересам
    user_extra = set(user_interests.get('interests', []))
    candidate_extra = set(candidate_interests.get('interests', []))
    overlap['interests'] = len(user_extra & candidate_extra)
    
    # Общая сумма
    overlap['total'] = (
        overlap['music'] + 
        overlap['books'] + 
        overlap['groups'] + 
        overlap['interests']
    )
    
    return overlap


def get_interests_text(interests: Dict) -> str:
    """
    Форматирование интересов для вывода пользователю.
    """
    parts = []
    
    if interests.get('groups'):
        parts.append(f"📁 Группы: {', '.join(interests['groups'][:5])}")
    
    if interests.get('music'):
        parts.append(f"🎵 Музыка: {', '.join(interests['music'][:5])}")
    
    if interests.get('books'):
        parts.append(f"📚 Книги: {', '.join(interests['books'][:5])}")
    
    if interests.get('interests'):
        parts.append(f"✨ Интересы: {', '.join(interests['interests'][:5])}")
    
    if not parts:
        return "Интересы не указаны"
    
    return '\n'.join(parts)


def clear_interests_cache(user_id: Optional[int] = None):
    """
    Очистка кэша интересов.
    
    Args:
        user_id: если указан, очищает только для конкретного пользователя
    """
    global _interests_cache
    
    if user_id:
        _interests_cache.pop(user_id, None)
        logger.debug(f"Очищен кэш интересов для {user_id}")
    else:
        _interests_cache.clear()
        logger.debug("Очищен весь кэш интересов")