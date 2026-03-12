"""
Модуль для управления миграциями базы данных через Alembic.
Позволяет автоматически применять миграции при запуске приложения.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from dotenv import load_dotenv

# Добавляем путь к проекту для импорта моделей
sys.path.append(str(Path(__file__).parent.parent))

from database.models import Base

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Менеджер миграций базы данных.
    Оборачивает команды Alembic для удобного использования.
    """
    
    def __init__(self):
        """Инициализация менеджера миграций"""
        self.project_root = Path(__file__).parent.parent
        self.alembic_ini_path = self.project_root / 'alembic.ini'
        self.alembic_dir = self.project_root / 'alembic'
        
        # Проверяем существование alembic.ini
        if not self.alembic_ini_path.exists():
            logger.warning(f"Файл {self.alembic_ini_path} не найден. Создайте его или инициализируйте Alembic.")
        
        # Параметры подключения к БД
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'vkinder_db')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', '')
        
        # Формируем строку подключения
        self.database_url = self._build_database_url()
        
        # Создаем конфигурацию Alembic
        self.alembic_cfg = self._create_alembic_config()
        
        # Создаем движок для проверки
        self.engine = None
        self._connect_to_database()
    
    def _build_database_url(self) -> str:
        """
        Формирование URL для подключения к БД.
        
        Returns:
            str: URL подключения
        """
        # Проверяем, не указан ли полный URL в переменных
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url
        
        # Формируем из компонентов
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    def _create_alembic_config(self) -> Optional[Config]:
        """
        Создание конфигурации Alembic.
        
        Returns:
            Config: Конфигурация Alembic или None
        """
        try:
            if not self.alembic_ini_path.exists():
                logger.error(f"Файл конфигурации не найден: {self.alembic_ini_path}")
                return None
            
            cfg = Config(str(self.alembic_ini_path))
            cfg.set_main_option('sqlalchemy.url', self.database_url)
            return cfg
            
        except Exception as e:
            logger.error(f"Ошибка при создании конфигурации Alembic: {e}")
            return None
    
    def _connect_to_database(self) -> bool:
        """
        Подключение к базе данных.
        
        Returns:
            bool: True если успешно
        """
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,  # Проверка соединения перед использованием
                pool_size=5,
                max_overflow=10
            )
            
            # Проверяем подключение
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ Успешное подключение к базе данных")
            return True
            
        except OperationalError as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            logger.info("Проверьте параметры подключения в .env файле")
            return False
            
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при подключении к БД: {e}")
            return False
    
    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """
        Создание новой миграции.
        
        Args:
            message: Описание миграции
            autogenerate: Автоматически генерировать из моделей
            
        Returns:
            bool: True если успешно
        """
        if not self.alembic_cfg:
            logger.error("Alembic не настроен")
            return False
        
        try:
            # Проверяем, инициализирован ли Alembic
            if not self.alembic_dir.exists():
                logger.warning("Alembic не инициализирован. Сначала выполните init_alembic()")
                return False
            
            # Создаем миграцию
            if autogenerate:
                logger.info(f"Создание автоматической миграции: {message}")
                command.revision(
                    self.alembic_cfg,
                    message=message,
                    autogenerate=True
                )
            else:
                logger.info(f"Создание пустой миграции: {message}")
                command.revision(
                    self.alembic_cfg,
                    message=message,
                    autogenerate=False
                )
            
            # Получаем путь к созданной миграции
            script = ScriptDirectory.from_config(self.alembic_cfg)
            head = script.get_current_head()
            
            logger.info(f"✅ Миграция создана: {message} (версия: {head})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при создании миграции: {e}")
            return False
    
    def upgrade(self, revision: str = "head") -> Tuple[bool, str]:
        """
        Применение миграций до указанной версии.
        
        Args:
            revision: Версия (по умолчанию head - последняя)
            
        Returns:
            Tuple[bool, str]: (Успех, Сообщение)
        """
        if not self.alembic_cfg:
            return False, "Alembic не настроен"
        
        try:
            # Получаем текущую версию до обновления
            current_before = self.get_current_revision()
            
            # Применяем миграции
            logger.info(f"Применение миграций до версии {revision}...")
            command.upgrade(self.alembic_cfg, revision)
            
            # Получаем версию после обновления
            current_after = self.get_current_revision()
            
            if current_before != current_after:
                logger.info(f"✅ Миграции применены: {current_before} -> {current_after}")
                return True, f"Миграции применены: {current_before} -> {current_after}"
            else:
                logger.info("✅ База данных уже в актуальном состоянии")
                return True, "База данных уже в актуальном состоянии"
            
        except Exception as e:
            logger.error(f"❌ Ошибка при применении миграций: {e}")
            return False, str(e)
    
    def downgrade(self, revision: str = "-1") -> Tuple[bool, str]:
        """
        Откат миграций.
        
        Args:
            revision: Версия для отката (-1 - на одну назад, base - до начала)
            
        Returns:
            Tuple[bool, str]: (Успех, Сообщение)
        """
        if not self.alembic_cfg:
            return False, "Alembic не настроен"
        
        try:
            # Получаем текущую версию
            current = self.get_current_revision()
            
            logger.info(f"Откат миграций до версии {revision}...")
            command.downgrade(self.alembic_cfg, revision)
            
            # Получаем версию после отката
            new_current = self.get_current_revision()
            
            logger.info(f"✅ Миграции откачены: {current} -> {new_current}")
            return True, f"Миграции откачены: {current} -> {new_current}"
            
        except Exception as e:
            logger.error(f"❌ Ошибка при откате миграций: {e}")
            return False, str(e)
    
    def show_history(self, verbose: bool = False) -> None:
        """
        Показать историю миграций.
        
        Args:
            verbose: Подробный вывод
        """
        if not self.alembic_cfg:
            logger.error("Alembic не настроен")
            return
        
        try:
            if verbose:
                command.history(self.alembic_cfg, verbose=True)
            else:
                command.history(self.alembic_cfg)
        except Exception as e:
            logger.error(f"❌ Ошибка при получении истории: {e}")
    
    def get_current_revision(self) -> Optional[str]:
        """
        Получение текущей версии базы данных.
        
        Returns:
            str: Текущая версия или None
        """
        if not self.engine:
            return None
        
        try:
            with self.engine.connect() as conn:
                context = MigrationContext.configure(conn)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"❌ Ошибка при получении текущей версии: {e}")
            return None
    
    def check_for_changes(self) -> Tuple[bool, list]:
        """
        Проверка наличия изменений в моделях по сравнению с БД.
        
        Returns:
            Tuple[bool, list]: (Есть изменения, Список изменений)
        """
        if not self.engine or not self.alembic_cfg:
            return False, []
        
        try:
            # Получаем текущую схему БД
            inspector = inspect(self.engine)
            existing_tables = set(inspector.get_table_names())
            
            # Получаем ожидаемые таблицы из моделей
            model_tables = set(Base.metadata.tables.keys())
            
            changes = []
            
            # Проверяем отсутствующие таблицы
            missing_tables = model_tables - existing_tables
            if missing_tables:
                changes.append(f"Отсутствуют таблицы: {', '.join(missing_tables)}")
            
            # Проверяем лишние таблицы (не из моделей)
            extra_tables = existing_tables - model_tables
            if extra_tables:
                changes.append(f"Лишние таблицы: {', '.join(extra_tables)}")
            
            # Для существующих таблиц проверяем колонки
            for table_name in model_tables & existing_tables:
                model_columns = set(Base.metadata.tables[table_name].columns.keys())
                db_columns = set(col['name'] for col in inspector.get_columns(table_name))
                
                missing_cols = model_columns - db_columns
                if missing_cols:
                    changes.append(f"В таблице {table_name} отсутствуют колонки: {', '.join(missing_cols)}")
                
                extra_cols = db_columns - model_columns
                if extra_cols:
                    changes.append(f"В таблице {table_name} лишние колонки: {', '.join(extra_cols)}")
            
            has_changes = len(changes) > 0
            
            if has_changes:
                logger.warning("⚠️ Обнаружены изменения в структуре БД:")
                for change in changes:
                    logger.warning(f"  • {change}")
            else:
                logger.info("✅ Структура БД соответствует моделям")
            
            return has_changes, changes
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке изменений: {e}")
            return True, [f"Ошибка проверки: {e}"]
    
    def init_alembic(self) -> bool:
        """
        Инициализация Alembic в проекте.
        
        Returns:
            bool: True если успешно
        """
        try:
            if self.alembic_dir.exists():
                logger.info("ℹ️ Alembic уже инициализирован")
                return True
            
            # Создаем директорию для миграций
            logger.info("Инициализация Alembic...")
            command.init(self.alembic_cfg, str(self.alembic_dir))
            
            # Обновляем env.py для использования наших моделей
            self._update_env_py()
            
            logger.info("✅ Alembic инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации Alembic: {e}")
            return False
    
    def _update_env_py(self):
        """
        Обновление файла env.py для работы с нашими моделями.
        """
        env_py_path = self.alembic_dir / 'env.py'
        
        if not env_py_path.exists():
            logger.error(f"Файл {env_py_path} не найден")
            return
        
        try:
            with open(env_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Добавляем импорт моделей
            import_line = "from database.models import Base\n"
            target_metadata_line = "target_metadata = Base.metadata\n"
            
            if import_line not in content:
                # Находим место для вставки импорта
                lines = content.split('\n')
                
                # Ищем секцию импортов
                import_section_end = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        import_section_end = i
                    elif line.strip() == '' and import_section_end > 0:
                        break
                
                # Вставляем после последнего импорта
                if import_section_end > 0:
                    lines.insert(import_section_end + 1, import_line)
                else:
                    # Если импортов нет, вставляем в начало
                    lines.insert(0, import_line)
                
                # Обновляем target_metadata
                for i, line in enumerate(lines):
                    if 'target_metadata = None' in line:
                        lines[i] = target_metadata_line
                        break
                
                new_content = '\n'.join(lines)
                
                with open(env_py_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info("✅ Файл env.py обновлен для работы с моделями")
            else:
                logger.info("ℹ️ Файл env.py уже настроен")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении env.py: {e}")
    
    def create_initial_migration(self) -> bool:
        """
        Создание начальной миграции.
        
        Returns:
            bool: True если успешно
        """
        if not self.alembic_cfg:
            logger.error("Alembic не настроен")
            return False
        
        try:
            # Проверяем, есть ли уже миграции
            script = ScriptDirectory.from_config(self.alembic_cfg)
            if script.get_current_head():
                logger.info("ℹ️ Миграции уже существуют")
                return True
            
            # Проверяем, есть ли таблицы в БД
            with self.engine.connect() as conn:
                # Проверяем наличие таблицы alembic_version
                result = conn.execute(text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = 'alembic_version')"
                ))
                has_alembic_table = result.scalar()
                
                if has_alembic_table:
                    logger.warning("⚠️ Таблица alembic_version существует, но миграции не найдены")
                    logger.info("Используйте stamp_database() для пометки текущей версии")
                    return False
            
            # Создаем начальную миграцию
            logger.info("Создание начальной миграции...")
            success = self.create_migration("initial migration", autogenerate=True)
            
            if success:
                logger.info("✅ Начальная миграция создана")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при создании начальной миграции: {e}")
            return False
    
    def stamp_database(self, revision: str = "head") -> bool:
        """
        Установка версии без применения миграций.
        
        Args:
            revision: Версия
            
        Returns:
            bool: True если успешно
        """
        if not self.alembic_cfg:
            logger.error("Alembic не настроен")
            return False
        
        try:
            logger.info(f"Пометка базы данных версией {revision}...")
            command.stamp(self.alembic_cfg, revision)
            logger.info(f"✅ База данных помечена версией {revision}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при установке версии: {e}")
            return False
    
    def ensure_database_up_to_date(self) -> bool:
        """
        Гарантирует, что база данных находится в актуальном состоянии.
        Вызывается при запуске приложения.
        
        Returns:
            bool: True если успешно
        """
        logger.info("🔄 Проверка состояния базы данных...")
        
        # Проверяем подключение к БД
        if not self._connect_to_database():
            logger.error("❌ Невозможно подключиться к БД")
            return False
        
        # Проверяем наличие alembic директории
        if not self.alembic_dir.exists():
            logger.warning("⚠️ Alembic не инициализирован")
            if not self.init_alembic():
                logger.error("❌ Не удалось инициализировать Alembic")
                return False
        
        # Проверяем наличие миграций
        script = ScriptDirectory.from_config(self.alembic_cfg)
        if not script.get_current_head():
            logger.warning("⚠️ Миграции не найдены")
            
            # Проверяем, есть ли уже таблицы в БД
            has_tables = self._check_if_tables_exist()
            
            if has_tables:
                logger.info("📦 Таблицы уже существуют в БД")
                # Пытаемся создать начальную миграцию и применить stamp
                if self.create_initial_migration():
                    self.stamp_database("head")
            else:
                logger.info("🆕 Создание новой базы данных")
                # Создаем начальную миграцию и применяем её
                if self.create_initial_migration():
                    self.upgrade()
        
        # Проверяем наличие изменений
        has_changes, changes = self.check_for_changes()
        
        if has_changes:
            logger.warning("⚠️ Обнаружены изменения в моделях БД")
            
            # Создаем автоматическую миграцию
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.create_migration(f"auto_migration_{timestamp}", autogenerate=True):
                # Применяем миграцию
                success, message = self.upgrade()
                if success:
                    logger.info("✅ Изменения успешно применены")
                else:
                    logger.error(f"❌ Ошибка при применении изменений: {message}")
                    return False
            else:
                logger.error("❌ Не удалось создать миграцию для изменений")
                return False
        else:
            # Просто применяем все миграции
            success, message = self.upgrade()
            if not success:
                logger.error(f"❌ Ошибка при применении миграций: {message}")
                return False
        
        # Финальная проверка
        current_rev = self.get_current_revision()
        logger.info(f"✅ База данных в актуальном состоянии (версия: {current_rev})")
        
        return True
    
    def _check_if_tables_exist(self) -> bool:
        """
        Проверка, существуют ли таблицы в БД.
        
        Returns:
            bool: True если есть хотя бы одна таблица
        """
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            # Исключаем служебные таблицы
            user_tables = [t for t in tables if not t.startswith('alembic_')]
            
            return len(user_tables) > 0
            
        except Exception as e:
            logger.error(f"Ошибка при проверке таблиц: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """
        Получение информации о состоянии базы данных.
        
        Returns:
            dict: Информация о БД
        """
        info = {
            'connected': self.engine is not None,
            'database_url': self.database_url.replace(self.db_password, '****'),
            'current_revision': self.get_current_revision(),
            'alembic_initialized': self.alembic_dir.exists(),
            'tables_count': 0,
            'tables_list': []
        }
        
        if self.engine:
            try:
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                info['tables_count'] = len(tables)
                info['tables_list'] = tables
            except:
                pass
        
        return info
    
    def reset_database(self, confirm: bool = False) -> bool:
        """
        Сброс базы данных (удаление всех таблиц и создание заново).
        Только для разработки!
        
        Args:
            confirm: Подтверждение действия
            
        Returns:
            bool: True если успешно
        """
        if not confirm:
            logger.warning("⚠️ Сброс БД требует подтверждения (confirm=True)")
            return False
        
        logger.warning("⚠️ СБРОС БАЗЫ ДАННЫХ!")
        
        try:
            # Удаляем все таблицы
            Base.metadata.drop_all(self.engine)
            logger.info("✅ Все таблицы удалены")
            
            # Создаем таблицы заново
            Base.metadata.create_all(self.engine)
            logger.info("✅ Таблицы созданы заново")
            
            # Сбрасываем миграции
            if self.alembic_dir.exists():
                import shutil
                shutil.rmtree(self.alembic_dir)
                logger.info("✅ Директория миграций удалена")
            
            # Инициализируем заново
            self.init_alembic()
            self.create_initial_migration()
            self.upgrade()
            
            logger.info("✅ База данных полностью пересоздана")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сбросе БД: {e}")
            return False


# Создаем глобальный экземпляр для использования в приложении
migration_manager = MigrationManager()