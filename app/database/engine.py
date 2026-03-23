"""
Database engine and schema bootstrap helpers.
"""
from typing import Generator

import psycopg
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database.base import Base


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_if_not_exists() -> None:
    """Create the target database if it does not exist yet."""
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
        raise RuntimeError(f"Ошибка при проверке/создании базы данных: {e}") from e


def sync_schema() -> None:
    """Add columns required by the current models to older databases."""
    schema_updates = {
        "users": [
            ("is_bot_user", "ALTER TABLE users ADD COLUMN is_bot_user BOOLEAN NOT NULL DEFAULT FALSE"),
            ("state", "ALTER TABLE users ADD COLUMN state VARCHAR(50) DEFAULT 'idle'"),
        ],
        "search_criteria": [
            ("city_id", "ALTER TABLE search_criteria ADD COLUMN city_id INTEGER"),
            ("search_offset", "ALTER TABLE search_criteria ADD COLUMN search_offset INTEGER NOT NULL DEFAULT 0"),
        ],
        "photos": [
            ("popularity_score", "ALTER TABLE photos ADD COLUMN popularity_score INTEGER NOT NULL DEFAULT 0"),
        ],
        "user_interests": [
            ("interest_source_id", "ALTER TABLE user_interests ADD COLUMN interest_source_id VARCHAR(100)"),
        ],
    }

    with engine.begin() as conn:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())

        for table_name, updates in schema_updates.items():
            if table_name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, ddl in updates:
                if column_name not in existing_columns:
                    conn.execute(text(ddl))


def init_models() -> None:
    """Create missing tables and synchronize older schemas."""
    try:
        create_db_if_not_exists()
        Base.metadata.create_all(bind=engine)
        sync_schema()
        print("Все таблицы успешно созданы.")
    except Exception as e:
        raise RuntimeError(f"Ошибка при создании таблиц: {e}") from e


def get_db() -> Generator[Session, None, None]:
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
