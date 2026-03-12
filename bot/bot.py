"""
Основной модуль бота VKinder.
Обрабатывает сообщения пользователей и управляет логикой знакомств.
"""

import time
import random
from typing import Dict, List, Optional

# Импортируем наши модули
from database import initialize_database, DatabaseManager
from database.models import User
from vk_api_handler.vk_client import VKClient


class VKinderBot:
    """
    Основной класс бота VKinder.
    """
    
    def __init__(self):
        """Инициализация бота"""
        print("🚀 Запуск VKinder бота...")
        
        # Инициализируем базу данных (с проверкой миграций)
        self.db = initialize_database()
        
        # Инициализируем VK клиент
        self.vk = VKClient()
        
        # Текущие сессии пользователей
        self.user_sessions = {}
        
        print("✅ VKinder бот инициализирован")
    
    def handle_message(self, user_id: int, message_text: str) -> None:
        """
        Обработка входящего сообщения.
        
        Args:
            user_id: ID пользователя
            message_text: Текст сообщения
        """
        # Получаем или создаем сессию пользователя
        session = self._get_user_session(user_id)
        
        # Обрабатываем команды
        if message_text.lower() == '/start':
            self._handle_start(user_id)
        elif message_text.lower() == '/search':
            self._handle_search(user_id)
        elif message_text.lower() == '/next':
            self._handle_next(user_id)
        elif message_text.lower() == '/favorites':
            self._handle_favorites(user_id)
        elif message_text.lower() == '/blacklist':
            self._handle_blacklist(user_id)
        elif message_text.lower() == '/like':
            self._handle_like(user_id)
        elif message_text.lower() == '/help':
            self._handle_help(user_id)
        else:
            # Обработка callback-кнопок
            self._handle_callback(user_id, message_text)
    
    def _get_user_session(self, user_id: int) -> Dict:
        """
        Получение или создание сессии пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict: Сессия пользователя
        """
        if user_id not in self.user_sessions:
            # Получаем информацию о пользователе из VK
            user_info = self.vk.get_user_info(user_id)
            
            if user_info:
                # Сохраняем пользователя в БД
                self.db.add_or_update_user(
                    vk_id=user_id,
                    first_name=user_info['first_name'],
                    last_name=user_info['last_name'],
                    age=user_info['age'],
                    city=user_info['city'],
                    sex=user_info['sex'],
                    profile_url=user_info['profile_url']
                )
            
            # Создаем сессию
            self.user_sessions[user_id] = {
                'current_candidates': [],
                'current_index': 0,
                'search_offset': 0,
                'criteria': self._get_default_criteria(user_info)
            }
        
        return self.user_sessions[user_id]
    
    def _get_default_criteria(self, user_info: Dict) -> Dict:
        """
        Получение критериев поиска по умолчанию.
        
        Args:
            user_info: Информация о пользователе
            
        Returns:
            Dict: Критерии поиска
        """
        criteria = {
            'age_from': 18,
            'age_to': 45,
            'has_photos': True
        }
        
        if user_info:
            # Противоположный пол
            if user_info.get('sex') == 1:
                criteria['sex'] = 2  # Ищем мужчин
            elif user_info.get('sex') == 2:
                criteria['sex'] = 1  # Ищем женщин
            
            # Тот же город
            if user_info.get('city'):
                criteria['city'] = user_info['city']
            
            # Возраст +/- 5 лет
            if user_info.get('age'):
                criteria['age_from'] = max(18, user_info['age'] - 5)
                criteria['age_to'] = user_info['age'] + 5
        
        return criteria
    
    def _handle_start(self, user_id: int) -> None:
        """
        Обработка команды /start.
        
        Args:
            user_id: ID пользователя
        """
        # Получаем информацию о пользователе
        user_info = self.vk.get_user_info(user_id)
        
        welcome_text = (
            f"👋 Привет, {user_info['first_name']}!\n\n"
            "Я бот VKinder - помогу тебе найти новых знакомых!\n\n"
            "📌 Доступные команды:\n"
            "/search - начать поиск\n"
            "/next - следующий кандидат\n"
            "/favorites - список избранных\n"
            "/blacklist - черный список\n"
            "/like - поставить лайк текущему кандидату\n"
            "/help - помощь\n\n"
            "Нажми /search, чтобы начать!"
        )
        
        self.vk.send_message(user_id, welcome_text)
    
    def _handle_search(self, user_id: int) -> None:
        """
        Обработка команды /search - начало поиска.
        
        Args:
            user_id: ID пользователя
        """
        session = self._get_user_session(user_id)
        
        # Отправляем сообщение о начале поиска
        self.vk.send_message(user_id, "🔍 Ищу подходящих кандидатов...")
        
        # Выполняем поиск
        start_time = time.time()
        candidates = self.vk.search_users_batch(
            criteria=session['criteria'],
            total_needed=100
        )
        search_time = time.time() - start_time
        
        # Логируем поиск
        self.db.log_search(
            user_vk_id=user_id,
            search_params=session['criteria'],
            results_count=len(candidates),
            execution_time=search_time
        )
        
        if not candidates:
            self.vk.send_message(
                user_id, 
                "😕 К сожалению, никого не найдено. Попробуй изменить критерии поиска."
            )
            return
        
        # Получаем ID пользователей в черном списке
        blacklist = [u.vk_id for u in self.db.get_blacklist(user_id)]
        
        # Фильтруем кандидатов
        filtered_candidates = []
        for candidate in candidates:
            if candidate['id'] not in blacklist:
                filtered_candidates.append(candidate)
        
        session['current_candidates'] = filtered_candidates
        session['current_index'] = 0
        
        # Показываем первого кандидата
        self._show_candidate(user_id)
    
    def _show_candidate(self, user_id: int) -> None:
        """
        Показ текущего кандидата.
        
        Args:
            user_id: ID пользователя
        """
        session = self._get_user_session(user_id)
        
        if not session['current_candidates'] or session['current_index'] >= len(session['current_candidates']):
            self.vk.send_message(
                user_id,
                "🏁 Кандидаты закончились. Нажми /search для нового поиска."
            )
            return
        
        candidate = session['current_candidates'][session['current_index']]
        
        # Получаем топ-3 фотографии
        photos = self.vk.get_top_photos(candidate['id'], count=3)
        
        # Сохраняем фото в БД
        if photos:
            self.db.save_photos(candidate['id'], photos)
        
        # Добавляем в просмотренные
        self.db.add_viewed_user(user_id, candidate['id'])
        
        # Форматируем и отправляем сообщение
        message, attachments = self.vk.format_user_info_message(candidate, photos)
        
        # Добавляем инструкцию
        message += "\n\n❓ Действия:\n❤️ /favorite - в избранное\n🚫 /blacklist - в черный список\n👍 /like - лайк фото\n⏭ /next - следующий"
        
        self.vk.send_message_with_photos(user_id, message, attachments)
    
    def _handle_next(self, user_id: int) -> None:
        """
        Обработка команды /next - переход к следующему кандидату.
        
        Args:
            user_id: ID пользователя
        """
        session = self._get_user_session(user_id)
        session['current_index'] += 1
        self._show_candidate(user_id)
    
    def _handle_favorites(self, user_id: int) -> None:
        """
        Обработка команды /favorites - показ избранных.
        
        Args:
            user_id: ID пользователя
        """
        favorites = self.db.get_favorites(user_id)
        
        if not favorites:
            self.vk.send_message(
                user_id,
                "📭 У вас пока нет избранных пользователей."
            )
            return
        
        message = "🌟 Ваши избранные:\n\n"
        for i, fav in enumerate(favorites, 1):
            message += f"{i}. {fav.first_name} {fav.last_name}\n"
            message += f"   {fav.profile_url}\n"
            
            # Получаем фото
            photos = self.db.get_photos(fav.vk_id, limit=1)
            if photos:
                message += f"   Фото: {photos[0].photo_url}\n"
            message += "\n"
        
        self.vk.send_message(user_id, message)
    
    def _handle_blacklist(self, user_id: int) -> None:
        """
        Обработка команды /blacklist - показ черного списка.
        
        Args:
            user_id: ID пользователя
        """
        blacklist = self.db.get_blacklist(user_id)
        
        if not blacklist:
            self.vk.send_message(
                user_id,
                "📭 Черный список пуст."
            )
            return
        
        message = "🚫 Черный список:\n\n"
        for i, bl in enumerate(blacklist, 1):
            message += f"{i}. {bl.first_name} {bl.last_name}\n"
            message += f"   {bl.profile_url}\n\n"
        
        self.vk.send_message(user_id, message)
    
    def _handle_like(self, user_id: int) -> None:
        """
        Обработка команды /like - лайк текущему кандидату.
        
        Args:
            user_id: ID пользователя
        """
        session = self._get_user_session(user_id)
        
        if not session['current_candidates'] or session['current_index'] >= len(session['current_candidates']):
            self.vk.send_message(
                user_id,
                "❌ Нет текущего кандидата для лайка."
            )
            return
        
        candidate = session['current_candidates'][session['current_index']]
        
        # Получаем фото кандидата
        photos = self.db.get_photos(candidate['id'], limit=1)
        
        if photos:
            # Ставим лайк первому фото
            photo = photos[0]
            if self.vk.like_photo(photo.owner_id, int(photo.photo_id)):
                self.vk.send_message(
                    user_id,
                    f"👍 Вы поставили лайк фото пользователя {candidate['first_name']}!"
                )
            else:
                self.vk.send_message(
                    user_id,
                    "❌ Не удалось поставить лайк."
                )
        else:
            self.vk.send_message(
                user_id,
                "❌ У кандидата нет фотографий для лайка."
            )
    
    def _handle_help(self, user_id: int) -> None:
        """
        Обработка команды /help - показ помощи.
        
        Args:
            user_id: ID пользователя
        """
        help_text = (
            "📚 Помощь по VKinder:\n\n"
            "🔍 /search - начать поиск кандидатов\n"
            "⏭ /next - показать следующего кандидата\n"
            "❤️ /favorite - добавить текущего в избранное\n"
            "🚫 /blacklist - добавить в черный список\n"
            "📋 /favorites - показать список избранных\n"
            "📋 /blacklist - показать черный список\n"
            "👍 /like - поставить лайк текущему кандидату\n"
            "❓ /help - показать это сообщение\n\n"
            "Советы:\n"
            "- Кандидаты подбираются на основе ваших данных\n"
            "- Черный список помогает исключить нежелательных людей\n"
            "- Избранное сохраняет понравившихся кандидатов"
        )
        
        self.vk.send_message(user_id, help_text)
    
    def _handle_callback(self, user_id: int, callback_data: str) -> None:
        """
        Обработка callback-кнопок.
        
        Args:
            user_id: ID пользователя
            callback_data: Данные кнопки
        """
        if callback_data == 'favorite':
            self._handle_add_to_favorites(user_id)
        elif callback_data == 'blacklist':
            self._handle_add_to_blacklist(user_id)
        elif callback_data == 'next':
            self._handle_next(user_id)
        elif callback_data == 'like':
            self._handle_like(user_id)
    
    def _handle_add_to_favorites(self, user_id: int) -> None:
        """
        Добавление текущего кандидата в избранное.
        
        Args:
            user_id: ID пользователя
        """
        session = self._get_user_session(user_id)
        
        if not session['current_candidates'] or session['current_index'] >= len(session['current_candidates']):
            self.vk.send_message(
                user_id,
                "❌ Нет текущего кандидата для добавления в избранное."
            )
            return
        
        candidate = session['current_candidates'][session['current_index']]
        
        if self.db.add_to_favorites(user_id, candidate['id']):
            self.vk.send_message(
                user_id,
                f"❤️ {candidate['first_name']} добавлен(а) в избранное!"
            )
        else:
            self.vk.send_message(
                user_id,
                "❌ Не удалось добавить в избранное."
            )
    
    def _handle_add_to_blacklist(self, user_id: int) -> None:
        """
        Добавление текущего кандидата в черный список.
        
        Args:
            user_id: ID пользователя
        """
        session = self._get_user_session(user_id)
        
        if not session['current_candidates'] or session['current_index'] >= len(session['current_candidates']):
            self.vk.send_message(
                user_id,
                "❌ Нет текущего кандидата для добавления в черный список."
            )
            return
        
        candidate = session['current_candidates'][session['current_index']]
        
        if self.db.add_to_blacklist(user_id, candidate['id']):
            self.vk.send_message(
                user_id,
                f"🚫 {candidate['first_name']} добавлен(а) в черный список!"
            )
            
            # Переходим к следующему
            self._handle_next(user_id)
        else:
            self.vk.send_message(
                user_id,
                "❌ Не удалось добавить в черный список."
            )
    
    def run(self):
        """
        Запуск бота (основной цикл).
        В реальном проекте здесь будет Long Poll сервер.
        """
        print("✅ VKinder бот запущен и готов к работе!")
        
        # Здесь должен быть код для Long Poll сервера
        # Для примера просто имитируем работу
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Остановка бота...")
            self.stop()
    
    def stop(self):
        """Остановка бота и закрытие соединений"""
        print("🛑 Остановка VKinder бота...")
        self.db.close()
        self.vk.close()
        print("👋 До свидания!")


if __name__ == "__main__":
    bot = VKinderBot()
    bot.run()