"""
Клавиатуры для взаимодействия с кандидатами (с payload)
"""
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_interaction_keyboard(candidate_id: int, is_favorite: bool = False, is_blocked: bool = False) -> VkKeyboard:
    """
    Клавиатура для взаимодействия с кандидатом.
    Использует payload для действий.
    """
    keyboard = VkKeyboard(one_time=False)
    
    # Кнопки действий
    if not is_favorite:
        keyboard.add_button(
            label="⭐ В избранное",
            color=VkKeyboardColor.PRIMARY,
            payload={"type": "add_favorite", "candidate_id": candidate_id}
        )
    
    if not is_blocked:
        keyboard.add_button(
            label="🚫 В чёрный список",
            color=VkKeyboardColor.NEGATIVE,
            payload={"type": "add_blacklist", "candidate_id": candidate_id}
        )
    
    keyboard.add_line()
    keyboard.add_button(
        label="➡️ Следующий",
        color=VkKeyboardColor.POSITIVE,
        payload={"type": "next_candidate"}
    )
    keyboard.add_button(
        label="📸 Показать фото",
        color=VkKeyboardColor.SECONDARY,
        payload={"type": "show_photos", "candidate_id": candidate_id}
    )
    
    return keyboard


def get_favorites_list_keyboard() -> VkKeyboard:
    """Клавиатура для списка избранных"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Показать всех", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Очистить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard


def get_blacklist_list_keyboard() -> VkKeyboard:
    """Клавиатура для списка черного списка"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Показать всех", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Очистить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard