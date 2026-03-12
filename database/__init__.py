"""
Пакет для работы с базой данных.
Поддерживает миграции через Alembic.
"""

from .db_manager import DatabaseManager
from .migration_manager import migration_manager, MigrationManager
from .models import (
    Base, User, SearchCriteria, ViewedUser, Photo, 
    SearchLog, UserInterest, blacklist_table, favorites_table
)

# При импорте пакета проверяем миграции
def initialize_database():
    """
    Инициализация базы данных с проверкой миграций.
    Вызывается при запуске приложения.
    """
    print("🔄 Инициализация базы данных...")
    
    # Проверяем и применяем миграции
    migration_manager.ensure_database_up_to_date()
    
    # Создаем экземпляр DatabaseManager
    db_manager = DatabaseManager()
    
    return db_manager

__all__ = [
    'DatabaseManager',
    'MigrationManager',
    'migration_manager',
    'initialize_database',
    'Base',
    'User',
    'SearchCriteria',
    'ViewedUser',
    'Photo',
    'SearchLog',
    'UserInterest',
    'blacklist_table',
    'favorites_table'
]