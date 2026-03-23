"""
Настройка подключения к базе данных
"""
import psycopg
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings
from app.database.base import Base

# Создаем engine ОДИН РАЗ на уровне модуля
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    echo=False  # Для отладки можно включить True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_if_not_exists() -> None:
    """Создает базу данных, если она не существует"""
    try:
        with psycopg.connect(settings.SYSTEM_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.DB_NAME,))
                exists = cur.fetchone()
                
                if not exists:
                    cur.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
                    print(f"База данных {settings.DB_NAME} успешно создана.")
                else:
                    print(f"База данных {settings.DB_NAME} уже существует.")
    except Exception as e:
        print(f"Ошибка при проверке/создании базы данных: {e}")


def init_models() -> None:
    """Создание всех таблиц"""
    try:
        create_db_if_not_exists()
        Base.metadata.create_all(bind=engine)
        print("Все таблицы успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")


def get_db() -> Generator[Session, None, None]:
    """Генератор сессий для Dependency Injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()