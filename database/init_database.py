"""
Скрипт для инициализации базы данных
Создает все таблицы согласно моделям
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

# Импортируем модели
from database.models import Base

def init_database():
    """Инициализация базы данных"""
    print("=" * 60)
    print("🚀 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ VKINDER")
    print("=" * 60)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Параметры подключения
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'vkinder_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    # Формируем строку подключения с драйвером psycopg 3
    database_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print(f"\n📡 Параметры подключения:")
    print(f"   Хост: {db_host}")
    print(f"   Порт: {db_port}")
    print(f"   База данных: {db_name}")
    print(f"   Пользователь: {db_user}")
    print(f"   Пароль: {'*' * len(db_password) if db_password else '⚠️ НЕ УКАЗАН'}")
    
    if not db_password:
        print("\n⚠️  ВНИМАНИЕ: Пароль не указан в файле .env!")
        print("   Для подключения к PostgreSQL необходимо указать пароль.")
        print("\n📌 Инструкция:")
        print("   1. Откройте файл .env в корне проекта")
        print("   2. Добавьте или раскомментируйте строку:")
        print("      DB_PASSWORD=ваш_пароль_от_postgresql")
        print("   3. Сохраните файл и запустите скрипт снова")
        return False
    
    try:
        # Создаем движок
        print(f"\n🔄 Подключение к базе данных...")
        engine = create_engine(database_url, echo=False)
        
        # Проверяем подключение
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Подключение к БД успешно!")
        
        # Создаем все таблицы
        print("\n📦 Создание таблиц...")
        Base.metadata.create_all(engine)
        print("✅ Таблицы созданы!")
        
        # Проверяем созданные таблицы
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            print(f"\n📋 Создано таблиц: {len(tables)}")
            if tables:
                print("   Список таблиц:")
                for i, table in enumerate(tables, 1):
                    # Проверяем количество записей в таблице
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table[0]}"))
                    count = count_result.scalar()
                    print(f"   {i:2d}. {table[0]} (записей: {count})")
            else:
                print("   ⚠️ Таблицы не созданы!")
        
        print("\n" + "=" * 60)
        print("✅ БАЗА ДАННЫХ УСПЕШНО ИНИЦИАЛИЗИРОВАНА!")
        print("=" * 60)
        print("\n📌 Теперь можно:")
        print("   1. Получить токены VK и добавить их в .env")
        print("   2. Запустить бота: python run.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        print("\n🔧 Возможные причины:")
        print("   1. PostgreSQL не запущен")
        print("   → Запустите службу PostgreSQL")
        print("   2. Неправильный пароль в .env")
        print("   → Проверьте значение DB_PASSWORD")
        print("   3. База данных vkinder_db не создана")
        print("   → Создайте БД через pgAdmin 4")
        return False

def check_existing_tables():
    """Проверка существующих таблиц без создания новых"""
    print("\n" + "=" * 60)
    print("🔍 ПРОВЕРКА СУЩЕСТВУЮЩИХ ТАБЛИЦ")
    print("=" * 60)
    
    load_dotenv()
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'vkinder_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    if not db_password:
        print("\n⚠️  Пароль не указан в .env. Проверка невозможна.")
        return False
    
    database_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Проверяем подключение
            conn.execute(text("SELECT 1"))
            print("✅ Подключение к БД успешно!")
            
            # Получаем список таблиц
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"\n📊 Найдено таблиц: {len(tables)}")
                print("   Существующие таблицы:")
                for i, table in enumerate(tables, 1):
                    # Проверяем количество записей в таблице
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table[0]}"))
                    count = count_result.scalar()
                    print(f"   {i:2d}. {table[0]} (записей: {count})")
            else:
                print("\n📭 Таблицы не найдены. База данных пуста.")
                print("   Запустите инициализацию (пункт 1 меню)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при проверке: {e}")
        return False

def show_help():
    """Показать справку по настройке"""
    print("\n" + "=" * 60)
    print("📖 СПРАВКА ПО НАСТРОЙКЕ")
    print("=" * 60)
    print("""
🔧 НАСТРОЙКА ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ:

1.  Убедитесь, что PostgreSQL запущен:
    • Windows: Запустите службу PostgreSQL
    • Команда: Start-Service postgresql*

2.  Проверьте файл .env в корне проекта:
    Должны быть указаны:
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=vkinder_db
    DB_USER=postgres
    DB_PASSWORD=ваш_пароль

3.  Убедитесь, что база данных существует:
    • Откройте pgAdmin 4
    • Проверьте наличие БД vkinder_db
    • Если нет - создайте: правый клик → Create → Database

4.  Запустите инициализацию:
    • Выберите пункт 1 в меню

❓ ЕСЛИ ВОЗНИКАЮТ ОШИБКИ:

• Ошибка подключения → проверьте пароль и что PostgreSQL запущен
• Ошибка "database does not exist" → создайте БД через pgAdmin
• Ошибка "password authentication failed" → проверьте пароль в .env
    """)

if __name__ == "__main__":
    print("\n" + "🔥" * 35)
    print("🔥  ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ VKINDER")
    print("🔥" * 35)
    
    while True:
        print("\n📋 Меню:")
        print("   1 - Инициализировать БД (создать все таблицы)")
        print("   2 - Проверить существующие таблицы")
        print("   3 - Справка по настройке")
        print("   4 - Выход")
        print("-" * 40)
        
        choice = input("Ваш выбор (1-4): ").strip()
        
        if choice == "1":
            init_database()
        elif choice == "2":
            check_existing_tables()
        elif choice == "3":
            show_help()
        elif choice == "4":
            print("\n👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Пожалуйста, введите 1, 2, 3 или 4")
        
        input("\nНажмите Enter для продолжения...")