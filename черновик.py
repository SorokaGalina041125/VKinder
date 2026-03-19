import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class VK:
    def __init__(self, access_token=None, user_id=None, version='5.199'):
        self.token = access_token or os.getenv('VK_GROUP_TOKEN')
        if not self.token:
            raise ValueError("Токен доступа не найден. Укажите его в параметре access_token или в переменной окружения VK_GROUP_TOKEN")

        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

        # Атрибуты, которые заполнятся после вызова users_info()
        self.user_name = None
        self.user_profile_link = None
        self.user_sex = None          # пол: 'мужской', 'женский' или 'не указан'
        self.user_age = None           # возраст (число) или None
        self.user_bdate_raw = None     # исходная строка даты рождения (как вернуло API)
        self.user_photos_attachment = None  # строка для attachment (фото через запятую)

    @staticmethod
    def _calculate_age(bdate_str):
        """Вычисляет возраст по дате рождения в формате D.M.YYYY."""
        try:
            parts = bdate_str.split('.')
            if len(parts) == 3:  # день.месяц.год
                birth_date = datetime.strptime(bdate_str, '%d.%m.%Y')
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return age
            else:
                return None  # год не указан
        except (ValueError, AttributeError):
            return None

    def users_info(self):
        """
        Получает информацию о пользователе: имя, пол, дату рождения.
        Если self.id не задан, возвращает данные владельца токена.
        Сохраняет имя, ID, ссылку на профиль, пол и возраст.
        :return: ссылка на профиль пользователя
        """
        url = 'https://api.vk.com/method/users.get'
        params = {'fields': 'sex,bdate'}  # запрашиваем дополнительные поля
        if self.id:
            params['user_ids'] = self.id

        response = requests.get(url, params={**self.params, **params})
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            raise Exception(f"VK API error: {data['error'].get('error_msg', 'Неизвестная ошибка')}")

        if 'response' not in data or not data['response']:
            raise Exception("VK API вернул пустой ответ. Проверьте токен и параметры запроса.")

        user_data = data['response'][0]
        self.id = user_data['id']
        self.user_name = f"{user_data['first_name']} {user_data['last_name']}"
        self.user_profile_link = f"https://vk.com/id{self.id}"

        # Обработка пола
        sex_code = user_data.get('sex', 0)
        if sex_code == 1:
            self.user_sex = 'женский'
        elif sex_code == 2:
            self.user_sex = 'мужской'
        else:
            self.user_sex = 'не указан'

        # Обработка даты рождения
        self.user_bdate_raw = user_data.get('bdate')
        if self.user_bdate_raw:
            self.user_age = self._calculate_age(self.user_bdate_raw)
        else:
            self.user_age = None

        return self.user_profile_link

    def get_user_photos(self, count=3):
        """Получает указанное количество фотографий из альбома 'profile' пользователя и формирует attachment."""
        if not self.id:
            raise Exception("Сначала вызовите users_info() для получения ID пользователя.")

        url = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': self.id,
            'album_id': 'profile',
            'count': count,
            'extended': 0
        }
        response = requests.get(url, params={**self.params, **params})
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            raise Exception(f"VK API error: {data['error'].get('error_msg', 'Неизвестная ошибка')}")

        photos = data['response'].get('items', [])
        if not photos:
            self.user_photos_attachment = ''
            return ''

        attachments = [f"photo{photo['owner_id']}_{photo['id']}" for photo in photos]
        self.user_photos_attachment = ','.join(attachments)
        return self.user_photos_attachment


# Пример использования
if __name__ == '__main__':
    vk = VK()  # токен из .env, user_id можно не указывать

    try:
        profile_link = vk.users_info()
        print(f"Имя: {vk.user_name}")
        print(f"Ссылка: {profile_link}")
        print(f"Пол: {vk.user_sex}")
        if vk.user_age:
            print(f"Возраст: {vk.user_age}")
        else:
            print("Возраст: не указан или год скрыт")
        print(f"Исходная дата рождения: {vk.user_bdate_raw}")

        attachment_str = vk.get_user_photos(count=3)
        if attachment_str:
            print(f"Attachment для фото: {attachment_str}")
        else:
            print("У пользователя нет фото в профиле.")

    except Exception as e:
        print(f"Ошибка: {e}")