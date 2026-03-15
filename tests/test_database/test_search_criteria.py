import pytest
from datetime import datetime, timedelta
import time
from sqlalchemy.exc import IntegrityError
from psycopg.errors import NotNullViolation, ForeignKeyViolation

from app.database.models.user import User
from app.database.models.search_criteria import SearchCriteria


class TestSearchCriteriaModel:
    """Тесты для модели SearchCriteria"""

    def test_create_search_criteria(self, session, clean_db, test_user):
        """Тест создания критериев поиска"""
        criteria = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=18,
            age_to=35,
            city="Москва",
            sex=2,
            has_photos=True,
            relation_status="single"
        )
        
        session.add(criteria)
        session.commit()
        session.refresh(criteria)
        
        assert criteria.id is not None
        assert criteria.user_vk_id == test_user.vk_id
        assert criteria.age_from == 18
        assert criteria.age_to == 35
        assert criteria.city == "Москва"
        assert criteria.sex == 2
        assert criteria.has_photos is True
        assert criteria.relation_status == "single"
        assert isinstance(criteria.created_at, datetime)

    def test_create_criteria_with_defaults(self, session, clean_db, test_user):
        """Тест создания критериев со значениями по умолчанию"""
        criteria = SearchCriteria(
            user_vk_id=test_user.vk_id
        )
        
        session.add(criteria)
        session.commit()
        session.refresh(criteria)
        
        assert criteria.age_from is None
        assert criteria.age_to is None
        assert criteria.city is None
        assert criteria.sex is None
        assert criteria.has_photos is True
        assert criteria.relation_status is None
        assert isinstance(criteria.created_at, datetime)

    def test_create_criteria_with_partial_data(self, session, clean_db, test_user):
        """Тест создания критериев с частичными данными"""
        criteria = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=25,
            age_to=40,
            city="Санкт-Петербург"
        )
        
        session.add(criteria)
        session.commit()
        session.refresh(criteria)
        
        assert criteria.age_from == 25
        assert criteria.age_to == 40
        assert criteria.city == "Санкт-Петербург"
        assert criteria.sex is None
        assert criteria.relation_status is None

    def test_foreign_key_constraint(self, session, clean_db):
        """Тест внешнего ключа - нельзя добавить критерии с несуществующим пользователем"""
        criteria = SearchCriteria(user_vk_id=99999)
        
        session.add(criteria)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, ForeignKeyViolation)
        session.rollback()

    def test_multiple_criteria_for_user(self, session, clean_db, test_user):
        """Тест создания нескольких критериев для одного пользователя"""
        criteria1 = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=20,
            age_to=30,
            city="Москва"
        )
        
        criteria2 = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=25,
            age_to=35,
            city="Санкт-Петербург"
        )
        
        session.add_all([criteria1, criteria2])
        session.commit()
        
        user_criteria = session.query(SearchCriteria).filter_by(
            user_vk_id=test_user.vk_id
        ).all()
        
        assert len(user_criteria) == 2

    def test_get_latest_criteria(self, session, clean_db, test_user):
        """Тест получения последних критериев поиска"""
        criteria1 = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=20,
            age_to=30,
            city="Москва"
        )
        session.add(criteria1)
        session.commit()
        
        time.sleep(0.1)
        
        criteria2 = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=25,
            age_to=35,
            city="Санкт-Петербург"
        )
        session.add(criteria2)
        session.commit()
        
        latest_criteria = session.query(SearchCriteria).filter_by(
            user_vk_id=test_user.vk_id
        ).order_by(SearchCriteria.created_at.desc()).first()
        
        assert latest_criteria.age_from == 25
        assert latest_criteria.city == "Санкт-Петербург"

    def test_update_criteria(self, session, clean_db, test_user):
        """Тест обновления критериев поиска"""
        criteria = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=20,
            age_to=30,
            city="Москва"
        )
        
        session.add(criteria)
        session.commit()
        
        criteria.age_from = 25
        criteria.age_to = 40
        criteria.city = "Санкт-Петербург"
        criteria.sex = 1
        criteria.relation_status = "married"
        
        session.commit()
        session.refresh(criteria)
        
        assert criteria.age_from == 25
        assert criteria.age_to == 40
        assert criteria.city == "Санкт-Петербург"
        assert criteria.sex == 1
        assert criteria.relation_status == "married"

    def test_delete_criteria(self, session, clean_db, test_user):
        """Тест удаления критериев поиска"""
        criteria = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=20,
            age_to=30
        )
        
        session.add(criteria)
        session.commit()
        
        criteria_id = criteria.id
        session.delete(criteria)
        session.commit()
        
        deleted_criteria = session.get(SearchCriteria, criteria_id)
        assert deleted_criteria is None

    def test_search_criteria_repr(self, session, clean_db, test_user):
        """Тест строкового представления"""
        criteria = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=20,
            age_to=30
        )
        
        expected_repr = f"<SearchCriteria(user_id={test_user.vk_id}, age=20-30)>"
        assert repr(criteria) == expected_repr

    def test_cannot_delete_user_with_criteria(self, session, clean_db, test_user):
        """Тест что нельзя удалить пользователя, у которого есть критерии поиска (защита от потери данных)"""
        # Создаем критерии
        criteria = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=20,
            age_to=30
        )
        session.add(criteria)
        session.commit()

        # Пытаемся удалить пользователя
        user = session.get(User, test_user.vk_id)
        session.delete(user)

        # Должна возникнуть ошибка NOT NULL (SQLAlchemy пытается обновить внешний ключ)
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()

        # Проверяем что это ошибка NotNullViolation (а не ForeignKeyViolation)
        assert isinstance(excinfo.value.orig, NotNullViolation)
        assert "user_vk_id" in str(excinfo.value.orig).lower()

        session.rollback()

        # Проверяем что пользователь и критерии всё еще в базе
        assert session.get(User, test_user.vk_id) is not None
        assert session.query(SearchCriteria).filter_by(user_vk_id=test_user.vk_id).count() == 1

    def test_delete_criteria_before_user(self, session, clean_db, test_user):
        """Тест что можно удалить пользователя после удаления его критериев поиска"""
        # Создаем критерии
        criteria = SearchCriteria(
            user_vk_id=test_user.vk_id,
            age_from=20,
            age_to=30
        )
        session.add(criteria)
        session.commit()

        # Сначала удаляем все критерии пользователя
        session.query(SearchCriteria).filter_by(user_vk_id=test_user.vk_id).delete()
        session.commit()

        # Теперь можно удалить пользователя
        user = session.get(User, test_user.vk_id)
        session.delete(user)
        session.commit()

        # Проверяем что пользователь удален
        assert session.get(User, test_user.vk_id) is None
        assert session.query(SearchCriteria).filter_by(user_vk_id=test_user.vk_id).count() == 0