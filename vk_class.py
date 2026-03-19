import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
## ГОРОД НАДО ДОБАВИТЬ

class VK:
    def __init__(self, access_token=None, user_id=None, version='5.199'):
        self.token = access_token or os.getenv('VK_GROUP_TOKEN')
        if not self.token:
            raise ValueError(
                "Токен доступа не найден. Укажите его в параметре access_token или в переменной окружения VK_GROUP_TOKEN")

        self.raw_id = user_id  # исходный ID (может быть числом или строкой с буквами)
        self.id = None  # числовой ID, который получим после запроса
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

        self.user_name = None
        self.user_profile_link = None
        self.user_sex = None
        self.user_age = None
        self.user_bdate_raw = None
        self.user_photos_attachment = None

    @staticmethod
    def _calculate_age(bdate_str):
        try:
            parts = bdate_str.split('.')
            if len(parts) == 3:
                birth_date = datetime.strptime(bdate_str, '%d.%m.%Y')
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return age
        except (ValueError, AttributeError):
            return None
        return None

    def users_info(self):
        """
        Получает информацию о пользователе.
        Если self.raw_id не задан, возвращает данные владельца токена.
        Выводит тип переданного ID (числовой или буквенный) и результат.
        """
        url = 'https://api.vk.com/method/users.get'
        params = {'fields': 'sex,bdate'}

        # Проверяем, передан ли ID
        if self.raw_id:
            # Определяем тип: если строка состоит только из цифр, то числовой, иначе буквенный
            id_type = 'числовой' if str(self.raw_id).isdigit() else 'буквенный (screen name)'
            print(f"🔍 Передан ID: {self.raw_id} (тип: {id_type})")
            params['user_ids'] = self.raw_id
        else:
            print("🔍 ID не передан, получаем информацию о владельце токена.")

        response = requests.get(url, params={**self.params, **params})
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            raise Exception(f"VK API error: {data['error'].get('error_msg', 'Неизвестная ошибка')}")

        if 'response' not in data or not data['response']:
            raise Exception("VK API вернул пустой ответ. Проверьте токен или ID.")

        user_data = data['response'][0]
        self.id = user_data['id']  # теперь у нас числовой ID
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

        # Вывод информации о пользователе
        print("\n📌 Информация о пользователе:")
        print(f"   Имя: {self.user_name}")
        print(f"   Числовой ID: {self.id}")
        print(f"   Ссылка: {self.user_profile_link}")
        print(f"   Пол: {self.user_sex}")
        if self.user_age:
            print(f"   Возраст: {self.user_age}")
        else:
            print(f"   Возраст: не определён (год рождения скрыт или не указан)")
        if self.user_bdate_raw:
            print(f"   Дата рождения (исходная): {self.user_bdate_raw}")

        return self.user_profile_link

    def get_user_photos(self, count=3):
        """Получает фотографии профиля и формирует attachment."""
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
    # Пример 1: без указания ID (владелец токена)
    print("=== Тест 1: без ID ===")
    vk1 = VK()
    try:
        vk1.users_info()
        attachment = vk1.get_user_photos(3)
        print(f"Attachment для фото: {attachment if attachment else 'нет фото'}")
    except Exception as e:
        print(f"Ошибка: {e}")

    print("\n=== Тест 2: с числовым ID ===")
    vk2 = VK(user_id='123456789')  # замените на реальный ID
    try:
        vk2.users_info()
        attachment = vk2.get_user_photos(3)
        print(f"Attachment для фото: {attachment if attachment else 'нет фото'}")
    except Exception as e:
        print(f"Ошибка: {e}")

    print("\n=== Тест 3: с буквенным screen name ===")
    vk3 = VK(user_id='durov')  # screen name Павла Дурова
    try:
        vk3.users_info()
        attachment = vk3.get_user_photos(3)
        print(f"Attachment для фото: {attachment if attachment else 'нет фото'}")
    except Exception as e:
        print(f"Ошибка: {e}")