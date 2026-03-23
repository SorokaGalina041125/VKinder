import logging

logger = logging.getLogger(__name__)

# Кэш для городов
_city_cache = {}


def get_city_id(vk, city_name: str) -> int:
    """
    Получить ID города по названию через VK API (с кэшем)
    """
    city_lower = city_name.lower().strip()
    
    # Проверяем кэш
    if city_lower in _city_cache:
        return _city_cache[city_lower]
    
    try:
        # Ищем город через VK API
        result = vk.database.getCities(
            country_id=1,  # Россия
            q=city_name,
            count=1,
            need_all=0
        )
        
        items = result.get('items', [])
        if items:
            city_id = items[0]['id']
            _city_cache[city_lower] = city_id
            logger.info(f"Город '{city_name}' -> ID {city_id}")
            return city_id
        else:
            logger.warning(f"Город '{city_name}' не найден")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка получения ID города '{city_name}': {e}")
        return None