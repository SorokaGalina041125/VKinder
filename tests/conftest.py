"""
Общие фикстуры для тестов с использованием PostgreSQL в Docker
"""
import pytest
import time
import sys
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.database.base import Base
from app.database.models import User, SearchCriteria, ViewedUser, Photo, Like, UserInterest
from app.config import get_test_settings, settings


# Получаем настройки для тестов
test_settings = get_test_settings()


def get_test_database_url() -> str:
    """Получить URL для тестовой базы данных"""
    return f"postgresql+psycopg://{test_settings.DB_USER}:{test_settings.DB_PASSWORD}@{test_settings.DB_HOST}:{test_settings.DB_PORT}/{test_settings.DB_NAME}"


def create_test_database() -> None:
    """Создать тестовую базу данных с защитой от удаления продакшн БД"""
    if test_settings.DB_NAME == settings.DB_NAME:
        raise ValueError(
            f"Имя тестовой базы '{test_settings.DB_NAME}' совпадает с именем основной базы! "
            "Это опасно. Пожалуйста, измените TEST_DB_NAME или DB_NAME в настройках."
        )
    
    sys_engine = create_engine(
        f"postgresql+psycopg://{test_settings.DB_USER}:{test_settings.DB_PASSWORD}@{test_settings.DB_HOST}:{test_settings.DB_PORT}/postgres",
        isolation_level="AUTOCOMMIT"
    )
    
    with sys_engine.connect() as conn:
        # Закрываем существующие подключения к тестовой базе
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{test_settings.DB_NAME}' AND pid <> pg_backend_pid()
        """))
        
        # Удаляем тестовую базу если существует
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_settings.DB_NAME}"))
        
        # Создаем новую тестовую базу
        conn.execute(text(f"CREATE DATABASE {test_settings.DB_NAME}"))
    
    sys_engine.dispose()


def drop_test_database() -> None:
    """Удалить тестовую базу данных с защитой"""
    if test_settings.DB_NAME == settings.DB_NAME:
        raise ValueError("Нельзя удалить основную базу данных!")
    
    sys_engine = create_engine(
        f"postgresql+psycopg://{test_settings.DB_USER}:{test_settings.DB_PASSWORD}@{test_settings.DB_HOST}:{test_settings.DB_PORT}/postgres",
        isolation_level="AUTOCOMMIT"
    )
    
    with sys_engine.connect() as conn:
        # Закрываем существующие подключения
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{test_settings.DB_NAME}' AND pid <> pg_backend_pid()
        """))
        
        # Удаляем базу
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_settings.DB_NAME}"))
    
    sys_engine.dispose()


@pytest.fixture(scope="session")
def test_engine():
    """
    Фикстура для создания тестовой базы данных.
    Создает базу перед всеми тестами и удаляет после.
    """
    # Создаем тестовую базу
    create_test_database()
    
    # Создаем engine для тестовой базы
    test_url = get_test_database_url()
    engine = create_engine(test_url, pool_pre_ping=True)
    
    # Создаем все таблицы
    Base.metadata.create_all(engine)
    
    yield engine
    
    # После всех тестов удаляем базу
    drop_test_database()
    engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Фикстура для сессии базы данных.
    Оборачивает каждый тест в транзакцию и откатывает её после выполнения.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def real_vk_api():
    """
    Фикстура для реального VK API.
    Использует токен из настроек с задержками для избежания rate limit.
    """
    from app.bot.search.vk_client import VKClient
    
    vk_client = VKClient(test_settings.VK_USER_TOKEN)
    return vk_client


@pytest.fixture(autouse=True)
def rate_limit_sleep():
    """
    Автоматическая задержка для всех тестов в test_integration.
    Избегаем rate limit VK API.
    """
    import inspect
    frame = inspect.currentframe()
    if frame and frame.f_back:
        module = frame.f_back.f_globals.get('__file__', '')
        if 'test_integration' in module:
            time.sleep(0.34)
    yield


@pytest.fixture
def test_user(db_session, real_vk_api):
    """
    Фикстура для создания тестового пользователя.
    """
    from app.database.crud.user import get_or_create_user
    
    # Используем ID тестового пользователя
    test_user_id = test_settings.TEST_USER_ID
    user = get_or_create_user(db_session, real_vk_api, vk_id=test_user_id)
    return user


@pytest.fixture
def test_candidate(db_session, real_vk_api):
    """
    Фикстура для создания тестового кандидата (закрытый профиль).
    """
    from app.database.crud.user import register_candidate
    from app.database.models import User
    
    test_candidate_id = test_settings.TEST_CANDIDATE_ID
    
    # Для интеграционных тестов - реальный API
    try:
        user_info = real_vk_api.api.users.get(
            user_ids=test_candidate_id,
            fields='domain, bdate, city, sex'
        )[0]
        
        candidate = register_candidate(db_session, user_info)
        return candidate
    except Exception:
        # Заглушка для случаев, когда API недоступен
        candidate = User(
            vk_id=test_candidate_id,
            first_name="Закрытый",
            last_name="Профиль",
            age=None,
            city=None,
            sex=None,
            profile_url=f"https://vk.com/id{test_candidate_id}",
            is_bot_user=False
        )
        db_session.add(candidate)
        db_session.commit()
        return candidate


@pytest.fixture
def test_search_criteria(db_session, test_user):
    """
    Фикстура для создания критериев поиска.
    """
    from app.database.crud.criteria import update_criteria
    
    criteria = update_criteria(
        db_session, 
        test_user.vk_id,
        age_from=20,
        age_to=35,
        city="Москва",
        sex=1
    )
    return criteria


@pytest.fixture
def closed_profile_vk_id() -> int:
    """
    ID заведомо закрытого профиля для тестирования.
    """
    # Используем ID закрытого профиля из настроек
    return getattr(test_settings, 'TEST_CANDIDATE_ID', 33556489)