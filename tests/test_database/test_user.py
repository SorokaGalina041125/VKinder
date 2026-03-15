import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from psycopg.errors import UniqueViolation

from app.database.models.user import User


class TestUserModel:
    """Тесты для модели User"""

    def test_create_user(self, session, clean_db):
        """Тест создания пользователя"""
        user = User(
            vk_id=123456,
            first_name="Иван",
            last_name="Иванов",
            age=25,
            city="Москва",
            sex=2,
            profile_url="https://vk.com/id123456",
            last_search_offset=0,
            is_active=True
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.vk_id == 123456
        assert user.first_name == "Иван"
        assert user.last_name == "Иванов"
        assert user.age == 25
        assert user.city == "Москва"
        assert user.sex == 2
        assert user.profile_url == "https://vk.com/id123456"
        assert user.last_search_offset == 0
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)

    def test_user_without_optional_fields(self, session, clean_db):
        """Тест создания пользователя без опциональных полей"""
        user = User(
            vk_id=789012,
            first_name="Петр",
            last_name="Петров",
            profile_url="https://vk.com/id789012"
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.vk_id == 789012
        assert user.first_name == "Петр"
        assert user.last_name == "Петров"
        assert user.profile_url == "https://vk.com/id789012"
        assert user.age is None
        assert user.city is None
        assert user.sex is None
        assert user.last_search_offset == 0
        assert user.is_active is True

    def test_user_default_values(self, session, clean_db):
        """Тест значений по умолчанию"""
        user = User(
            vk_id=345678,
            first_name="Анна",
            last_name="Смирнова",
            profile_url="https://vk.com/id345678"
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        assert user.last_search_offset == 0
        assert user.is_active is True

    def test_update_user(self, session, clean_db, test_user):
        """Тест обновления данных пользователя"""
        test_user.age = 30
        test_user.city = "Санкт-Петербург"
        test_user.sex = 1
        test_user.last_search_offset = 10
        test_user.is_active = False
        
        session.commit()
        session.refresh(test_user)
        
        assert test_user.age == 30
        assert test_user.city == "Санкт-Петербург"
        assert test_user.sex == 1
        assert test_user.last_search_offset == 10
        assert test_user.is_active is False

    def test_delete_user(self, session, clean_db, test_user):
        """Тест удаления пользователя"""
        vk_id = test_user.vk_id
        
        session.delete(test_user)
        session.commit()
        
        deleted_user = session.get(User, vk_id)
        assert deleted_user is None

    def test_user_repr(self):
        """Тест строкового представления пользователя"""
        user = User(
            vk_id=123456,
            first_name="Иван",
            last_name="Иванов",
            profile_url="https://vk.com/id123456"
        )
        
        expected_repr = "<User(vk_id=123456, name='Иван')>"
        assert repr(user) == expected_repr

    def test_query_user_by_vk_id(self, session, clean_db, test_users):
        """Тест поиска пользователя по vk_id"""
        # Ищем по vk_id
        user = session.get(User, 2)
        assert user is not None
        # Исправляем ожидаемое значение на реальные данные из фикстуры
        assert user.first_name == "Мария"
        assert user.last_name == "Иванова"
        assert user.vk_id == 2

    def test_unique_vk_id_constraint(self, session, clean_db, test_user):
        """Тест уникальности vk_id"""
        # Очищаем сессию чтобы избежать конфликта в кэше
        session.expunge_all()
        
        user2 = User(
            vk_id=test_user.vk_id,
            first_name="User2",
            last_name="Test2",
            profile_url="url2"
        )
        session.add(user2)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, UniqueViolation)
        session.rollback()

    def test_filter_active_users(self, session, clean_db):
        """Тест фильтрации активных пользователей"""
        users = [
            User(vk_id=1, first_name="Active1", last_name="Test", profile_url="url", is_active=True),
            User(vk_id=2, first_name="Active2", last_name="Test", profile_url="url", is_active=True),
            User(vk_id=3, first_name="Inactive", last_name="Test", profile_url="url", is_active=False),
        ]
        
        session.add_all(users)
        session.commit()
        
        active_users = session.query(User).filter_by(is_active=True).all()
        assert len(active_users) == 2
        assert all(user.is_active for user in active_users)
        
        inactive_users = session.query(User).filter_by(is_active=False).all()
        assert len(inactive_users) == 1
        assert inactive_users[0].first_name == "Inactive"

    def test_bulk_insert_users(self, session, clean_db):
        """Тест массовой вставки пользователей"""
        users_data = [
            {"vk_id": 1001, "first_name": "Алексей", "last_name": "Алексеев", "profile_url": "url1"},
            {"vk_id": 1002, "first_name": "Мария", "last_name": "Иванова", "profile_url": "url2"},
            {"vk_id": 1003, "first_name": "Сергей", "last_name": "Сергеев", "profile_url": "url3"},
        ]
        
        users = [User(**data) for data in users_data]
        session.add_all(users)
        session.commit()
        
        count = session.query(User).count()
        assert count == 3
        
        for data in users_data:
            user = session.get(User, data["vk_id"])
            assert user is not None
            assert user.first_name == data["first_name"]
            assert user.last_name == data["last_name"]