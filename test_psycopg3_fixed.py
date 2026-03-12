"""
Исправленный тестовый скрипт для проверки psycopg 3 и SQLAlchemy
"""

import sys
import psycopg
import sqlalchemy
import dotenv
import os
from importlib.metadata import version
from sqlalchemy import text

def get_package_version(package_name):
    """Получение версии пакета"""
    try:
        return version(package_name)
    except:
        return "unknown"

def print_header(title):
    """Печать заголовка"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def test_installation():
    """Проверка установки всех компонентов"""
    print_header("ПРОВЕРКА УСТАНОВКИ БИБЛИОТЕК")
    
    # Версии
    print(f"🐍 Python: {sys.version}")
    print(f"📦 psycopg: {psycopg.__version__}")
    print(f"📦 SQLAlchemy: {sqlalchemy.__version__}")
    print(f"📦 python-dotenv: {get_package_version('python-dotenv')}")
    print()
    
    # Проверка psycopg 3
    print("🔍 Проверка psycopg 3:")
    try:
        print(f"   📍 Модуль: {psycopg.__file__}")
        print("   ✅ psycopg 3 успешно загружен")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Проверка SQLAlchemy
    print("\n🔍 Проверка SQLAlchemy:")
    try:
        print(f"   📍 Модуль: {sqlalchemy.__file__}")
        print("   ✅ SQLAlchemy успешно загружен")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    return True

def test_psycopg3_connection(db_config):
    """Тест прямого подключения через psycopg 3"""
    print("\n🔌 ТЕСТ 1: Прямое подключение через psycopg 3")
    print("-" * 50)
    
    try:
        # Подключаемся
        conn = psycopg.connect(
            host=db_config['host'],
            port=db_config['port'],
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        # Создаем курсор
        cur = conn.cursor()
        
        # Выполняем запрос
        cur.execute("SELECT version()")
        version = cur.fetchone()
        print(f"   ✅ Версия PostgreSQL: {version[0]}")
        
        # Получаем список баз данных
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        databases = cur.fetchall()
        print(f"   ✅ Доступные базы данных: {', '.join([db[0] for db in databases])}")
        
        # Проверяем текущую базу
        cur.execute("SELECT current_database()")
        current_db = cur.fetchone()
        print(f"   ✅ Текущая база данных: {current_db[0]}")
        
        # Закрываем соединение
        cur.close()
        conn.close()
        print("   ✅ Подключение через psycopg 3 успешно завершено")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка psycopg 3: {e}")
        return False

def test_sqlalchemy_with_psycopg3(db_config):
    """Тест подключения через SQLAlchemy с драйвером psycopg 3"""
    print("\n🔌 ТЕСТ 2: SQLAlchemy с драйвером psycopg 3")
    print("-" * 50)
    
    try:
        # Формируем правильную строку подключения для psycopg 3
        # Важно: используем postgresql+psycopg:// вместо postgresql://
        database_url = (f"postgresql+psycopg://{db_config['user']}:{db_config['password']}"
                       f"@{db_config['host']}:{db_config['port']}/{db_config['dbname']}")
        
        print(f"   📍 Строка подключения: postgresql+psycopg://{db_config['user']}:****@{db_config['host']}:{db_config['port']}/{db_config['dbname']}")
        
        # Создаем engine
        engine = sqlalchemy.create_engine(
            database_url,
            echo=False,  # Включить True для отладки SQL запросов
            pool_pre_ping=True  # Проверка соединения перед использованием
        )
        
        print(f"   ✅ Engine создан: {engine}")
        
        # Тестируем подключение
        with engine.connect() as conn:
            # Простой запрос
            result = conn.execute(text("SELECT 1"))
            print(f"   ✅ Простой запрос: {result.scalar()}")
            
            # Информация о версии
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   ✅ Версия PostgreSQL: {version[:60]}...")
            
            # Список таблиц в схеме public
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"   ✅ Таблиц в схеме public: {len(tables)}")
                print("   📋 Таблицы:")
                for i, table in enumerate(tables[:10], 1):
                    print(f"      {i}. {table[0]}")
                if len(tables) > 10:
                    print(f"      ... и еще {len(tables) - 10}")
            else:
                print("   ⚠️ В схеме public нет таблиц (база данных пуста)")
            
            # Проверка схемы
            result = conn.execute(text("SELECT current_schema()"))
            schema = result.scalar()
            print(f"   ✅ Текущая схема: {schema}")
        
        print("   ✅ SQLAlchemy с psycopg 3 успешно протестирован")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка SQLAlchemy с psycopg 3: {e}")
        print(f"   🔍 Тип ошибки: {type(e).__name__}")
        return False

def test_sqlalchemy_alternative(db_config):
    """Альтернативный тест с созданием тестовой таблицы"""
    print("\n🔌 ТЕСТ 3: Создание и работа с тестовой таблицей")
    print("-" * 50)
    
    try:
        database_url = (f"postgresql+psycopg://{db_config['user']}:{db_config['password']}"
                       f"@{db_config['host']}:{db_config['port']}/{db_config['dbname']}")
        
        engine = sqlalchemy.create_engine(database_url)
        
        with engine.connect() as conn:
            # Начинаем транзакцию
            trans = conn.begin()
            
            try:
                # Создаем временную тестовую таблицу
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS test_connection (
                        id SERIAL PRIMARY KEY,
                        test_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("   ✅ Тестовая таблица создана")
                
                # Вставляем тестовые данные
                conn.execute(
                    text("INSERT INTO test_connection (test_data) VALUES (:data)"),
                    {"data": "Тестовое подключение"}
                )
                print("   ✅ Тестовые данные вставлены")
                
                # Читаем данные
                result = conn.execute(
                    text("SELECT * FROM test_connection ORDER BY created_at DESC LIMIT 1")
                )
                row = result.fetchone()
                print(f"   ✅ Данные прочитаны: ID={row[0]}, data={row[1]}, created={row[2]}")
                
                # Удаляем тестовую таблицу
                conn.execute(text("DROP TABLE test_connection"))
                print("   ✅ Тестовая таблица удалена")
                
                # Подтверждаем транзакцию
                trans.commit()
                print("   ✅ Транзакция подтверждена")
                
            except Exception as e:
                trans.rollback()
                print(f"   ⚠️ Ошибка в транзакции, откат: {e}")
                raise
        
        print("   ✅ Полный цикл работы с БД успешно завершен")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка в тесте с таблицей: {e}")
        return False

def test_connection():
    """Основной тест подключения к PostgreSQL"""
    print_header("ТЕСТ ПОДКЛЮЧЕНИЯ К POSTGRESQL")
    
    # Загружаем переменные окружения
    dotenv.load_dotenv()
    
    # Параметры подключения
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'dbname': os.getenv('DB_NAME', 'vkinder_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    print("\n📋 Параметры подключения:")
    print(f"   Хост: {db_config['host']}")
    print(f"   Порт: {db_config['port']}")
    print(f"   База данных: {db_config['dbname']}")
    print(f"   Пользователь: {db_config['user']}")
    print(f"   Пароль: {'*' * len(db_config['password']) if db_config['password'] else '⚠️ НЕ УКАЗАН'}")
    
    if not db_config['password']:
        print("\n⚠️  ВНИМАНИЕ: Пароль не указан в .env файле!")
        print("   Добавьте строку: DB_PASSWORD=ваш_пароль")
        return False
    
    results = []
    
    # Тест 1: Прямое подключение через psycopg 3
    results.append(("psycopg3", test_psycopg3_connection(db_config)))
    
    # Тест 2: SQLAlchemy с psycopg 3
    results.append(("sqlalchemy_psycopg3", test_sqlalchemy_with_psycopg3(db_config)))
    
    # Тест 3: Работа с таблицей (только если предыдущие тесты успешны)
    if all(r[1] for r in results[:2]):
        results.append(("table_operations", test_sqlalchemy_alternative(db_config)))
    else:
        print("\n⚠️  Пропускаем тест с таблицей из-за ошибок в предыдущих тестах")
    
    # Итоги
    print_header("ИТОГИ ТЕСТИРОВАНИЯ")
    
    all_success = True
    for test_name, success in results:
        status = "✅ УСПЕШНО" if success else "❌ ОШИБКА"
        print(f"   {status} - {test_name}")
        all_success = all_success and success
    
    if all_success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("   PostgreSQL настроен корректно, можно работать с базой данных!")
    else:
        print("\n⚠️  ЕСТЬ ПРОБЛЕМЫ С ПОДКЛЮЧЕНИЕМ")
        print("\n🔧 Возможные решения:")
        print("   1. Проверьте что PostgreSQL запущен")
        print("   2. Проверьте правильность пароля в .env")
        print("   3. Убедитесь что база данных 'vkinder_db' существует")
        print("   4. Проверьте что порт 5432 открыт")
    
    return all_success

def quick_test():
    """Быстрый тест без подключения к БД"""
    print_header("БЫСТРЫЙ ТЕСТ (БЕЗ ПОДКЛЮЧЕНИЯ К БД)")
    
    # Проверяем, что все библиотеки импортируются
    libraries = [
        ('psycopg', psycopg),
        ('sqlalchemy', sqlalchemy),
        ('dotenv', dotenv),
    ]
    
    all_ok = True
    for name, lib in libraries:
        try:
            print(f"   ✅ {name} - {lib.__file__}")
        except AttributeError:
            print(f"   ✅ {name} - импортирован")
        except Exception as e:
            print(f"   ❌ {name} - ошибка: {e}")
            all_ok = False
    
    if all_ok:
        print("\n✅ Все библиотеки успешно импортированы!")
        print("\n👉 Теперь можно запустить полный тест (режим 1)")
    else:
        print("\n❌ Есть проблемы с импортом библиотек")

def show_instructions():
    """Показать инструкции по настройке"""
    print_header("ИНСТРУКЦИИ ПО НАСТРОЙКЕ")
    print("""
🔧 НАСТРОЙКА POSTGRESQL:

1.  Проверьте, запущен ли PostgreSQL:
    PowerShell (администратор):
    > Get-Service postgres*
    > Start-Service postgresql*

2.  Создайте базу данных через pgAdmin 4:
    - Подключитесь к серверу
    - Правый клик на "Databases" → Create → Database
    - Имя: vkinder_db
    - Owner: postgres
    - Save

3.  Проверьте файл .env в корне проекта:
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=vkinder_db
    DB_USER=postgres
    DB_PASSWORD=ваш_пароль

4.  Для SQLAlchemy используйте строку подключения:
    postgresql+psycopg://user:password@host:port/dbname
    (ВАЖНО: +psycopg указывает на использование драйвера psycopg 3)

5.  Установите все зависимости:
    > pip install -r requirements.txt
    """)

if __name__ == "__main__":
    print("\n" + "🔥" * 35)
    print("🔥  ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К POSTGRESQL")
    print("🔥" * 35)
    
    while True:
        print("\n📋 Меню:")
        print("   1 - Полный тест (с подключением к БД)")
        print("   2 - Быстрый тест (без подключения к БД)")
        print("   3 - Инструкции по настройке")
        print("   4 - Выход")
        print("-" * 40)
        
        choice = input("Ваш выбор (1-4): ").strip()
        
        if choice == "1":
            test_installation()
            test_connection()
        elif choice == "2":
            quick_test()
        elif choice == "3":
            show_instructions()
        elif choice == "4":
            print("\n👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Пожалуйста, введите 1, 2, 3 или 4")
        
        input("\nНажмите Enter для продолжения...")