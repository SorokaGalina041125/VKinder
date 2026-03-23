"""
Сквозные интеграционные тесты
"""
import pytest
from app.database.crud import user as user_crud
from app.database.crud import viewed as viewed_crud
from app.database.crud import content as content_crud


class TestSearchFlow:
    """Сквозные тесты сценариев поиска"""
    
    def test_full_search_flow(self, db_session, test_user, test_search_criteria, real_vk_api, rate_limit_sleep):
        """Тест: полный сценарий поиска"""
        # 1. Поиск кандидатов
        
        candidates = real_vk_api.search_bulk(
            {'sex': 1, 'age_from': 20, 'age_to': 30, 'has_photo': 1},
            limit=5
        )
        
        # Если API не вернул кандидатов, пропускаем тест
        if not candidates:
            pytest.skip("API не вернул кандидатов. Возможно, нет подходящих профилей.")
        
        assert len(candidates) > 0
        
        # 2. Сохраняем первого кандидата
        candidate_data = candidates[0]
        candidate = user_crud.register_candidate(db_session, candidate_data)
        assert candidate is not None
        
        # 3. Получаем следующего кандидата из БД
        next_candidate = user_crud.get_next_candidate(db_session, test_user.vk_id)
        # Может быть None, если нет других кандидатов
        if next_candidate is None:
            pytest.skip("Нет других кандидатов в БД для проверки")
    
    def test_favorite_flow(self, db_session, test_user, test_candidate):
        """Тест: сценарий работы с избранным"""
        # 1. Добавляем в избранное
        viewed_crud.add_to_favorites(db_session, test_user.vk_id, test_candidate.vk_id)
        
        # 2. Проверяем, что появился в избранном
        favorites = viewed_crud.get_user_favorites(db_session, test_user.vk_id)
        assert test_candidate.vk_id in favorites
        
        # 3. Удаляем из избранного
        viewed_crud.remove_from_favorites(db_session, test_user.vk_id, test_candidate.vk_id)
        
        # 4. Проверяем, что удалился
        favorites = viewed_crud.get_user_favorites(db_session, test_user.vk_id)
        assert test_candidate.vk_id not in favorites
    
    def test_like_flow(self, db_session, test_user, test_candidate):
        """Тест: сценарий работы с лайками"""
        # 1. Добавляем лайк
        content_crud.add_like(db_session, test_user.vk_id, test_candidate.vk_id, "123")
        
        # 2. Проверяем наличие
        has_liked = content_crud.has_liked(db_session, test_user.vk_id, test_candidate.vk_id, "123")
        assert has_liked == True
        
        # 3. Удаляем лайк
        content_crud.remove_like(db_session, test_user.vk_id, test_candidate.vk_id, "123")
        
        # 4. Проверяем отсутствие
        has_liked = content_crud.has_liked(db_session, test_user.vk_id, test_candidate.vk_id, "123")
        assert has_liked == False