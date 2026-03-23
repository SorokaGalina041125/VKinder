"""
Унифицированные обработчики для избранного, ЧС и лайков
"""
import logging
from app.database import crud
from app.bot.utils import send_msg, get_last_candidate_id, get_last_candidate
from app.bot.keyboards import get_main_keyboard, get_photo_actions_keyboard
from app.config import settings

logger = logging.getLogger(__name__)


# ========== ЛАЙКИ ==========

def handle_like(db, vk, user, text, payload=None):
    """Обработка лайка через payload"""
    from app.bot.search.vk_client import VKClient
    
    user_id = user.vk_id
    
    if payload:
        photo_owner_id = payload.get('owner_id')
        photo_id = payload.get('photo_id')
    else:
        # Fallback для текстовых команд
        photo_owner_id = None
        photo_id = None
    
    if not photo_owner_id or not photo_id:
        send_msg(vk, user_id, "❌ Не удалось определить фото", get_main_keyboard())
        return
    
    # Используем токен пользователя для лайков
    vk_client = VKClient(settings.VK_USER_TOKEN)
    
    if vk_client.add_like(photo_owner_id, photo_id):
        crud.content.add_like(db, user_id, photo_owner_id, photo_id)
        send_msg(vk, user_id, "❤️ Лайк поставлен!", get_main_keyboard())
    else:
        send_msg(vk, user_id, "⚠️ Не удалось поставить лайк", get_main_keyboard())


def handle_unlike(db, vk, user, text, payload=None):
    """Обработка снятия лайка через payload"""
    from app.bot.search.vk_client import VKClient
    
    user_id = user.vk_id
    
    if payload:
        photo_owner_id = payload.get('owner_id')
        photo_id = payload.get('photo_id')
    else:
        photo_owner_id = None
        photo_id = None
    
    if not photo_owner_id or not photo_id:
        send_msg(vk, user_id, "❌ Не удалось определить фото", get_main_keyboard())
        return
    
    # Используем токен пользователя для снятия лайков
    vk_client = VKClient(settings.VK_USER_TOKEN)
    
    if vk_client.remove_like(photo_owner_id, photo_id):
        crud.content.remove_like(db, user_id, photo_owner_id, photo_id)
        send_msg(vk, user_id, "💔 Лайк убран!", get_main_keyboard())
    else:
        send_msg(vk, user_id, "⚠️ Не удалось убрать лайк", get_main_keyboard())


def handle_back_to_candidate(db, vk, user, text, payload=None):
    """Возврат к кандидату из режима просмотра фото"""
    user_id = user.vk_id
    candidate = get_last_candidate(db, user_id)
    
    if candidate:
        from .search import show_candidate_by_id
        show_candidate_by_id(db, vk, user_id, candidate.vk_id, send_msg, 0, 0)
    else:
        send_msg(vk, user_id, "Нет активного кандидата", get_main_keyboard())


# ========== ИЗБРАННОЕ ==========

def handle_add_favorite(db, vk, user, text, payload=None, candidate_id=None):
    """Добавление в избранное"""
    user_id = user.vk_id
    
    if payload:
        candidate_id = payload.get('candidate_id')
    elif candidate_id is None:
        candidate_id = get_last_candidate_id(db, user_id)
    
    if not candidate_id:
        send_msg(vk, user_id, "Нет кандидата для добавления", get_main_keyboard())
        return
    
    if crud.viewed.add_to_favorites(db, user_id, candidate_id):
        send_msg(vk, user_id, "⭐ Добавлено в избранное!", get_main_keyboard())
    else:
        send_msg(vk, user_id, "⚠️ Уже в избранном", get_main_keyboard())


def handle_remove_favorite(db, vk, user, text, payload=None):
    """Удаление из избранного"""
    user_id = user.vk_id
    
    if payload:
        candidate_id = payload.get('candidate_id')
    else:
        candidate_id = get_last_candidate_id(db, user_id)
    
    if not candidate_id:
        send_msg(vk, user_id, "Нет кандидата для удаления", get_main_keyboard())
        return
    
    if crud.viewed.remove_from_favorites(db, user_id, candidate_id):
        send_msg(vk, user_id, "⭐ Удалено из избранного!", get_main_keyboard())
    else:
        send_msg(vk, user_id, "⚠️ Не найдено в избранном", get_main_keyboard())


def handle_show_favorites(db, vk, user, send_msg_func=None):
    """Показать избранное"""
    user_id = user.vk_id
    msg_func = send_msg_func or send_msg
    
    favorites = crud.viewed.get_user_favorites(db, user_id)
    
    if not favorites:
        msg_func(vk, user_id, "📭 Избранное пусто", get_main_keyboard())
        return
    
    from app.database.models import User
    
    message = "⭐ Ваши избранные:\n\n"
    for i, fav_id in enumerate(favorites[:10], 1):
        candidate = db.get(User, fav_id)
        if candidate:
            message += f"{i}. {candidate.first_name} {candidate.last_name}\n"
            message += f"   {candidate.profile_url}\n\n"
    
    if len(favorites) > 10:
        message += f"... и еще {len(favorites) - 10} анкет"
    
    msg_func(vk, user_id, message, get_main_keyboard())


# ========== ЧЕРНЫЙ СПИСОК ==========

def handle_add_blacklist(db, vk, user, text, payload=None, candidate_id=None):
    """Добавление в черный список"""
    user_id = user.vk_id
    
    if payload:
        candidate_id = payload.get('candidate_id')
    elif candidate_id is None:
        candidate_id = get_last_candidate_id(db, user_id)
    
    if not candidate_id:
        send_msg(vk, user_id, "Нет кандидата для добавления", get_main_keyboard())
        return
    
    if crud.viewed.add_to_blacklist(db, user_id, candidate_id):
        send_msg(vk, user_id, "⛔ Добавлено в черный список!", get_main_keyboard())
    else:
        send_msg(vk, user_id, "⚠️ Уже в черном списке", get_main_keyboard())


def handle_show_blacklist(db, vk, user, send_msg_func=None):
    """Показать черный список"""
    user_id = user.vk_id
    msg_func = send_msg_func or send_msg
    
    blacklist = crud.viewed.get_user_blacklist(db, user_id)
    
    if not blacklist:
        msg_func(vk, user_id, "📭 Черный список пуст", get_main_keyboard())
        return
    
    from app.database.models import User
    
    message = "⛔ Ваш черный список:\n\n"
    for i, blocked_id in enumerate(blacklist[:10], 1):
        candidate = db.get(User, blocked_id)
        if candidate:
            message += f"{i}. {candidate.first_name} {candidate.last_name}\n"
            message += f"   {candidate.profile_url}\n\n"
    
    if len(blacklist) > 10:
        message += f"... и еще {len(blacklist) - 10} анкет"
    
    msg_func(vk, user_id, message, get_main_keyboard())


# ========== НАВИГАЦИЯ ==========

def handle_next_candidate(db, vk, user, text, payload=None):
    """Переход к следующему кандидату"""
    from .search import handle_next_batch
    return handle_next_batch(db, vk, user.vk_id, user, send_msg)


def handle_show_photos(db, vk, user, text, payload=None):
    """Показать фото кандидата"""
    user_id = user.vk_id
    
    if payload:
        candidate_id = payload.get('candidate_id')
    else:
        candidate_id = get_last_candidate_id(db, user_id)
    
    if not candidate_id:
        send_msg(vk, user_id, "Нет активного кандидата", get_main_keyboard())
        return
    
    from app.database.models import User
    candidate = db.get(User, candidate_id)
    
    if candidate:
        from .search import show_candidate_photos
        show_candidate_photos(db, vk, user_id, candidate, send_msg)
    else:
        send_msg(vk, user_id, "Кандидат не найден", get_main_keyboard())