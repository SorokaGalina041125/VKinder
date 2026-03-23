"""
Интеграционные тесты VK API с реальным API
"""
import pytest


class TestVKClient:
    """Тесты VKClient с реальным API"""
    
    def test_check_profile_open(self, real_vk_api):
        """Тест: проверка открытого профиля"""
        is_open = real_vk_api.check_profile_open(1)
        assert isinstance(is_open, bool)
    
    def test_check_profile_closed(self, real_vk_api, closed_profile_vk_id):
        """Тест: проверка закрытого профиля"""
        # Проверяем, что профиль закрыт (ID 33556489)
        is_open = real_vk_api.check_profile_open(closed_profile_vk_id)
        assert is_open == False, f"Профиль {closed_profile_vk_id} должен быть закрыт"
    
    def test_get_city_id(self, real_vk_api):
        """Тест: получение ID города"""
        city_id = real_vk_api.get_city_id("Москва")
        assert city_id is not None
        assert isinstance(city_id, int)
        
        # Проверка кэша
        city_id_cached = real_vk_api.get_city_id("Москва")
        assert city_id == city_id_cached
    
    def test_get_photos(self, real_vk_api):
        """Тест: получение фото пользователя"""
        photos = real_vk_api.get_photos(1)
        assert isinstance(photos, list)
    
    def test_search_bulk(self, real_vk_api):
        """Тест: массовый поиск через execute"""
        params = {
            'sex': 1,
            'age_from': 20,
            'age_to': 30,
            'has_photo': 1
        }
        
        results = real_vk_api.search_bulk(params, limit=100)
        assert isinstance(results, list)
        assert len(results) <= 100
    
    def test_add_like_public_photo(self, real_vk_api):
        """Тест: добавление лайка на публичное фото"""
        result = real_vk_api.add_like(1, "456239000")
        assert isinstance(result, bool)


class TestVKApiSearch:
    """Тесты поиска через VK API"""
    
    def test_search_users_basic(self, real_vk_api):
        """Тест: базовый поиск пользователей"""
        result = real_vk_api.users_search(
            sex=1,
            age_from=20,
            age_to=30,
            count=10,
            fields='domain, bdate, city, sex'
        )
        
        assert result is not None
        assert 'items' in result
        assert isinstance(result['items'], list)
    
    def test_search_with_city(self, real_vk_api):
        """Тест: поиск с фильтром по городу"""
        city_id = real_vk_api.get_city_id("Москва")
        
        result = real_vk_api.users_search(
            sex=1,
            age_from=20,
            age_to=30,
            city=city_id,
            count=10,
            fields='domain, bdate, city, sex'
        )
        
        assert result is not None
        assert 'items' in result
    
    def test_get_user_info(self, real_vk_api):
        """Тест: получение информации о пользователе"""
        users = real_vk_api.users_get([1], 'domain, bdate, city, sex')
        
        assert len(users) == 1
        assert 'id' in users[0]
        assert 'first_name' in users[0]