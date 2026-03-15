import os
from dotenv import load_dotenv
from app.database.engine import init_models

load_dotenv()

def main():
    print("--- Запуск VKinder ---")
    
    # 1. Инициализация базы данных
    
    try:
        print("Проверка и инициализация базы данных")
        init_models()
        print("База данных готова")
    except Exception as e:
        print(f"Ошибка при настройке базы данных: {e}")
        return

    # 2. Здесь будет прописана логика бота
    print("Бот готов к работе")
    
    

if __name__ == "__main__":
    main()