import pytest
from sqlalchemy.exc import IntegrityError
from psycopg.errors import NotNullViolation, ForeignKeyViolation

from app.database.models.user import User
from app.database.models.interest import UserInterest


class TestUserInterestModel:
    """Тесты для модели UserInterest"""

    def test_create_interest(self, session, clean_db, test_user):
        """Тест создания интереса пользователя"""
        interest = UserInterest(
            user_vk_id=test_user.vk_id,
            interest_type="music",
            interest_value="Rock",
            interest_source_id="123456"
        )
        
        session.add(interest)
        session.commit()
        session.refresh(interest)
        
        assert interest.id is not None
        assert interest.user_vk_id == test_user.vk_id
        assert interest.interest_type == "music"
        assert interest.interest_value == "Rock"
        assert interest.interest_source_id == "123456"

    def test_create_interest_without_source_id(self, session, clean_db, test_user):
        """Тест создания интереса без source_id"""
        interest = UserInterest(
            user_vk_id=test_user.vk_id,
            interest_type="books",
            interest_value="Фантастика"
        )
        
        session.add(interest)
        session.commit()
        session.refresh(interest)
        
        assert interest.interest_source_id is None
        assert interest.interest_type == "books"
        assert interest.interest_value == "Фантастика"

    def test_create_multiple_interests(self, session, clean_db, test_user):
        """Тест создания нескольких интересов для одного пользователя"""
        interests = [
            UserInterest(user_vk_id=test_user.vk_id, interest_type="music", interest_value="Rock"),
            UserInterest(user_vk_id=test_user.vk_id, interest_type="music", interest_value="Pop"),
            UserInterest(user_vk_id=test_user.vk_id, interest_type="books", interest_value="Фантастика"),
            UserInterest(user_vk_id=test_user.vk_id, interest_type="groups", interest_value="Программирование"),
        ]
        
        session.add_all(interests)
        session.commit()
        
        user_interests = session.query(UserInterest).filter_by(user_vk_id=test_user.vk_id).all()
        assert len(user_interests) == 4
        
        music_interests = session.query(UserInterest).filter_by(
            user_vk_id=test_user.vk_id, 
            interest_type="music"
        ).all()
        assert len(music_interests) == 2

    def test_interest_types_enum(self, session, clean_db, test_user):
        """Тест различных типов интересов"""
        valid_types = ["music", "books", "groups"]
        
        for interest_type in valid_types:
            interest = UserInterest(
                user_vk_id=test_user.vk_id,
                interest_type=interest_type,
                interest_value=f"Value for {interest_type}"
            )
            session.add(interest)
        
        session.commit()
        
        count = session.query(UserInterest).filter_by(user_vk_id=test_user.vk_id).count()
        assert count == 3

    def test_foreign_key_constraint(self, session, clean_db):
        """Тест внешнего ключа - нельзя добавить интерес с несуществующим пользователем"""
        interest = UserInterest(
            user_vk_id=99999,
            interest_type="music",
            interest_value="Rock"
        )
        
        session.add(interest)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, ForeignKeyViolation)
        session.rollback()

    def test_get_user_interests(self, session, clean_db, test_user):
        """Тест получения всех интересов пользователя"""
        interests = [
            UserInterest(user_vk_id=test_user.vk_id, interest_type="music", interest_value="Rock"),
            UserInterest(user_vk_id=test_user.vk_id, interest_type="music", interest_value="Jazz"),
            UserInterest(user_vk_id=test_user.vk_id, interest_type="books", interest_value="Science"),
        ]
        
        session.add_all(interests)
        session.commit()
        
        user_interests = session.query(UserInterest).filter_by(user_vk_id=test_user.vk_id).all()
        assert len(user_interests) == 3
        
        music_interests = session.query(UserInterest).filter_by(
            user_vk_id=test_user.vk_id,
            interest_type="music"
        ).all()
        assert len(music_interests) == 2
        assert music_interests[0].interest_value in ["Rock", "Jazz"]

    def test_delete_interest(self, session, clean_db, test_user):
        """Тест удаления интереса"""
        interest = UserInterest(
            user_vk_id=test_user.vk_id,
            interest_type="music",
            interest_value="Rock"
        )
        
        session.add(interest)
        session.commit()
        
        interest_id = interest.id
        session.delete(interest)
        session.commit()
        
        deleted_interest = session.get(UserInterest, interest_id)
        assert deleted_interest is None

    def test_update_interest(self, session, clean_db, test_user):
        """Тест обновления интереса"""
        interest = UserInterest(
            user_vk_id=test_user.vk_id,
            interest_type="music",
            interest_value="Rock"
        )
        
        session.add(interest)
        session.commit()
        
        interest.interest_value = "Metal"
        interest.interest_source_id = "789012"
        session.commit()
        session.refresh(interest)
        
        assert interest.interest_value == "Metal"
        assert interest.interest_source_id == "789012"

    def test_interest_repr(self, session, clean_db, test_user):
        """Тест строкового представления"""
        interest = UserInterest(
            user_vk_id=test_user.vk_id,
            interest_type="music",
            interest_value="Rock"
        )
        
        expected_repr = f"<UserInterest(user={test_user.vk_id}, type='music')>"
        assert repr(interest) == expected_repr

    def test_cannot_delete_user_with_interests(self, session, clean_db, test_user):
        """Тест что нельзя удалить пользователя, у которого есть интересы (защита от потери данных)"""
        # Создаем интерес
        interest = UserInterest(
            user_vk_id=test_user.vk_id,
            interest_type="music",
            interest_value="Rock"
        )
        session.add(interest)
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
        
        # Проверяем что пользователь и интерес всё еще в базе
        assert session.get(User, test_user.vk_id) is not None
        assert session.query(UserInterest).filter_by(user_vk_id=test_user.vk_id).count() == 1

    def test_delete_interests_before_user(self, session, clean_db, test_user):
        """Тест что можно удалить пользователя после удаления его интересов"""
        # Создаем интерес
        interest = UserInterest(
            user_vk_id=test_user.vk_id,
            interest_type="music",
            interest_value="Rock"
        )
        session.add(interest)
        session.commit()
        
        # Сначала удаляем все интересы пользователя
        session.query(UserInterest).filter_by(user_vk_id=test_user.vk_id).delete()
        session.commit()
        
        # Теперь можно удалить пользователя
        user = session.get(User, test_user.vk_id)
        session.delete(user)
        session.commit()
        
        # Проверяем что пользователь удален
        assert session.get(User, test_user.vk_id) is None
        assert session.query(UserInterest).filter_by(user_vk_id=test_user.vk_id).count() == 0