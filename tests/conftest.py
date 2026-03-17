import os
import sys
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import psycopg
import logging
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Берем настройки из .env файла
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
TEST_DB_NAME = "vkinder_test"

SYSTEM_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
TEST_DB_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"

def create_test_database():
    """Создает тестовую базу данных если её нет"""
    try:
        logger.info(f"Подключение к PostgreSQL: {DB_HOST}:{DB_PORT}, пользователь: {DB_USER}")
        
        with psycopg.connect(SYSTEM_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,))
                if not cur.fetchone():
                    cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
                    logger.info(f"Тестовая БД {TEST_DB_NAME} создана")
                else:
                    logger.info(f"Тестовая БД {TEST_DB_NAME} уже существует")
        
        # Проверяем подключение к созданной БД
        test_dsn = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"
        with psycopg.connect(test_dsn) as conn:
            conn.execute("SELECT 1")
        
        return True
        
    except psycopg.OperationalError as e:
        error_msg = str(e)
        logger.error(f"Ошибка подключения к PostgreSQL: {error_msg}")
        print(f"\nОшибка подключения к PostgreSQL:")
        print(f"  {error_msg}")
        print(f"\nТекущие настройки (из .env файла):")
        print(f"  Пользователь: {DB_USER}")
        print(f"  Пароль: {'*****' if DB_PASSWORD else 'не указан'}")
        print(f"  Хост: {DB_HOST}")
        print(f"  Порт: {DB_PORT}")
        print(f"  Тестовая БД: {TEST_DB_NAME}")
        print(f"\nПроверьте:")
        print("1. Запущен ли PostgreSQL (services.msc)")
        print("2. Правильность пароля в .env файле")
        print("3. Что база данных postgres существует")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Автоматически создает тестовую БД перед запуском тестов"""
    if not create_test_database():
        pytest.exit("Не удалось подключиться к PostgreSQL. Проверьте настройки выше.")

@pytest.fixture(scope="session")
def engine():
    """Создает движок SQLAlchemy для тестов"""
    from app.database.base import Base
    
    log_url = TEST_DB_URL.replace(DB_PASSWORD, '****') if DB_PASSWORD else TEST_DB_URL
    logger.info(f"Подключение к тестовой БД: {log_url}")
    
    try:
        engine = create_engine(
            TEST_DB_URL,
            poolclass=NullPool,
            echo=False
        )
        
        # Проверяем подключение
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Создаем таблицы
        Base.metadata.create_all(engine)
        
        yield engine
        
    except Exception as e:
        logger.error(f"Ошибка при создании движка: {e}")
        raise
    finally:
        # Очищаем после тестов
        if 'engine' in locals():
            Base.metadata.drop_all(engine)
            engine.dispose()

@pytest.fixture
def session(engine):
    """Создает сессию для тестов с автоматическим откатом при ошибках"""
    SessionLocal = sessionmaker(
        bind=engine, 
        autocommit=False, 
        autoflush=False,
        expire_on_commit=False
    )
    session = SessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Ошибка в тесте, выполняем откат: {e}")
        session.rollback()
        raise
    finally:
        session.close()

@pytest.fixture
def clean_db(session):
    """Очищает все таблицы перед тестом"""
    from app.database.base import Base
    
    try:
        # Отключаем проверку внешних ключей временно
        session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        
        # Включаем проверку внешних ключей обратно
        session.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        session.commit()
    except Exception as e:
        logger.error(f"Ошибка при очистке БД: {e}")
        session.rollback()
        raise
    
    return session

@pytest.fixture
def test_user(session):
    """Создает тестового пользователя"""
    from app.database.models.user import User
    
    try:
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
        
        return user
    except Exception as e:
        logger.error(f"Ошибка при создании тестового пользователя: {e}")
        session.rollback()
        raise

@pytest.fixture
def test_users(session):
    """Создает нескольких тестовых пользователей"""
    from app.database.models.user import User
    
    try:
        users = [
            User(vk_id=1, first_name="Алексей", last_name="Алексеев", profile_url="url1", age=25, city="Москва", sex=2),
            User(vk_id=2, first_name="Мария", last_name="Иванова", profile_url="url2", age=23, city="СПб", sex=1),
            User(vk_id=3, first_name="Дмитрий", last_name="Смирнов", profile_url="url3", age=28, city="Казань", sex=2),
            User(vk_id=4, first_name="Елена", last_name="Козлова", profile_url="url4", age=22, city="Новосибирск", sex=1),
        ]
        
        session.add_all(users)
        session.commit()
        
        for user in users:
            session.refresh(user)
        
        return users
    except Exception as e:
        logger.error(f"Ошибка при создании тестовых пользователей: {e}")
        session.rollback()
        raise

@pytest.fixture
def transaction_session(session):
    """Создает сессию с явной транзакцией для тестов, требующих изоляции"""
    transaction = session.begin_nested()
    try:
        yield session
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise

# Добавляем фикстуру для отлова предупреждений
@pytest.fixture
def warning_catcher():
    """Фикстура для отлова и обработки предупреждений"""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        yield w

# Добавляем фикстуру для измерения времени выполнения
@pytest.fixture
def timer():
    """Фикстура для измерения времени выполнения тестов"""
    import time
    start = time.time()
    yield
    end = time.time()
    logger.info(f"Время выполнения: {end - start:.3f} сек")