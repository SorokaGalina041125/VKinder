import os
import psycopg
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SYSTEM_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"

def create_db_if_not_exists():
    """Создает базу данных, если она не существует"""
    try:
        with psycopg.connect(SYSTEM_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
                exists = cur.fetchone()
                
                if not exists:
                    cur.execute(f'CREATE DATABASE "{DB_NAME}"')
                    print(f"База данных {DB_NAME} успешно создана.")
                else:
                    print(f"База данных {DB_NAME} уже существует.")
    except Exception as e:
        print(f"Ошибка при проверке/создании базы данных: {e}")


create_db_if_not_exists()

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_models():
    try:
        Base.metadata.create_all(bind=engine)
        print("Все таблицы успешно синхронизированы.")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")