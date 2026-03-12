# Инициализация клиента
vk = VKClient()

# Получение информации о текущем пользователе
current_user = vk.get_user_info()
print(f"Текущий пользователь: {current_user['first_name']}")

# Поиск пользователей
criteria = {
    'age_from': 25,
    'age_to': 35,
    'sex': 1,  # Женский
    'city': 'Москва',
    'has_photos': True
}
users = vk.search_users_batch(criteria, total_needed=500)

# Для каждого найденного пользователя
for user in users[:10]:
    # Получаем лучшие фото
    top_photos = vk.get_top_photos(user['id'], count=3)
    
    # Форматируем сообщение
    message, attachments = vk.format_user_info_message(user, top_photos)
    
    # Отправляем сообщение
    vk.send_message_with_photos(
        user_id=current_user['id'],
        text=message,
        photo_attachments=attachments
    )
    
    # Ставим лайк первому фото
    if top_photos:
        vk.like_photo(top_photos[0]['owner_id'], top_photos[0]['id'])
    
    time.sleep(1)  # Пауза между пользователями

# Закрываем соединение
vk.close()