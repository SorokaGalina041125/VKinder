"""
Обработчики поиска
"""
import logging
from app.bot.search.searcher import CandidateSearcher
from app.bot.search.vk_client import InvalidUserTokenError
from app.bot.keyboards import get_main_keyboard, get_selection_keyboard
from app.database import crud
from app.bot.utils import send_msg, get_last_candidate_id, get_last_candidate
from app.config import settings

logger = logging.getLogger(__name__)

# Хранилище для ID кандидатов в очереди
pending_candidate_ids = {}  # user_id: list of candidate_ids


def _handle_invalid_user_token(vk, user_id, send_msg_func):
    send_msg_func(
        vk,
        user_id,
        "VK_USER_TOKEN недействителен или истек. Обновите пользовательский токен в `.env` и перезапустите бота.",
        get_main_keyboard()
    )


def handle_search(db, vk, user_id, current_user, send_msg_func):
    """Обработка команды поиск"""
    criteria = crud.criteria.get_criteria(db, user_id)
    
    if not criteria:
        message = "Давайте настроим поиск. Кого ты ищешь? 👫"
        crud.user.update_user_state(db, user_id, "wait_sex")
        send_msg_func(vk, user_id, message, get_selection_keyboard())
        return
    
    # Ищем в базе
    candidate = crud.user.get_next_candidate(db, user_id)
    
    if not candidate:
        send_msg_func(vk, user_id, "🔍 Ищу кандидатов...")
        
        searcher = CandidateSearcher(db, settings.VK_USER_TOKEN)
        
        try:
            candidates, remaining = searcher.search_batch(user_id, criteria, batch_size=10)
        except InvalidUserTokenError:
            _handle_invalid_user_token(vk, user_id, send_msg_func)
            return
        
        if candidates:
            pending_candidate_ids[user_id] = [c.vk_id for c in candidates[1:]]
            show_candidate_by_id(db, vk, user_id, candidates[0].vk_id, send_msg_func, len(candidates) - 1, remaining)
            return
        else:
            send_msg_func(vk, user_id, "Подходящие анкеты не найдены.", get_main_keyboard())
            return

    if candidate:
        show_candidate_by_id(db, vk, user_id, candidate.vk_id, send_msg_func, 0, 0)


def handle_next_batch(db, vk, user_id, current_user, send_msg_func):
    """Показывает следующего кандидата из очереди"""
    criteria = crud.criteria.get_criteria(db, user_id)
    
    if not criteria:
        send_msg_func(vk, user_id, "Сначала настройте поиск (кнопка 'Поиск')", get_main_keyboard())
        return
    
    if user_id in pending_candidate_ids and pending_candidate_ids[user_id]:
        next_candidate_id = pending_candidate_ids[user_id].pop(0)
        remaining = len(pending_candidate_ids[user_id])
        show_candidate_by_id(db, vk, user_id, next_candidate_id, send_msg_func, remaining, 0)
        return
    
    send_msg_func(vk, user_id, "🔄 Загружаю следующую партию...")
    
    searcher = CandidateSearcher(db, settings.VK_USER_TOKEN)
    
    try:
        candidates, remaining = searcher.search_batch(user_id, criteria, batch_size=10)
    except InvalidUserTokenError:
        _handle_invalid_user_token(vk, user_id, send_msg_func)
        return
    
    if candidates:
        pending_candidate_ids[user_id] = [c.vk_id for c in candidates[1:]]
        show_candidate_by_id(db, vk, user_id, candidates[0].vk_id, send_msg_func, len(candidates) - 1, remaining)
    else:
        send_msg_func(vk, user_id, "Кандидаты закончились. Нажмите 'Поиск' для нового поиска.", get_main_keyboard())


def show_candidate_by_id(db, vk, user_id, candidate_id, send_msg_func, remaining_in_queue, total_remaining):
    """Показ кандидата"""
    from app.database.models import User
    from app.bot.search.vk_client import VKClient
    
    candidate = db.get(User, candidate_id)
    
    if not candidate:
        send_msg_func(vk, user_id, "Кандидат не найден в базе", get_main_keyboard())
        return
    
    # Проверяем доступность профиля с использованием токена пользователя
    vk_client = VKClient(settings.VK_USER_TOKEN)
    if not vk_client.check_profile_open(candidate.vk_id):
        crud.viewed.mark_as_viewed(db, user_id, candidate.vk_id)
        send_msg_func(vk, user_id, "⚠️ Профиль кандидата закрыт, перехожу к следующему.", get_main_keyboard())
        return handle_next_batch(db, vk, user_id, None, send_msg_func)
    
    # Получаем фото
    attachments = crud.content.get_user_photos(db, candidate.vk_id)
    photos_count = len(attachments.split(',')) if attachments else 0
    
    if photos_count == 0:
        crud.viewed.mark_as_viewed(db, user_id, candidate.vk_id)
        send_msg_func(vk, user_id, "⚠️ У кандидата нет доступных фото", get_main_keyboard())
        return handle_next_batch(db, vk, user_id, None, send_msg_func)
    
    message = (
        f"👤 {candidate.first_name} {candidate.last_name}\n"
        f"🆔 ID: {candidate.vk_id}\n"
        f"🔗 Ссылка: {candidate.profile_url}\n"
        f"📸 Фото: {photos_count} шт.\n"
    )
    
    if remaining_in_queue > 0:
        message += f"📊 Осталось в очереди: {remaining_in_queue}\n"
    
    message += (
        f"\n💡 Действия:\n"
        f"   • Добавить в избранное - кнопка \"В избранное\"\n"
        f"   • Добавить в чёрный список - кнопка \"В чс\"\n"
        f"   • Посмотреть конкретное фото - напиши \"фото 1\"\n"
        f"   • Следующий кандидат - кнопка \"Следующий\""
    )
    
    send_msg_func(vk, user_id, message, get_main_keyboard(), attachment=attachments)
    crud.viewed.mark_as_viewed(db, user_id, candidate.vk_id)


def show_candidate_photos(db, vk, user_id, candidate, send_msg_func):
    """
    Показать все фото кандидата с возможностью лайка.
    Вызывается из interactions.py при нажатии на кнопку "Показать фото".
    """
    from app.bot.keyboards.photo_actions import get_photo_actions_keyboard
    
    # Получаем фото кандидата
    attachments = crud.content.get_user_photos(db, candidate.vk_id)
    
    if not attachments:
        send_msg_func(vk, user_id, "📷 У кандидата нет доступных фото", get_main_keyboard())
        return
    
    # Разбиваем строку attachment на отдельные фото
    photo_list = attachments.split(',')
    
    # Показываем первое фото с кнопками действий
    first_photo = photo_list[0]
    photo_parts = first_photo.split('_')
    photo_owner_id = int(photo_parts[0].replace('photo', ''))
    photo_id = photo_parts[1]
    
    message = (
        f"📸 Фото кандидата {candidate.first_name} {candidate.last_name}\n"
        f"Всего фото: {len(photo_list)}\n\n"
        f"💡 Нажмите на кнопки, чтобы поставить или снять лайк."
    )
    
    keyboard = get_photo_actions_keyboard(photo_owner_id, photo_id)
    send_msg_func(vk, user_id, message, keyboard, attachment=first_photo)


def handle_reset_search(db, vk, user_id, current_user, send_msg_func):
    """Сброс критериев поиска"""
    crud.criteria.reset_criteria(db, user_id)
    
    # Очищаем очередь кандидатов, чтобы избежать утечки памяти
    if user_id in pending_candidate_ids:
        del pending_candidate_ids[user_id]
    
    crud.user.update_user_state(db, user_id, "wait_sex")
    
    message = "Настройки сброшены. Кого ты ищешь? 👫"
    send_msg_func(vk, user_id, message, get_selection_keyboard())
