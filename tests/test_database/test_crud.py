"""
Объединенные тесты CRUD операций
"""
import pytest
from app.database.crud import user as user_crud
from app.database.crud import viewed as viewed_crud
from app.database.crud import criteria as criteria_crud
from app.database.crud import content as content_crud
from app.database.models import User, ViewedUser, Photo


class TestUserCRUD:
    """Тесты операций с пользователями"""
    
    def test_get_or_create_user(self, db_session, real_vk_api):
        """Тест: создание и получение пользователя"""
        user = user_crud.get_or_create_user(db_session, real_vk_api, 123456)
        assert user is not None
        assert user.vk_id == 123456
        assert user.is_bot_user == True
    
    def test_update_user_state(self, db_session, test_user):
        """Тест: обновление состояния"""
        user_crud.update_user_state(db_session, test_user.vk_id, "wait_age")
        db_session.refresh(test_user)
        assert test_user.state == "wait_age"
    
    def test_register_candidate(self, db_session, real_vk_api, rate_limit_sleep):
        """Тест: регистрация кандидата"""
        user_info = real_vk_api.api.users.get(
            user_ids=1,
            fields='domain, bdate, city, sex'
        )[0]
        
        candidate = user_crud.register_candidate(db_session, user_info)
        assert candidate is not None
        assert not candidate.is_bot_user


class TestViewedCRUD:
    """Тесты операций с просмотрами"""
    
    def test_mark_as_viewed(self, db_session, test_user, test_candidate):
        """Тест: отметка о просмотре"""
        result = viewed_crud.mark_as_viewed(db_session, test_user.vk_id, test_candidate.vk_id)
        assert result == True
    
    def test_add_to_favorites(self, db_session, test_user, test_candidate):
        """Тест: добавление в избранное"""
        result = viewed_crud.add_to_favorites(db_session, test_user.vk_id, test_candidate.vk_id)
        assert result == True
        
        favorites = viewed_crud.get_user_favorites(db_session, test_user.vk_id)
        assert test_candidate.vk_id in favorites
    
    def test_add_to_blacklist(self, db_session, test_user, test_candidate):
        """Тест: добавление в черный список"""
        result = viewed_crud.add_to_blacklist(db_session, test_user.vk_id, test_candidate.vk_id)
        assert result == True
        
        is_blocked = viewed_crud.is_blocked(db_session, test_user.vk_id, test_candidate.vk_id)
        assert is_blocked == True


class TestCriteriaCRUD:
    """Тесты операций с критериями поиска"""
    
    def test_update_criteria(self, db_session, test_user):
        """Тест: обновление критериев"""
        criteria = criteria_crud.update_criteria(
            db_session,
            test_user.vk_id,
            age_from=20,
            age_to=35,
            city="Москва",
            sex=1
        )
        
        assert criteria.age_from == 20
        assert criteria.age_to == 35
        assert criteria.city == "Москва"
        assert criteria.sex == 1
    
    def test_update_criteria_partial(self, db_session, test_user):
        """Тест: частичное обновление"""
        criteria_crud.update_criteria(db_session, test_user.vk_id, age_from=20)
        criteria_crud.update_criteria(db_session, test_user.vk_id, age_to=35)
        
        criteria = criteria_crud.get_criteria(db_session, test_user.vk_id)
        assert criteria.age_from == 20
        assert criteria.age_to == 35
    
    def test_reset_criteria(self, db_session, test_user):
        """Тест: сброс критериев"""
        criteria_crud.update_criteria(db_session, test_user.vk_id, age_from=20)
        criteria_crud.reset_criteria(db_session, test_user.vk_id)
        
        criteria = criteria_crud.get_criteria(db_session, test_user.vk_id)
        assert criteria is None


class TestContentCRUD:
    """Тесты операций с контентом"""
    
    def test_save_candidate_photos(self, db_session, test_candidate):
        """Тест: сохранение фото кандидата"""
        test_photos = [
            {'id': '123', 'likes': {'count': 10}, 'comments': {'count': 2}},
            {'id': '124', 'likes': {'count': 5}, 'comments': {'count': 1}}
        ]
        
        content_crud.save_candidate_photos(db_session, test_candidate.vk_id, test_photos)
        
        photos = db_session.query(Photo).filter_by(owner_id=test_candidate.vk_id).all()
        assert len(photos) == 2
    
    def test_photos_are_replaced_on_save(self, db_session, test_candidate):
        """Тест: старые фото удаляются при сохранении новых"""
        old_photos = [
            {'id': '123', 'likes': {'count': 10}, 'comments': {'count': 2}}
        ]
        content_crud.save_candidate_photos(db_session, test_candidate.vk_id, old_photos)
        
        new_photos = [
            {'id': '456', 'likes': {'count': 20}, 'comments': {'count': 5}}
        ]
        content_crud.save_candidate_photos(db_session, test_candidate.vk_id, new_photos)
        
        photos = db_session.query(Photo).filter_by(owner_id=test_candidate.vk_id).all()
        assert len(photos) == 1
        assert photos[0].photo_id == '456'
    
    def test_like_operations(self, db_session, test_user, test_candidate):
        """Тест: добавление и удаление лайков"""
        result = content_crud.add_like(db_session, test_user.vk_id, test_candidate.vk_id, "123")
        assert result == True
        
        has_liked = content_crud.has_liked(db_session, test_user.vk_id, test_candidate.vk_id, "123")
        assert has_liked == True
        
        result = content_crud.remove_like(db_session, test_user.vk_id, test_candidate.vk_id, "123")
        assert result == True
        
        has_liked = content_crud.has_liked(db_session, test_user.vk_id, test_candidate.vk_id, "123")
        assert has_liked == False


class TestGetNextCandidate:
    """Тесты получения следующего кандидата"""
    
    def test_get_next_candidate_returns_candidate(self, db_session, test_user, test_candidate, test_search_criteria):
        """Тест: получение кандидата"""
        
        test_candidate.age = 25
        test_candidate.city = "Москва"
        test_candidate.sex = 1
        db_session.commit()
        
        candidate = user_crud.get_next_candidate(db_session, test_user.vk_id)
        assert candidate is not None
        assert candidate.vk_id == test_candidate.vk_id
    
    def test_age_boundary_inclusive(self, db_session, test_user):
        """Тест: граничные значения возраста (20 и 30 должны включаться)"""
        from app.database.models import User
        from app.database.crud.criteria import update_criteria
        
        # Создаем локальные критерии для этого теста
        update_criteria(db_session, test_user.vk_id, age_from=20, age_to=30, city="Москва", sex=1)
        
        candidate_20 = User(
            vk_id=777777,
            first_name="Двадцать",
            last_name="Лет",
            age=20,
            city="Москва",
            sex=1,
            is_bot_user=False
        )
        candidate_30 = User(
            vk_id=888888,
            first_name="Тридцать",
            last_name="Лет",
            age=30,
            city="Москва",
            sex=1,
            is_bot_user=False
        )
        candidate_outside = User(
            vk_id=999999,
            first_name="Сорок",
            last_name="Лет",
            age=40,
            city="Москва",
            sex=1,
            is_bot_user=False
        )
        
        db_session.add_all([candidate_20, candidate_30, candidate_outside])
        db_session.commit()
        
        
        candidates_found = set()
        for _ in range(5):
            cand = user_crud.get_next_candidate(db_session, test_user.vk_id)
            if cand:
                candidates_found.add(cand.vk_id)
                # Отмечаем как просмотренного, чтобы не возвращался снова
                viewed_crud.mark_as_viewed(db_session, test_user.vk_id, cand.vk_id)
        
        assert 777777 in candidates_found, "Кандидат 20 лет должен быть найден"
        assert 888888 in candidates_found, "Кандидат 30 лет должен быть найден"
        assert 999999 not in candidates_found, "Кандидат 40 лет не должен быть найден"
    
    def test_city_case_insensitive(self, db_session, test_user):
        """Тест: город должен сравниваться без учета регистра"""
        from app.database.models import User
        from app.database.crud.criteria import update_criteria
        
        candidate = User(
            vk_id=555555,
            first_name="Тест",
            last_name="Города",
            age=25,
            city="Москва",
            sex=1,
            is_bot_user=False
        )
        db_session.add(candidate)
        db_session.commit()
        
        # Создаем критерии с городом в нижнем регистре
        update_criteria(db_session, test_user.vk_id, city="москва", age_from=20, age_to=30, sex=1)
        
        # Проверяем, что кандидат найден (город должен совпасть)
        found = user_crud.get_next_candidate(db_session, test_user.vk_id)
        assert found is not None
        assert found.vk_id == 555555
    
    def test_get_next_candidate_excludes_viewed(self, db_session, test_user, test_candidate, test_search_criteria):
        """Тест: исключение просмотренных кандидатов"""
        viewed_crud.mark_as_viewed(db_session, test_user.vk_id, test_candidate.vk_id)
        
        candidate = user_crud.get_next_candidate(db_session, test_user.vk_id)
        assert candidate is None
    
    def test_get_next_candidate_excludes_blacklisted(self, db_session, test_user, test_candidate, test_search_criteria):
        """Тест: исключение заблокированных кандидатов"""
        viewed_crud.add_to_blacklist(db_session, test_user.vk_id, test_candidate.vk_id)
        
        candidate = user_crud.get_next_candidate(db_session, test_user.vk_id)
        assert candidate is None