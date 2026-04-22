"""
Клиент для работы с VK API.
Инкапсулирует все обращения к VK, обрабатывает ошибки и rate limiting.
"""
import time
import logging
import json
from typing import Dict, List, Optional, Any
from functools import wraps

import vk_api
from vk_api.exceptions import ApiError

from app.config import settings

logger = logging.getLogger(__name__)


class InvalidUserTokenError(Exception):
    """Raised when VK user token is invalid or expired."""


def _is_user_token_error(error_code: int) -> bool:
    """
    VK API codes that indicate invalid user auth for methods requiring user token.
    5  - user authorization failed / token invalid
    27 - group token used where user token is required
    """
    return error_code in (5, 27)


def retry_on_flood(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток при Flood Control"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except ApiError as e:
                    if _is_user_token_error(e.code):
                        raise InvalidUserTokenError(
                            "VK_USER_TOKEN невалиден, истек или не является пользовательским токеном"
                        ) from e
                    if e.code == 6:  # Flood control
                        wait = delay * (2 ** attempt)
                        logger.warning(f"Flood control, waiting {wait}s...")
                        time.sleep(wait)
                    else:
                        raise
            raise Exception(f"Max retries exceeded for {func.__name__}")
        return wrapper
    return decorator


class VKClient:
    """Клиент для работы с VK API"""
    
    def __init__(self, user_token: Optional[str] = None):
        token = user_token or settings.VK_USER_TOKEN
        self.vk_session = vk_api.VkApi(token=token)
        self.api = self.vk_session.get_api()
        self._city_cache = {}  # Кэш для городов (живет все время работы)
    
    @retry_on_flood()
    def users_search(self, **params) -> Dict:
        """Поиск пользователей с автоматическим повтором при flood"""
        return self.api.users.search(**params)
    
    @retry_on_flood()
    def users_get(self, user_ids: List[int], fields: str = None) -> List[Dict]:
        """Получение информации о пользователях"""
        params = {"user_ids": ",".join(map(str, user_ids))}
        if fields:
            params["fields"] = fields
        return self.api.users.get(**params)
    
    @retry_on_flood()
    def get_photos(self, owner_id: int, album_id: str = 'profile', count: int = 10) -> List[Dict]:
        """Получение фотографий пользователя"""
        try:
            result = self.api.photos.get(
                owner_id=owner_id,
                album_id=album_id,
                extended=1,
                count=count
            )
            return result.get('items', [])
        except ApiError as e:
            if _is_user_token_error(e.code):
                raise InvalidUserTokenError(
                    "VK_USER_TOKEN невалиден, истек или не является пользовательским токеном"
                ) from e
            if e.code == 30:  # Profile is private
                logger.debug(f"Profile {owner_id} is private")
            else:
                logger.error(f"Error getting photos for {owner_id}: {e}")
            return []
    
    @retry_on_flood()
    def get_groups(self, user_id: int, count: int = 100) -> List[Dict]:
        """Получение групп пользователя"""
        try:
            result = self.api.groups.get(
                user_id=user_id,
                extended=1,
                fields='name, members_count',
                count=count
            )
            return result.get('items', [])
        except ApiError as e:
            if _is_user_token_error(e.code):
                raise InvalidUserTokenError(
                    "VK_USER_TOKEN невалиден, истек или не является пользовательским токеном"
                ) from e
            logger.error(f"Error getting groups for {user_id}: {e}")
            return []
    
    @retry_on_flood()
    def get_group_members(self, group_id: int, count: int = 1000) -> List[int]:
        """Получение участников группы"""
        try:
            result = self.api.groups.getMembers(
                group_id=group_id,
                count=count
            )
            return result.get('items', [])
        except ApiError as e:
            if _is_user_token_error(e.code):
                raise InvalidUserTokenError(
                    "VK_USER_TOKEN невалиден, истек или не является пользовательским токеном"
                ) from e
            logger.error(f"Error getting members of group {group_id}: {e}")
            return []
    
    def get_city_id(self, city_name: str) -> Optional[int]:
        """Получить ID города по названию (с кэшированием)"""
        city_lower = city_name.lower().strip()
        
        if city_lower in self._city_cache:
            return self._city_cache[city_lower]
        
        try:
            result = self.api.database.getCities(
                country_id=1,  # Россия
                q=city_name,
                count=1
            )
            
            items = result.get('items', [])
            if items:
                city_id = items[0]['id']
                self._city_cache[city_lower] = city_id
                logger.info(f"City '{city_name}' -> ID {city_id}")
                return city_id
            else:
                logger.warning(f"City '{city_name}' not found")
                return None
                
        except ApiError as e:
            if _is_user_token_error(e.code):
                raise InvalidUserTokenError(
                    "VK_USER_TOKEN невалиден, истек или не является пользовательским токеном"
                ) from e
            logger.error(f"Error getting city ID for '{city_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting city ID for '{city_name}': {e}")
            return None
    
    @retry_on_flood()
    def add_like(self, owner_id: int, item_id: int) -> bool:
        """Поставить лайк на фото"""
        try:
            self.api.likes.add(
                type='photo',
                owner_id=owner_id,
                item_id=item_id
            )
            return True
        except ApiError as e:
            if _is_user_token_error(e.code):
                raise InvalidUserTokenError(
                    "VK_USER_TOKEN невалиден, истек или не является пользовательским токеном"
                ) from e
            if e.code == 15:  # Access denied
                logger.debug(f"Access denied to like photo {owner_id}_{item_id}")
            elif e.code == 9:  # Already liked
                logger.debug(f"Already liked photo {owner_id}_{item_id}")
            else:
                logger.error(f"Error adding like: {e}")
            return False
    
    @retry_on_flood()
    def remove_like(self, owner_id: int, item_id: int) -> bool:
        """Снять лайк с фото"""
        try:
            self.api.likes.delete(
                type='photo',
                owner_id=owner_id,
                item_id=item_id
            )
            return True
        except ApiError as e:
            if _is_user_token_error(e.code):
                raise InvalidUserTokenError(
                    "VK_USER_TOKEN невалиден, истек или не является пользовательским токеном"
                ) from e
            logger.error(f"Error removing like: {e}")
            return False
    
    def execute(self, script: str) -> Any:
        """Выполнение VKScript через execute"""
        try:
            result = self.api.execute(code=script)
            logger.debug(f"Execute script executed successfully")
            return result
        except ApiError as e:
            if _is_user_token_error(e.code):
                raise InvalidUserTokenError(
                    "VK_USER_TOKEN невалиден, истек или не является пользовательским токеном"
                ) from e
            logger.error(f"Execute script error: {e}")
            return None
    
    def _escape_string(self, value: str) -> str:
        """Экранирование специальных символов для VKScript"""
        escaped = value.replace('\\', '\\\\')
        escaped = escaped.replace('"', '\\"')
        return escaped
    
    def search_bulk(self, params: dict, limit: int = 1000, start_offset: int = 0) -> List[Dict]:
        """
        Массовый поиск кандидатов через execute.
        Один вызов заменяет до 25 обычных запросов.
        """
        param_strs = []
        for key, value in params.items():
            if key == 'offset':
                continue
            if value:
                if isinstance(value, str):
                    escaped = self._escape_string(value)
                    param_strs.append(f'"{key}": "{escaped}"')
                else:
                    param_strs.append(f'"{key}": {value}')
        
        params_str = ", ".join(param_strs)
        max_offset = min(start_offset + limit, start_offset + 2500)
        
        script = f"""
        var users = [];
        var offset = {start_offset};
        var batch_size = 100;
        
        while (offset < {max_offset}) {{
            var response = API.users.search({{
                {params_str},
                "offset": offset,
                "count": batch_size
            }});
            
            var items = response.items;
            if (items.length == 0) {{
                offset = {max_offset};
            }} else {{
                users = users + items;
                offset = offset + batch_size;
            }}
        }}
        
        return users;
        """
        
        result = self.execute(script)
        return result if isinstance(result, list) else []
    
    def check_profile_open(self, user_id: int) -> bool:
        """Проверка, открыт ли профиль"""
        try:
            user = self.api.users.get(
                user_ids=user_id,
                fields='is_closed'
            )[0]
            return not user.get('is_closed', False)
        except Exception:
            return False
    
    def check_photo_available(self, owner_id: int, photo_id: str) -> bool:
        """Проверка доступности фото"""
        try:
            result = self.api.photos.getById(
                photos=f"{owner_id}_{photo_id}"
            )
            return result is not None and len(result) > 0
        except Exception:
            return False
