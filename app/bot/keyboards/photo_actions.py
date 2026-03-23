"""
Клавиатуры для действий с фото (с использованием payload)
"""
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_photo_actions_keyboard(photo_owner_id: int, photo_id: str) -> VkKeyboard:
    """
    Клавиатура для действий с фото.
    Использует payload для передачи данных без парсинга текста.
    """
    keyboard = VkKeyboard(one_time=True)
    
    keyboard.add_button(
        label="❤️ Лайк",
        color=VkKeyboardColor.PRIMARY,
        payload={
            "type": "like",
            "owner_id": photo_owner_id,
            "photo_id": photo_id
        }
    )
    
    keyboard.add_button(
        label="💔 Убрать лайк",
        color=VkKeyboardColor.NEGATIVE,
        payload={
            "type": "unlike",
            "owner_id": photo_owner_id,
            "photo_id": photo_id
        }
    )
    
    keyboard.add_line()
    keyboard.add_button(
        label="🔙 Назад к кандидату",
        color=VkKeyboardColor.SECONDARY,
        payload={"type": "back_to_candidate"}
    )
    
    return keyboard