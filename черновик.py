import os
import requests
from dotenv import load_dotenv

from logger import logger

load_dotenv()


class VK:
    def __init__(self, access_token=None, user_id=None, version='5.199'):
        self.token = access_token or os.getenv('VK_GROUP_TOKEN')
        self.id = user_id        # ID пользователя надо сделать чтоб брал откудато, по дефолту берет токен и возвращает его правообладателя
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}
        # Дополнительные атрибуты, которые заполнятся позже
        self.user_name = None
        self.user_profile_link = None
        self.user_photos_attachment = None  # строка для attachment
    @logger
    def users_info(self):
        """Получает имя, фамилию и ID пользователя, сохраняет их и возвращает ссылку на профиль."""
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        response.raise_for_status()  # вызовет исключение при HTTP-ошибке
        data = response.json()
        # print(f'фотки json\n {data}')
        # Проверка на ошибки API
        if 'error' in data:
            raise Exception(f"VK API error: {data['error']['error_msg']}")

        user_data = data['response'][0]
        self.id = user_data['id']
        self.user_name = f"{user_data['first_name']} {user_data['last_name']}"
        self.user_profile_link = f"https://vk.com/id{self.id}"
        return self.user_profile_link
    @logger
    def get_user_photos(self, count=3):
        """Получает указанное количество фотографий из профиля пользователя и формирует attachment."""
        if not self.id:
            raise Exception("Сначала вызовите users_info() для получения ID пользователя.")

        url = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': self.id,
            'album_id': 'profile',  # фотографии профиля
            'count': count,
            'extended': 0  # можно установить 1, если нужны лайки и т.п.
        }
        response = requests.get(url, params={**self.params, **params})
        response.raise_for_status()
        data = response.json()
        # print(f'фотки json\n {data}')

        if 'error' in data:
            raise Exception(f"VK API error: {data['error']['error_msg']}")

        photos = data['response']['items']
        if not photos:
            self.user_photos_attachment = ''
            return ''

        # Формируем attachment для трёх фото: photo{owner_id}_{id}
        attachments = []
        for photo in photos:
            owner_id = photo['owner_id']
            photo_id = photo['id']
            attachments.append(f"photo{owner_id}_{photo_id}")

        self.user_photos_attachment = ','.join(attachments)
        return self.user_photos_attachment


# Пример использования
vk = VK()  # тут должен быть токен группы 'он берется из env' и user_id="его id" указать надо

# Получаем информацию о пользователе
profile_link = vk.users_info()
print(f"Имя: {vk.user_name}")
print(f"Ссылка на профиль: {profile_link}")

# Получаем три фотографии и attachment
attachment_str = vk.get_user_photos(count=3)
print(f"Attachment для messages.send: {attachment_str}")

# Теперь вы можете использовать attachment_str в запросе к messages.send

if __name__ == '__main__':
    pass