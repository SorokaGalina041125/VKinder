from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_selection_keyboard():
    """Клавиатура для выбора пола"""
    keyboard = VkKeyboard(one_time=True)
    
    # Первая строка - выбор пола
    keyboard.add_button("Мужчин", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Женщин", color=VkKeyboardColor.POSITIVE)
    
    # Вторая строка - назад
    keyboard.add_line()
    keyboard.add_button("Назад", color=VkKeyboardColor.SECONDARY)
    
    return keyboard