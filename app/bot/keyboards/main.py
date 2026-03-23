from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_main_keyboard():
    """Главное меню бота"""
    keyboard = VkKeyboard(one_time=False)
    
    # Первая строка - поиск и навигация
    keyboard.add_button("🔍 Поиск", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("➡️ Следующий", color=VkKeyboardColor.POSITIVE)
    
    # Вторая строка - действия с текущим кандидатом
    keyboard.add_line()
    keyboard.add_button("⭐ В избранное", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🚫 В чёрный список", color=VkKeyboardColor.NEGATIVE)
    
    # Третья строка - просмотр списков
    keyboard.add_line()
    keyboard.add_button("📋 Избранное", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("⛔ Чёрный список", color=VkKeyboardColor.SECONDARY)
    
    # Четвёртая строка - настройки поиска
    keyboard.add_line()
    keyboard.add_button("🔄 Новый поиск", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("✏️ Изменить критерии", color=VkKeyboardColor.SECONDARY)
    
    return keyboard