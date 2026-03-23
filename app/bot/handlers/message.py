"""
Главный обработчик сообщений с использованием роутера.
Регистрация маршрутов происходит один раз при импорте модуля.
"""
import json
import logging
from app.database import crud
from app.bot.utils import send_msg, get_last_candidate_id
from .router import router, RouteType

# Импортируем функции-обработчики
from .start import handle_start
from .search import handle_search, handle_next_batch, handle_reset_search
from .states import (
    handle_wait_sex, handle_wait_age_from, handle_wait_age_to,
    handle_wait_city, handle_change_sex, handle_change_age,
    handle_change_age_to, handle_change_city, handle_change_criteria_menu
)
from .interactions import (
    handle_like, handle_unlike, handle_add_favorite, handle_remove_favorite,
    handle_add_blacklist, handle_next_candidate, handle_show_photos,
    handle_back_to_candidate, handle_show_favorites, handle_show_blacklist
)
from .unknown import handle_unknown

logger = logging.getLogger(__name__)


# ========== РЕГИСТРАЦИЯ ТЕКСТОВЫХ КОМАНД ==========

@router.register(RouteType.TEXT, "привет", priority=10, description="Стартовая команда")
@router.register(RouteType.TEXT, "start", priority=10, description="Стартовая команда")
@router.register(RouteType.TEXT, "начать", priority=10, description="Стартовая команда")
def _start(db, vk, user, text, **kwargs):
    return handle_start(vk, user, send_msg)


@router.register(RouteType.TEXT, "поиск", priority=10, description="Команда поиска")
@router.register(RouteType.TEXT, "🔍 поиск", priority=10, description="Команда поиска")
def _search(db, vk, user, text, **kwargs):
    return handle_search(db, vk, user.vk_id, user, send_msg)


@router.register(RouteType.TEXT, "следующий", priority=10, description="Следующий кандидат")
@router.register(RouteType.TEXT, "➡️ следующий", priority=10, description="Следующий кандидат")
def _next(db, vk, user, text, **kwargs):
    return handle_next_batch(db, vk, user.vk_id, user, send_msg)


@router.register(RouteType.TEXT, "новый поиск", priority=10, description="Сброс поиска")
@router.register(RouteType.TEXT, "сброс", priority=10, description="Сброс поиска")
@router.register(RouteType.TEXT, "🔄 новый поиск", priority=10, description="Сброс поиска")
def _reset(db, vk, user, text, **kwargs):
    return handle_reset_search(db, vk, user.vk_id, user, send_msg)


@router.register(RouteType.TEXT, "изменить критерии", priority=10, description="Изменение критериев")
@router.register(RouteType.TEXT, "✏️ изменить критерии", priority=10, description="Изменение критериев")
def _change_menu(db, vk, user, text, **kwargs):
    return handle_change_criteria_menu(vk, user.vk_id, send_msg)


@router.register(RouteType.TEXT, "в избранное", priority=10, description="Добавить в избранное")
@router.register(RouteType.TEXT, "⭐ в избранное", priority=10, description="Добавить в избранное")
def _add_favorite_text(db, vk, user, text, **kwargs):
    candidate_id = get_last_candidate_id(db, user.vk_id)
    return handle_add_favorite(db, vk, user, text, candidate_id=candidate_id)


@router.register(RouteType.TEXT, "избранное", priority=10, description="Показать избранное")
@router.register(RouteType.TEXT, "моё избранное", priority=10, description="Показать избранное")
@router.register(RouteType.TEXT, "⭐ избранное", priority=10, description="Показать избранное")
def _show_favorites(db, vk, user, text, **kwargs):
    return handle_show_favorites(db, vk, user, send_msg)


@router.register(RouteType.TEXT, "в чёрный список", priority=10, description="Добавить в ЧС")
@router.register(RouteType.TEXT, "🚫 в чёрный список", priority=10, description="Добавить в ЧС")
def _add_blacklist_text(db, vk, user, text, **kwargs):
    candidate_id = get_last_candidate_id(db, user.vk_id)
    return handle_add_blacklist(db, vk, user, text, candidate_id=candidate_id)


@router.register(RouteType.TEXT, "чёрный список", priority=10, description="Показать ЧС")
@router.register(RouteType.TEXT, "черный список", priority=10, description="Показать ЧС")
@router.register(RouteType.TEXT, "🚫 чёрный список", priority=10, description="Показать ЧС")
def _show_blacklist(db, vk, user, text, **kwargs):
    return handle_show_blacklist(db, vk, user, send_msg)


@router.register(RouteType.TEXT, "назад", priority=10, description="Возврат в главное меню")
def _back(db, vk, user, text, **kwargs):
    """Обработка кнопки 'Назад' - возврат в главное меню"""
    crud.user.update_user_state(db, user.vk_id, "idle")
    return handle_start(vk, user, send_msg)


# ========== РЕГИСТРАЦИЯ СОСТОЯНИЙ (FSM) ==========

@router.register(RouteType.STATE, "wait_sex", description="Ожидание ввода пола")
def _wait_sex(db, vk, user, text, **kwargs):
    return handle_wait_sex(db, vk, user.vk_id, text, send_msg)


@router.register(RouteType.STATE, "wait_age_from", description="Ожидание минимального возраста")
def _wait_age_from(db, vk, user, text, **kwargs):
    return handle_wait_age_from(db, vk, user.vk_id, text, send_msg)


@router.register(RouteType.STATE, "wait_age_to", description="Ожидание максимального возраста")
def _wait_age_to(db, vk, user, text, **kwargs):
    return handle_wait_age_to(db, vk, user.vk_id, text, send_msg)


@router.register(RouteType.STATE, "wait_city", description="Ожидание города")
def _wait_city(db, vk, user, text, **kwargs):
    return handle_wait_city(db, vk, user.vk_id, text, send_msg)


@router.register(RouteType.STATE, "change_sex", description="Изменение пола")
def _change_sex(db, vk, user, text, **kwargs):
    return handle_change_sex(db, vk, user.vk_id, text, send_msg)


@router.register(RouteType.STATE, "change_age_from", description="Изменение возраста (от)")
def _change_age(db, vk, user, text, **kwargs):
    return handle_change_age(db, vk, user.vk_id, text, send_msg)


@router.register(RouteType.STATE, "change_age_to", description="Изменение возраста (до)")
def _change_age_to(db, vk, user, text, **kwargs):
    return handle_change_age_to(db, vk, user.vk_id, text, send_msg)


@router.register(RouteType.STATE, "change_city", description="Изменение города")
def _change_city(db, vk, user, text, **kwargs):
    return handle_change_city(db, vk, user.vk_id, text, send_msg)


# ========== РЕГИСТРАЦИЯ PAYLOAD (КНОПКИ) ==========

@router.register(RouteType.PAYLOAD, "like", description="Лайк фото")
def _like(db, vk, user, text, payload=None, **kwargs):
    return handle_like(db, vk, user, text, payload)


@router.register(RouteType.PAYLOAD, "unlike", description="Снять лайк")
def _unlike(db, vk, user, text, payload=None, **kwargs):
    return handle_unlike(db, vk, user, text, payload)


@router.register(RouteType.PAYLOAD, "back_to_candidate", description="Назад к кандидату")
def _back_to_candidate(db, vk, user, text, payload=None, **kwargs):
    return handle_back_to_candidate(db, vk, user, text, payload)


@router.register(RouteType.PAYLOAD, "add_favorite", description="Добавить в избранное")
def _add_favorite(db, vk, user, text, payload=None, **kwargs):
    return handle_add_favorite(db, vk, user, text, payload)


@router.register(RouteType.PAYLOAD, "remove_favorite", description="Удалить из избранного")
def _remove_favorite(db, vk, user, text, payload=None, **kwargs):
    return handle_remove_favorite(db, vk, user, text, payload)


@router.register(RouteType.PAYLOAD, "add_blacklist", description="Добавить в ЧС")
def _add_blacklist(db, vk, user, text, payload=None, **kwargs):
    return handle_add_blacklist(db, vk, user, text, payload)


@router.register(RouteType.PAYLOAD, "next_candidate", description="Следующий кандидат")
def _next_candidate(db, vk, user, text, payload=None, **kwargs):
    return handle_next_candidate(db, vk, user, text, payload)


@router.register(RouteType.PAYLOAD, "show_photos", description="Показать фото")
def _show_photos(db, vk, user, text, payload=None, **kwargs):
    return handle_show_photos(db, vk, user, text, payload)


# ========== ОСНОВНАЯ ТОЧКА ВХОДА ==========

def handle_message(db, vk, event):
    """
    Главный обработчик всех сообщений.
    Теперь максимально простой — только получает данные и передает роутеру.
    """
    if hasattr(event, "message") and event.message:
        user_id = event.message.get("from_id")
        text = event.message.get("text", "") or ""
        payload = event.message.get("payload")
    else:
        user_id = event.user_id
        text = event.text or ""
        payload = event.payload if hasattr(event, 'payload') else None

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = None
    
    logger.info(f"Сообщение от {user_id}: '{text[:50]}'")
    
    # Получаем или создаем пользователя
    current_user = crud.user.get_or_create_user(db, vk, vk_id=user_id)
    
    # Передаем всё роутеру. Он уже знает все маршруты.
    return router.handle(
        db=db,
        vk=vk,
        user=current_user,
        text=text,
        state=current_user.state,
        payload=payload
    )
