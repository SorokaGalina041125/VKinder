"""
Обработчики состояний FSM (включая изменение критериев)
"""
import logging
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from app.bot.keyboards import get_main_keyboard, get_selection_keyboard
from app.database import crud
from app.bot.utils import send_msg

logger = logging.getLogger(__name__)


def handle_wait_sex(db, vk, user_id, text, send_msg_func):
    """Обработка ввода пола"""
    crud.criteria.update_criteria(db, user_id, sex=1 if "жен" in text.lower() else 2)
    crud.user.update_user_state(db, user_id, "wait_age_from")
    send_msg_func(vk, user_id, "Введи минимальный возраст (например, 18):")


def handle_wait_age_from(db, vk, user_id, text, send_msg_func):
    """Обработка ввода минимального возраста"""
    if not text.isdigit():
        send_msg_func(vk, user_id, "Введите число!")
        return
    
    age = int(text)
    if age < 14 or age > 100:
        send_msg_func(vk, user_id, "Введите корректный возраст (от 14 до 100)")
        return
    
    crud.criteria.update_criteria(db, user_id, age_from=age)
    crud.user.update_user_state(db, user_id, "wait_age_to")
    send_msg_func(vk, user_id, "Введи максимальный возраст (например, 35):")


def handle_wait_age_to(db, vk, user_id, text, send_msg_func):
    """Обработка ввода максимального возраста"""
    if not text.isdigit():
        send_msg_func(vk, user_id, "Введите число!")
        return
    
    age = int(text)
    criteria = crud.criteria.get_criteria(db, user_id)
    
    if criteria and criteria.age_from and age < criteria.age_from:
        send_msg_func(vk, user_id, f"Максимальный возраст должен быть больше или равен {criteria.age_from}")
        return
    
    crud.criteria.update_criteria(db, user_id, age_to=age)
    crud.user.update_user_state(db, user_id, "wait_city")
    send_msg_func(vk, user_id, "Введи название города (или 'пропустить', если не важно):")


def handle_wait_city(db, vk, user_id, text, send_msg_func):
    """Обработка ввода города"""
    if text.lower() in ["пропустить", "пропуск"]:
        city = None
        send_msg_func(vk, user_id, "🌍 Город пропущен. Поиск будет без фильтра по городу.")
    else:
        city = text
        send_msg_func(vk, user_id, f"🌍 Город '{city}' сохранён.")
    
    crud.criteria.update_criteria(db, user_id, city=city)
    crud.user.update_user_state(db, user_id, "idle")
    send_msg_func(vk, user_id, "✅ Критерии сохранены! Нажми 'Поиск' для поиска анкет.", get_main_keyboard())


# ========== ИЗМЕНЕНИЕ КРИТЕРИЕВ ==========

def handle_change_criteria_menu(vk, user_id, send_msg_func):
    """Меню выбора критерия для изменения"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("👤 Сменить пол", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📅 Сменить возраст", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🌍 Сменить город", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🔄 Полный сброс", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("🔙 Назад", color=VkKeyboardColor.SECONDARY)
    
    send_msg_func(vk, user_id, "✏️ Что хочешь изменить?", keyboard)


def handle_change_sex(db, vk, user_id, text, send_msg_func):
    """Изменение только пола"""
    crud.criteria.update_criteria(db, user_id, sex=1 if "жен" in text.lower() else 2)
    crud.user.update_user_state(db, user_id, "idle")
    send_msg_func(vk, user_id, "✅ Пол изменён. Нажми 'Поиск' для поиска.", get_main_keyboard())


def handle_change_age(db, vk, user_id, text, send_msg_func):
    """Изменение возраста - запрос минимального"""
    if not text.isdigit():
        send_msg_func(vk, user_id, "Введите число!")
        return
    
    age_from = int(text)
    if age_from < 14 or age_from > 100:
        send_msg_func(vk, user_id, "Введите корректный возраст (от 14 до 100)")
        return
    
    crud.criteria.update_criteria(db, user_id, age_from=age_from)
    crud.user.update_user_state(db, user_id, "change_age_to")
    send_msg_func(vk, user_id, "Введи новый максимальный возраст:")


def handle_change_age_to(db, vk, user_id, text, send_msg_func):
    """Изменение максимального возраста"""
    if not text.isdigit():
        send_msg_func(vk, user_id, "Введите число!")
        return
    
    age_to = int(text)
    criteria = crud.criteria.get_criteria(db, user_id)
    
    if criteria and criteria.age_from and age_to < criteria.age_from:
        send_msg_func(vk, user_id, f"Максимальный возраст должен быть больше или равен {criteria.age_from}")
        return
    
    crud.criteria.update_criteria(db, user_id, age_to=age_to)
    crud.user.update_user_state(db, user_id, "idle")
    send_msg_func(vk, user_id, "✅ Возраст изменён. Нажми 'Поиск' для поиска.", get_main_keyboard())


def handle_change_city(db, vk, user_id, text, send_msg_func):
    """Изменение города"""
    if text.lower() in ["пропустить", "пропуск"]:
        city = None
        send_msg_func(vk, user_id, "🌍 Город удалён из фильтров.")
    else:
        city = text
        send_msg_func(vk, user_id, f"🌍 Город изменён на '{city}'.")
    
    crud.criteria.update_criteria(db, user_id, city=city)
    crud.user.update_user_state(db, user_id, "idle")
    send_msg_func(vk, user_id, "✅ Критерии обновлены! Нажми 'Поиск' для поиска.", get_main_keyboard())