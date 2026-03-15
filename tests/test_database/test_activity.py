import pytest
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError
from psycopg.errors import ForeignKeyViolation

from app.database.models.user import User
from app.database.models.activity import UserActivity


class TestUserActivityModel:
    """Тесты для модели UserActivity"""

    def test_create_search_activity(self, session, clean_db, test_user):
        """Тест создания активности поиска"""
        search_params = {
            "age_from": 20,
            "age_to": 30,
            "city": "Москва",
            "sex": 2,
            "has_photos": True,
            "relation_status": "single"
        }
        
        activity = UserActivity(
            user_vk_id=test_user.vk_id,
            activity_type="search",
            search_params=search_params,
            results_count=100
        )
        
        session.add(activity)
        session.commit()
        session.refresh(activity)
        
        assert activity.user_vk_id == test_user.vk_id
        assert activity.activity_type == "search"
        assert activity.search_params == search_params
        assert activity.results_count == 100
        assert activity.target_id is None
        assert isinstance(activity.created_at, datetime)

    def test_create_view_activity(self, session, clean_db, test_user):
        """Тест создания активности просмотра"""
        activity = UserActivity(
            user_vk_id=test_user.vk_id,
            activity_type="view",
            target_id="789012"
        )
        
        session.add(activity)
        session.commit()
        session.refresh(activity)
        
        assert activity.target_id == "789012"
        assert activity.search_params is None
        assert activity.results_count is None

    def test_create_favorite_activity(self, session, clean_db, test_user):
        """Тест создания активности добавления в избранное"""
        activity = UserActivity(
            user_vk_id=test_user.vk_id,
            activity_type="favorite",
            target_id="456789"
        )
        
        session.add(activity)
        session.commit()
        session.refresh(activity)
        
        assert activity.target_id == "456789"

    def test_create_blacklist_activity(self, session, clean_db, test_user):
        """Тест создания активности добавления в черный список"""
        activity = UserActivity(
            user_vk_id=test_user.vk_id,
            activity_type="blacklist",
            target_id="654321"
        )
        
        session.add(activity)
        session.commit()
        session.refresh(activity)
        
        assert activity.target_id == "654321"

    def test_create_like_photo_activity(self, session, clean_db, test_user):
        """Тест создания активности лайка фотографии"""
        activity = UserActivity(
            user_vk_id=test_user.vk_id,
            activity_type="like_photo",
            target_id="photo_123456_789"
        )
        
        session.add(activity)
        session.commit()
        session.refresh(activity)
        
        assert activity.target_id == "photo_123456_789"

    def test_get_user_activities(self, session, clean_db, test_user):
        """Тест получения всех активностей пользователя"""
        activities = [
            UserActivity(user_vk_id=test_user.vk_id, activity_type="search", results_count=50),
            UserActivity(user_vk_id=test_user.vk_id, activity_type="view", target_id="111"),
            UserActivity(user_vk_id=test_user.vk_id, activity_type="favorite", target_id="222"),
            UserActivity(user_vk_id=test_user.vk_id, activity_type="like_photo", target_id="photo_333"),
        ]
        
        session.add_all(activities)
        session.commit()
        
        user_activities = session.query(UserActivity).filter_by(
            user_vk_id=test_user.vk_id
        ).order_by(UserActivity.created_at).all()
        
        assert len(user_activities) == 4
        activity_types = [a.activity_type for a in user_activities]
        assert "search" in activity_types
        assert "view" in activity_types
        assert "favorite" in activity_types
        assert "like_photo" in activity_types

    def test_filter_activities_by_type(self, session, clean_db, test_user):
        """Тест фильтрации активностей по типу"""
        activities = [
            UserActivity(user_vk_id=test_user.vk_id, activity_type="search"),
            UserActivity(user_vk_id=test_user.vk_id, activity_type="search"),
            UserActivity(user_vk_id=test_user.vk_id, activity_type="view"),
            UserActivity(user_vk_id=test_user.vk_id, activity_type="favorite"),
        ]
        
        session.add_all(activities)
        session.commit()
        
        search_activities = session.query(UserActivity).filter_by(
            user_vk_id=test_user.vk_id,
            activity_type="search"
        ).all()
        
        assert len(search_activities) == 2

    def test_activity_repr(self, session, clean_db, test_user):
        """Тест строкового представления"""
        activity = UserActivity(
            user_vk_id=test_user.vk_id,
            activity_type="search"
        )
        
        expected_repr = f"<UserActivity(user={test_user.vk_id}, type='search')>"
        assert repr(activity) == expected_repr

    def test_foreign_key_constraint(self, session, clean_db):
        """Тест внешнего ключа - нельзя добавить активность с несуществующим пользователем"""
        activity = UserActivity(
            user_vk_id=99999,
            activity_type="search"
        )
        
        session.add(activity)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, ForeignKeyViolation)
        session.rollback()

    def test_json_serialization_complex(self, session, clean_db, test_user):
        """Тест сериализации сложного JSON поля search_params"""
        complex_params = {
            "age_from": 18,
            "age_to": 35,
            "city": "Санкт-Петербург",
            "interests": ["музыка", "спорт", "книги"],
            "relation_status": ["single", "actively searching"],
            "has_photos": True,
            "nested": {
                "key1": "value1",
                "key2": [1, 2, 3]
            }
        }
        
        activity = UserActivity(
            user_vk_id=test_user.vk_id,
            activity_type="search",
            search_params=complex_params,
            results_count=150
        )
        
        session.add(activity)
        session.commit()
        session.refresh(activity)
        
        assert activity.search_params == complex_params
        assert activity.search_params["interests"] == ["музыка", "спорт", "книги"]
        assert activity.search_params["nested"]["key2"] == [1, 2, 3]

    def test_activity_timestamps(self, session, clean_db, test_user):
        """Тест автоматической установки временной метки"""
        activity = UserActivity(
            user_vk_id=test_user.vk_id,
            activity_type="search"
        )
        
        # Получаем текущее время до операции
        before = datetime.now()
        
        session.add(activity)
        session.commit()
        session.refresh(activity)
        
        # Получаем текущее время после операции
        after = datetime.now()
        
        assert activity.created_at is not None
        assert isinstance(activity.created_at, datetime)
        
        # Проверяем, что created_at установлено и находится в разумных пределах
        # (между before и after с учетом небольшой погрешности)
        assert activity.created_at >= before - timedelta(seconds=1)
        assert activity.created_at <= after + timedelta(seconds=1)
        
        # Дополнительная проверка: разница не более 5 секунд
        time_diff = after - activity.created_at
        assert time_diff.total_seconds() < 5