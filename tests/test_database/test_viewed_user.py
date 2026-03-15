import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from psycopg.errors import NotNullViolation, ForeignKeyViolation

from app.database.models.user import User
from app.database.models.viewed_user import ViewedUser


class TestViewedUserModel:
    """Тесты для модели ViewedUser"""

    def test_create_viewed_user(self, session, clean_db, test_user, test_users):
        """Тест создания записи о просмотренном пользователе"""
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2,
            compatibility_score=85,
            age_score=90,
            city_score=100,
            interests_score=75,
            friends_score=80,
            photos_score=85
        )
        
        session.add(viewed)
        session.commit()
        session.refresh(viewed)
        
        assert viewed.id is not None
        assert viewed.user_vk_id == test_user.vk_id
        assert viewed.viewed_user_vk_id == 2
        assert viewed.compatibility_score == 85
        assert viewed.age_score == 90
        assert viewed.city_score == 100
        assert viewed.interests_score == 75
        assert viewed.friends_score == 80
        assert viewed.photos_score == 85
        assert viewed.is_favorite is False
        assert viewed.is_blocked is False
        assert isinstance(viewed.viewed_at, datetime)

    def test_create_viewed_user_with_defaults(self, session, clean_db, test_user, test_users):
        """Тест создания записи со значениями по умолчанию"""
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2
        )
        
        session.add(viewed)
        session.commit()
        session.refresh(viewed)
        
        assert viewed.compatibility_score == 0
        assert viewed.age_score == 0
        assert viewed.city_score == 0
        assert viewed.interests_score == 0
        assert viewed.friends_score == 0
        assert viewed.photos_score == 0
        assert viewed.is_favorite is False
        assert viewed.is_blocked is False

    def test_create_viewed_user_with_favorite(self, session, clean_db, test_user, test_users):
        """Тест создания записи с отметкой избранное"""
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2,
            is_favorite=True,
            compatibility_score=95
        )
        
        session.add(viewed)
        session.commit()
        session.refresh(viewed)
        
        assert viewed.is_favorite is True
        assert viewed.is_blocked is False
        assert viewed.compatibility_score == 95

    def test_create_viewed_user_with_blocked(self, session, clean_db, test_user, test_users):
        """Тест создания записи с отметкой черный список"""
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2,
            is_blocked=True,
            compatibility_score=30
        )
        
        session.add(viewed)
        session.commit()
        session.refresh(viewed)
        
        assert viewed.is_favorite is False
        assert viewed.is_blocked is True
        assert viewed.compatibility_score == 30

    def test_foreign_key_constraint(self, session, clean_db):
        """Тест внешнего ключа - нельзя добавить запись с несуществующим пользователем"""
        viewed = ViewedUser(
            user_vk_id=99999,
            viewed_user_vk_id=1
        )
        
        session.add(viewed)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, ForeignKeyViolation)
        session.rollback()

    def test_get_user_viewed_history(self, session, clean_db, test_user, test_users):
        """Тест получения истории просмотров пользователя"""
        viewed_users = [
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=2, compatibility_score=85),
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=3, compatibility_score=90),
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=4, compatibility_score=75),
        ]
        
        session.add_all(viewed_users)
        session.commit()
        
        history = session.query(ViewedUser).filter_by(
            user_vk_id=test_user.vk_id
        ).order_by(ViewedUser.viewed_at.desc()).all()
        
        assert len(history) == 3
        assert history[0].viewed_user_vk_id in [2, 3, 4]

    def test_get_favorites(self, session, clean_db, test_user, test_users):
        """Тест получения списка избранных пользователей"""
        viewed_users = [
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=2, is_favorite=True),
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=3, is_favorite=False),
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=4, is_favorite=True),
        ]
        
        session.add_all(viewed_users)
        session.commit()
        
        favorites = session.query(ViewedUser).filter_by(
            user_vk_id=test_user.vk_id,
            is_favorite=True
        ).all()
        
        assert len(favorites) == 2
        favorite_ids = [fav.viewed_user_vk_id for fav in favorites]
        assert 2 in favorite_ids
        assert 4 in favorite_ids

    def test_get_blocked(self, session, clean_db, test_user, test_users):
        """Тест получения черного списка пользователей"""
        viewed_users = [
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=2, is_blocked=True),
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=3, is_blocked=False),
            ViewedUser(user_vk_id=test_user.vk_id, viewed_user_vk_id=4, is_blocked=True),
        ]
        
        session.add_all(viewed_users)
        session.commit()
        
        blocked = session.query(ViewedUser).filter_by(
            user_vk_id=test_user.vk_id,
            is_blocked=True
        ).all()
        
        assert len(blocked) == 2
        blocked_ids = [b.viewed_user_vk_id for b in blocked]
        assert 2 in blocked_ids
        assert 4 in blocked_ids

    def test_update_viewed_user_status(self, session, clean_db, test_user, test_users):
        """Тест обновления статуса просмотренного пользователя"""
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2
        )
        
        session.add(viewed)
        session.commit()
        
        viewed.is_favorite = True
        viewed.compatibility_score = 95
        session.commit()
        session.refresh(viewed)
        
        assert viewed.is_favorite is True
        assert viewed.compatibility_score == 95
        
        viewed.is_favorite = False
        viewed.is_blocked = True
        viewed.compatibility_score = 20
        session.commit()
        session.refresh(viewed)
        
        assert viewed.is_favorite is False
        assert viewed.is_blocked is True
        assert viewed.compatibility_score == 20

    def test_delete_viewed_user(self, session, clean_db, test_user, test_users):
        """Тест удаления записи о просмотренном пользователе"""
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2
        )
        
        session.add(viewed)
        session.commit()
        
        viewed_id = viewed.id
        session.delete(viewed)
        session.commit()
        
        deleted_viewed = session.get(ViewedUser, viewed_id)
        assert deleted_viewed is None

    def test_viewed_user_repr(self, session, clean_db, test_user, test_users):
        """Тест строкового представления"""
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2
        )
        
        expected_repr = f"<ViewedUser(user={test_user.vk_id}, viewed=2)>"
        assert repr(viewed) == expected_repr

    def test_cannot_delete_user_with_viewed_history(self, session, clean_db, test_user, test_users):
        """Тест что нельзя удалить пользователя, у которого есть история просмотров (защита от потери данных)"""
        # Создаем запись о просмотре
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2
        )
        session.add(viewed)
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

        # Проверяем что пользователь и история всё еще в базе
        assert session.get(User, test_user.vk_id) is not None
        assert session.query(ViewedUser).filter_by(user_vk_id=test_user.vk_id).count() == 1

    def test_delete_viewed_history_before_user(self, session, clean_db, test_user, test_users):
        """Тест что можно удалить пользователя после удаления его истории просмотров"""
        # Создаем запись о просмотре
        viewed = ViewedUser(
            user_vk_id=test_user.vk_id,
            viewed_user_vk_id=2
        )
        session.add(viewed)
        session.commit()

        # Сначала удаляем всю историю просмотров пользователя
        session.query(ViewedUser).filter_by(user_vk_id=test_user.vk_id).delete()
        session.commit()

        # Теперь можно удалить пользователя
        user = session.get(User, test_user.vk_id)
        session.delete(user)
        session.commit()

        # Проверяем что пользователь удален
        assert session.get(User, test_user.vk_id) is None
        assert session.query(ViewedUser).filter_by(user_vk_id=test_user.vk_id).count() == 0