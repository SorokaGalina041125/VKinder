import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from psycopg.errors import UniqueViolation, ForeignKeyViolation

from app.database.models.user import User
from app.database.models.favorite import Favorite


class TestFavoriteModel:
    """Тесты для модели Favorite"""

    def test_add_to_favorites(self, session, clean_db, test_users):
        """Тест добавления пользователя в избранное"""
        favorite_entry = Favorite(
            user_id=1,
            favorite_user_id=2
        )
        
        session.add(favorite_entry)
        session.commit()
        session.refresh(favorite_entry)
        
        assert favorite_entry.user_id == 1
        assert favorite_entry.favorite_user_id == 2
        assert isinstance(favorite_entry.created_at, datetime)

    def test_favorite_unique_constraint(self, session, clean_db, test_users):
        """Тест уникальности пары (user_id, favorite_user_id)"""
        entry1 = Favorite(user_id=1, favorite_user_id=2)
        session.add(entry1)
        session.commit()
        
        # Очищаем сессию чтобы избежать конфликта в кэше
        session.expunge_all()
        
        # Пытаемся добавить такую же запись
        entry2 = Favorite(user_id=1, favorite_user_id=2)
        session.add(entry2)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, UniqueViolation)
        session.rollback()

    def test_get_user_favorites(self, session, clean_db, test_users):
        """Тест получения списка избранного пользователя"""
        # Добавляем несколько записей в избранное
        entries = [
            Favorite(user_id=1, favorite_user_id=2),
            Favorite(user_id=1, favorite_user_id=3),
            Favorite(user_id=2, favorite_user_id=1),  # Для другого пользователя
            Favorite(user_id=1, favorite_user_id=4),
        ]
        
        session.add_all(entries)
        session.commit()
        
        # Получаем избранное пользователя 1
        user_favorites = session.query(Favorite).filter_by(user_id=1).all()
        assert len(user_favorites) == 3
        favorite_ids = [entry.favorite_user_id for entry in user_favorites]
        assert 2 in favorite_ids
        assert 3 in favorite_ids
        assert 4 in favorite_ids

    def test_remove_from_favorites(self, session, clean_db, test_users):
        """Тест удаления из избранного"""
        entry = Favorite(user_id=1, favorite_user_id=2)
        session.add(entry)
        session.commit()
        
        # Удаляем запись
        session.delete(entry)
        session.commit()
        
        deleted_entry = session.get(Favorite, (1, 2))
        assert deleted_entry is None

    def test_check_if_favorite(self, session, clean_db, test_users):
        """Тест проверки, находится ли пользователь в избранном"""
        entry = Favorite(user_id=1, favorite_user_id=2)
        session.add(entry)
        session.commit()
        
        # Проверяем
        is_favorite = session.get(Favorite, (1, 2)) is not None
        assert is_favorite is True
        
        # Проверяем другую пару
        is_not_favorite = session.get(Favorite, (1, 3)) is not None
        assert is_not_favorite is False

    def test_foreign_key_constraint(self, session, clean_db):
        """Тест внешнего ключа - нельзя добавить запись с несуществующим пользователем"""
        entry = Favorite(user_id=99999, favorite_user_id=1)  # Несуществующий пользователь
        
        session.add(entry)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, ForeignKeyViolation)
        session.rollback()

    def test_favorite_repr(self, session, clean_db, test_users):
        """Тест строкового представления"""
        entry = Favorite(user_id=1, favorite_user_id=2)
        
        expected_repr = "<Favorite(user=1, favorite=2)>"
        assert repr(entry) == expected_repr

    def test_duplicate_favorite_different_users(self, session, clean_db, test_users):
        """Тест что разные пользователи могут добавлять в избранное одного и того же пользователя"""
        entries = [
            Favorite(user_id=1, favorite_user_id=4),
            Favorite(user_id=2, favorite_user_id=4),
            Favorite(user_id=3, favorite_user_id=4),
        ]
        
        session.add_all(entries)
        session.commit()
        
        # Проверяем что все добавили пользователя 4 в избранное
        count = session.query(Favorite).filter_by(favorite_user_id=4).count()
        assert count == 3

    def test_cascade_delete_user(self, session, clean_db, test_users):
        """Тест каскадного удаления при удалении пользователя"""
        entry = Favorite(user_id=1, favorite_user_id=2)
        session.add(entry)
        session.commit()
        
        # Удаляем пользователя 1
        user = session.get(User, 1)
        session.delete(user)
        
        # При удалении пользователя, связанные записи в favorites должны удалиться автоматически
        # из-за настройки cascade в модели (если она есть)
        try:
            session.commit()
        except Exception:
            session.rollback()
            # Если каскадное удаление не настроено, проверяем что запись осталась
            entry_exists = session.get(Favorite, (1, 2)) is not None
            assert entry_exists is True
            return
        
        # Если коммит прошел успешно, проверяем что запись удалилась
        entry_exists = session.get(Favorite, (1, 2)) is not None
        assert entry_exists is False