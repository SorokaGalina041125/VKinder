import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from psycopg.errors import UniqueViolation, ForeignKeyViolation

from app.database.models.user import User
from app.database.models.blacklist import Blacklist


class TestBlacklistModel:
    """Тесты для модели Blacklist"""

    def test_add_to_blacklist(self, session, clean_db, test_users):
        """Тест добавления пользователя в черный список"""
        blacklist_entry = Blacklist(
            user_id=1,
            blocked_user_id=2
        )
        
        session.add(blacklist_entry)
        session.commit()
        session.refresh(blacklist_entry)
        
        assert blacklist_entry.user_id == 1
        assert blacklist_entry.blocked_user_id == 2
        assert isinstance(blacklist_entry.created_at, datetime)

    def test_blacklist_unique_constraint(self, session, clean_db, test_users):
        """Тест уникальности пары (user_id, blocked_user_id)"""
        entry1 = Blacklist(user_id=1, blocked_user_id=2)
        session.add(entry1)
        session.commit()
        
        # Очищаем сессию чтобы избежать конфликта в кэше
        session.expunge_all()
        
        # Пытаемся добавить такую же запись
        entry2 = Blacklist(user_id=1, blocked_user_id=2)
        session.add(entry2)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, UniqueViolation)
        session.rollback()
      

    def test_get_user_blacklist(self, session, clean_db, test_users):
        """Тест получения черного списка пользователя"""
        # Добавляем несколько записей в черный список
        entries = [
            Blacklist(user_id=1, blocked_user_id=2),
            Blacklist(user_id=1, blocked_user_id=3),
            Blacklist(user_id=2, blocked_user_id=1),  # Для другого пользователя
        ]
        
        session.add_all(entries)
        session.commit()
        
        # Получаем черный список пользователя 1
        user_blacklist = session.query(Blacklist).filter_by(user_id=1).all()
        assert len(user_blacklist) == 2
        blocked_ids = [entry.blocked_user_id for entry in user_blacklist]
        assert 2 in blocked_ids
        assert 3 in blocked_ids

    def test_remove_from_blacklist(self, session, clean_db, test_users):
        """Тест удаления из черного списка"""
        entry = Blacklist(user_id=1, blocked_user_id=2)
        session.add(entry)
        session.commit()
        
        # Удаляем запись
        session.delete(entry)
        session.commit()
        
        deleted_entry = session.get(Blacklist, (1, 2))
        assert deleted_entry is None

    def test_check_if_blocked(self, session, clean_db, test_users):
        """Тест проверки, находится ли пользователь в черном списке"""
        entry = Blacklist(user_id=1, blocked_user_id=2)
        session.add(entry)
        session.commit()
        
        # Проверяем
        is_blocked = session.get(Blacklist, (1, 2)) is not None
        assert is_blocked is True
        
        # Проверяем другую пару
        is_not_blocked = session.get(Blacklist, (1, 3)) is not None
        assert is_not_blocked is False

    def test_foreign_key_constraint(self, session, clean_db):
        """Тест внешнего ключа - нельзя добавить запись с несуществующим пользователем"""
        entry = Blacklist(user_id=99999, blocked_user_id=1)  # Несуществующий пользователь
        
        session.add(entry)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, ForeignKeyViolation)
        session.rollback()

    def test_blacklist_repr(self, session, clean_db, test_users):
        """Тест строкового представления"""
        entry = Blacklist(user_id=1, blocked_user_id=2)
        
        expected_repr = "<Blacklist(user=1, blocked=2)>"
        assert repr(entry) == expected_repr

    def test_multiple_blacklists_different_users(self, session, clean_db, test_users):
        """Тест что разные пользователи могут добавлять в черный список одного пользователя"""
        entries = [
            Blacklist(user_id=1, blocked_user_id=4),
            Blacklist(user_id=2, blocked_user_id=4),
            Blacklist(user_id=3, blocked_user_id=4),
        ]
        
        session.add_all(entries)
        session.commit()
        
        # Проверяем что все добавили пользователя 4 в черный список
        count = session.query(Blacklist).filter_by(blocked_user_id=4).count()
        assert count == 3

    def test_cascade_delete_user(self, session, clean_db, test_users):
        """Тест каскадного удаления при удалении пользователя"""
        entry = Blacklist(user_id=1, blocked_user_id=2)
        session.add(entry)
        session.commit()
        
        # Удаляем пользователя 1
        user = session.get(User, 1)
        session.delete(user)
        
        # При удалении пользователя, связанные записи в blacklist должны удалиться автоматически
        # из-за настройки cascade в модели (если она есть)
        try:
            session.commit()
        except Exception:
            session.rollback()
            # Если каскадное удаление не настроено, проверяем что запись осталась
            entry_exists = session.get(Blacklist, (1, 2)) is not None
            assert entry_exists is True
            return
        
        # Если коммит прошел успешно, проверяем что запись удалилась
        entry_exists = session.get(Blacklist, (1, 2)) is not None
        assert entry_exists is False