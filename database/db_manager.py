"""
Модуль для управления базой данных PostgreSQL.
Использует SQLAlchemy для ORM и работы с моделями.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, and_, or_, not_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Импортируем модели из отдельного файла
from .models import (
    Base, User, SearchCriteria, ViewedUser, Photo, 
    SearchLog, UserInterest, blacklist_table, favorites_table
)

# Загружаем переменные окружения
load_dotenv()


class DatabaseManager:
    """
    Класс для управления операциями с базой данных.
    Реализует паттерн Singleton для единственного экземпляра подключения.
    """
    
    _instance = None
    
    def __new__(cls):
        """Реализация Singleton паттерна"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Инициализация менеджера базы данных"""
        if self._initialized:
            return
            
        self._initialized = True
        self._engine = None
        self._Session = None
        self._connect_to_database()
    
    def _connect_to_database(self):
        """Установка соединения с базой данных"""
        try:
            # Получаем параметры подключения из переменных окружения
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'vkinder_db')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', '')
            
            # Формируем строку подключения
            connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            # Создаем движок SQLAlchemy
            self._engine = create_engine(
                connection_string,
                pool_size=10,  # Размер пула соединений
                max_overflow=20,  # Максимальное количество дополнительных соединений
                pool_pre_ping=True,  # Проверка соединения перед использованием
                echo=False  # Логировать SQL запросы (для отладки)
            )
            
            # Создаем фабрику сессий
            self._Session = sessionmaker(bind=self._engine)
            
            print("✅ Успешное подключение к базе данных")
            
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            raise
    
    @contextmanager
    def session_scope(self):
        """
        Контекстный менеджер для работы с сессией.
        Автоматически закрывает сессию после использования.
        """
        session = self._Session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ Ошибка базы данных: {e}")
            raise
        finally:
            session.close()
    
    def get_engine(self):
        """Получение движка SQLAlchemy (для Alembic)"""
        return self._engine
    
    def add_or_update_user(self, vk_id: int, first_name: str, last_name: str, 
                          age: int = None, city: str = None, sex: int = None,
                          profile_url: str = None) -> Optional[User]:
        """
        Добавление или обновление пользователя в базе данных.
        
        Args:
            vk_id: ID пользователя VK
            first_name: Имя
            last_name: Фамилия
            age: Возраст
            city: Город
            sex: Пол
            profile_url: Ссылка на профиль
            
        Returns:
            User: Объект пользователя или None если ошибка
        """
        try:
            with self.session_scope() as session:
                # Ищем существующего пользователя
                user = session.query(User).filter_by(vk_id=vk_id).first()
                
                if user:
                    # Обновляем существующего
                    user.first_name = first_name
                    user.last_name = last_name
                    if age is not None:
                        user.age = age
                    if city:
                        user.city = city
                    if sex is not None:
                        user.sex = sex
                    if profile_url:
                        user.profile_url = profile_url
                else:
                    # Создаем нового
                    user = User(
                        vk_id=vk_id,
                        first_name=first_name,
                        last_name=last_name,
                        age=age,
                        city=city,
                        sex=sex,
                        profile_url=profile_url
                    )
                    session.add(user)
                
                return user
                
        except Exception as e:
            print(f"❌ Ошибка при добавлении пользователя: {e}")
            return None
    
    def get_user(self, vk_id: int) -> Optional[User]:
        """
        Получение пользователя по VK ID.
        
        Args:
            vk_id: ID пользователя VK
            
        Returns:
            User или None если не найден
        """
        try:
            with self.session_scope() as session:
                return session.query(User).filter_by(vk_id=vk_id).first()
        except Exception as e:
            print(f"❌ Ошибка при получении пользователя: {e}")
            return None
    
    def get_or_create_user(self, vk_id: int, first_name: str = None, 
                          last_name: str = None) -> Optional[User]:
        """
        Получение существующего пользователя или создание нового.
        
        Args:
            vk_id: ID пользователя
            first_name: Имя (для создания)
            last_name: Фамилия (для создания)
            
        Returns:
            User: Объект пользователя
        """
        user = self.get_user(vk_id)
        if user:
            return user
        
        if first_name and last_name:
            return self.add_or_update_user(
                vk_id=vk_id,
                first_name=first_name,
                last_name=last_name
            )
        
        return None
    
    def add_to_favorites(self, user_vk_id: int, favorite_vk_id: int) -> bool:
        """
        Добавление пользователя в избранное.
        
        Args:
            user_vk_id: ID пользователя, который добавляет
            favorite_vk_id: ID добавляемого пользователя
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                favorite = session.query(User).filter_by(vk_id=favorite_vk_id).first()
                
                if user and favorite and favorite not in user.favorites:
                    user.favorites.append(favorite)
                    
                    # Обновляем запись в просмотренных
                    viewed = session.query(ViewedUser).filter_by(
                        user_vk_id=user_vk_id,
                        viewed_user_vk_id=favorite_vk_id
                    ).first()
                    if viewed:
                        viewed.is_favorite = True
                    
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при добавлении в избранное: {e}")
            return False
    
    def remove_from_favorites(self, user_vk_id: int, favorite_vk_id: int) -> bool:
        """
        Удаление пользователя из избранного.
        
        Args:
            user_vk_id: ID пользователя, который удаляет
            favorite_vk_id: ID удаляемого пользователя
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                favorite = session.query(User).filter_by(vk_id=favorite_vk_id).first()
                
                if user and favorite and favorite in user.favorites:
                    user.favorites.remove(favorite)
                    
                    # Обновляем запись в просмотренных
                    viewed = session.query(ViewedUser).filter_by(
                        user_vk_id=user_vk_id,
                        viewed_user_vk_id=favorite_vk_id
                    ).first()
                    if viewed:
                        viewed.is_favorite = False
                    
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при удалении из избранного: {e}")
            return False
    
    def add_to_blacklist(self, user_vk_id: int, blocked_vk_id: int) -> bool:
        """
        Добавление пользователя в черный список.
        
        Args:
            user_vk_id: ID пользователя, который добавляет
            blocked_vk_id: ID добавляемого в черный список
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                blocked = session.query(User).filter_by(vk_id=blocked_vk_id).first()
                
                if user and blocked and blocked not in user.blacklist:
                    user.blacklist.append(blocked)
                    
                    # Обновляем запись в просмотренных
                    viewed = session.query(ViewedUser).filter_by(
                        user_vk_id=user_vk_id,
                        viewed_user_vk_id=blocked_vk_id
                    ).first()
                    if viewed:
                        viewed.is_blocked = True
                    
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при добавлении в черный список: {e}")
            return False
    
    def remove_from_blacklist(self, user_vk_id: int, blocked_vk_id: int) -> bool:
        """
        Удаление пользователя из черного списка.
        
        Args:
            user_vk_id: ID пользователя
            blocked_vk_id: ID удаляемого из черного списка
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                blocked = session.query(User).filter_by(vk_id=blocked_vk_id).first()
                
                if user and blocked and blocked in user.blacklist:
                    user.blacklist.remove(blocked)
                    
                    # Обновляем запись в просмотренных
                    viewed = session.query(ViewedUser).filter_by(
                        user_vk_id=user_vk_id,
                        viewed_user_vk_id=blocked_vk_id
                    ).first()
                    if viewed:
                        viewed.is_blocked = False
                    
                    return True
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при удалении из черного списка: {e}")
            return False
    
    def add_viewed_user(self, user_vk_id: int, viewed_vk_id: int, 
                       compatibility_score: int = 0) -> bool:
        """
        Добавление пользователя в список просмотренных.
        
        Args:
            user_vk_id: ID пользователя, который просматривает
            viewed_vk_id: ID просматриваемого пользователя
            compatibility_score: Оценка совместимости
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            with self.session_scope() as session:
                # Проверяем, есть ли уже запись
                viewed = session.query(ViewedUser).filter_by(
                    user_vk_id=user_vk_id,
                    viewed_user_vk_id=viewed_vk_id
                ).first()
                
                if viewed:
                    # Обновляем существующую запись
                    viewed.viewed_at = datetime.now()
                    viewed.compatibility_score = compatibility_score
                    viewed.interaction_count += 1
                else:
                    # Создаем новую запись
                    viewed = ViewedUser(
                        user_vk_id=user_vk_id,
                        viewed_user_vk_id=viewed_vk_id,
                        compatibility_score=compatibility_score
                    )
                    session.add(viewed)
                
                return True
                
        except Exception as e:
            print(f"❌ Ошибка при добавлении просмотренного пользователя: {e}")
            return False
    
    def is_viewed(self, user_vk_id: int, viewed_vk_id: int) -> bool:
        """
        Проверка, просматривал ли пользователь данного человека.
        
        Args:
            user_vk_id: ID пользователя
            viewed_vk_id: ID проверяемого пользователя
            
        Returns:
            bool: True если просматривал, False если нет
        """
        try:
            with self.session_scope() as session:
                return session.query(ViewedUser).filter_by(
                    user_vk_id=user_vk_id,
                    viewed_user_vk_id=viewed_vk_id
                ).first() is not None
        except Exception as e:
            print(f"❌ Ошибка при проверке просмотра: {e}")
            return False
    
    def is_blacklisted(self, user_vk_id: int, check_vk_id: int) -> bool:
        """
        Проверка, находится ли пользователь в черном списке.
        
        Args:
            user_vk_id: ID пользователя
            check_vk_id: ID проверяемого пользователя
            
        Returns:
            bool: True если в черном списке, False если нет
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                if user:
                    check_user = session.query(User).filter_by(vk_id=check_vk_id).first()
                    return check_user in user.blacklist if check_user else False
                return False
        except Exception as e:
            print(f"❌ Ошибка при проверке черного списка: {e}")
            return False
    
    def get_favorites(self, user_vk_id: int) -> List[User]:
        """
        Получение списка избранных пользователей.
        
        Args:
            user_vk_id: ID пользователя
            
        Returns:
            List[User]: Список избранных пользователей
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                return user.favorites if user else []
        except Exception as e:
            print(f"❌ Ошибка при получении избранных: {e}")
            return []
    
    def get_blacklist(self, user_vk_id: int) -> List[User]:
        """
        Получение списка пользователей в черном списке.
        
        Args:
            user_vk_id: ID пользователя
            
        Returns:
            List[User]: Список пользователей в черном списке
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                return user.blacklist if user else []
        except Exception as e:
            print(f"❌ Ошибка при получении черного списка: {e}")
            return []
    
    def save_search_criteria(self, user_vk_id: int, criteria: Dict) -> bool:
        """
        Сохранение критериев поиска для пользователя.
        
        Args:
            user_vk_id: ID пользователя
            criteria: Словарь с критериями поиска
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            with self.session_scope() as session:
                # Проверяем, есть ли уже критерии
                search_criteria = session.query(SearchCriteria).filter_by(
                    user_vk_id=user_vk_id
                ).first()
                
                if search_criteria:
                    # Обновляем существующие
                    for key, value in criteria.items():
                        if hasattr(search_criteria, key):
                            setattr(search_criteria, key, value)
                else:
                    # Создаем новые
                    search_criteria = SearchCriteria(
                        user_vk_id=user_vk_id,
                        **criteria
                    )
                    session.add(search_criteria)
                
                return True
                
        except Exception as e:
            print(f"❌ Ошибка при сохранении критериев: {e}")
            return False
    
    def get_search_criteria(self, user_vk_id: int) -> Optional[SearchCriteria]:
        """
        Получение критериев поиска для пользователя.
        
        Args:
            user_vk_id: ID пользователя
            
        Returns:
            SearchCriteria или None если не найдены
        """
        try:
            with self.session_scope() as session:
                return session.query(SearchCriteria).filter_by(
                    user_vk_id=user_vk_id
                ).first()
        except Exception as e:
            print(f"❌ Ошибка при получении критериев: {e}")
            return None
    
    def update_search_offset(self, user_vk_id: int, offset: int) -> bool:
        """
        Обновление смещения поиска для пагинации.
        
        Args:
            user_vk_id: ID пользователя
            offset: Новое значение смещения
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                if user:
                    user.last_search_offset = offset
                    return True
                return False
        except Exception as e:
            print(f"❌ Ошибка при обновлении смещения: {e}")
            return False
    
    def save_photos(self, user_vk_id: int, photos: List[Dict]) -> bool:
        """
        Сохранение фотографий пользователя.
        
        Args:
            user_vk_id: ID пользователя
            photos: Список словарей с информацией о фото
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            with self.session_scope() as session:
                # Проверяем существование пользователя
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                if not user:
                    return False
                
                # Удаляем старые фото
                session.query(Photo).filter_by(user_vk_id=user_vk_id).delete()
                
                # Добавляем новые
                for photo_data in photos:
                    popularity = (photo_data.get('likes', 0) + 
                                 photo_data.get('comments', 0) * 2 +
                                 photo_data.get('reposts', 0) * 3)
                    
                    photo = Photo(
                        user_vk_id=user_vk_id,
                        photo_id=str(photo_data.get('id')),
                        owner_id=photo_data.get('owner_id', user_vk_id),
                        photo_url=photo_data.get('url', ''),
                        likes_count=photo_data.get('likes', 0),
                        comments_count=photo_data.get('comments', 0),
                        reposts_count=photo_data.get('reposts', 0),
                        is_profile_photo=photo_data.get('is_profile', False),
                        popularity_score=popularity
                    )
                    session.add(photo)
                
                return True
                
        except Exception as e:
            print(f"❌ Ошибка при сохранении фото: {e}")
            return False
    
    def get_photos(self, user_vk_id: int, limit: int = 3) -> List[Photo]:
        """
        Получение фотографий пользователя.
        
        Args:
            user_vk_id: ID пользователя
            limit: Количество фотографий
            
        Returns:
            List[Photo]: Список фотографий
        """
        try:
            with self.session_scope() as session:
                return session.query(Photo)\
                    .filter_by(user_vk_id=user_vk_id)\
                    .order_by(Photo.popularity_score.desc())\
                    .limit(limit)\
                    .all()
        except Exception as e:
            print(f"❌ Ошибка при получении фото: {e}")
            return []
    
    def log_search(self, user_vk_id: int, search_params: Dict, 
                   results_count: int, execution_time: float) -> bool:
        """
        Логирование поискового запроса.
        
        Args:
            user_vk_id: ID пользователя
            search_params: Параметры поиска
            results_count: Количество результатов
            execution_time: Время выполнения
            
        Returns:
            bool: True если успешно
        """
        try:
            with self.session_scope() as session:
                log = SearchLog(
                    user_vk_id=user_vk_id,
                    search_params=json.dumps(search_params, ensure_ascii=False),
                    results_count=results_count,
                    execution_time=execution_time
                )
                session.add(log)
                return True
        except Exception as e:
            print(f"❌ Ошибка при логировании поиска: {e}")
            return False
    
    def save_user_interests(self, user_vk_id: int, interests: List[Dict]) -> bool:
        """
        Сохранение интересов пользователя.
        
        Args:
            user_vk_id: ID пользователя
            interests: Список интересов с типами
            
        Returns:
            bool: True если успешно
        """
        try:
            with self.session_scope() as session:
                # Удаляем старые интересы
                session.query(UserInterest).filter_by(user_vk_id=user_vk_id).delete()
                
                # Добавляем новые
                for interest in interests:
                    user_interest = UserInterest(
                        user_vk_id=user_vk_id,
                        interest_type=interest.get('type'),
                        interest_value=interest.get('value'),
                        weight=interest.get('weight', 1)
                    )
                    session.add(user_interest)
                
                return True
        except Exception as e:
            print(f"❌ Ошибка при сохранении интересов: {e}")
            return False
    
    def get_user_interests(self, user_vk_id: int, interest_type: str = None) -> List[UserInterest]:
        """
        Получение интересов пользователя.
        
        Args:
            user_vk_id: ID пользователя
            interest_type: Тип интереса (опционально)
            
        Returns:
            List[UserInterest]: Список интересов
        """
        try:
            with self.session_scope() as session:
                query = session.query(UserInterest).filter_by(user_vk_id=user_vk_id)
                if interest_type:
                    query = query.filter_by(interest_type=interest_type)
                return query.all()
        except Exception as e:
            print(f"❌ Ошибка при получении интересов: {e}")
            return []
    
    def get_unviewed_users(self, user_vk_id: int, candidates: List[int]) -> List[int]:
        """
        Фильтрация списка кандидатов, оставляя только непросмотренных.
        
        Args:
            user_vk_id: ID пользователя
            candidates: Список ID кандидатов
            
        Returns:
            List[int]: Список непросмотренных ID
        """
        try:
            with self.session_scope() as session:
                # Получаем просмотренных
                viewed = session.query(ViewedUser.viewed_user_vk_id)\
                    .filter_by(user_vk_id=user_vk_id)\
                    .all()
                viewed_ids = {v[0] for v in viewed}
                
                # Получаем черный список
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                blacklist_ids = {u.vk_id for u in user.blacklist} if user else set()
                
                # Фильтруем
                return [c for c in candidates 
                       if c not in viewed_ids and c not in blacklist_ids]
        except Exception as e:
            print(f"❌ Ошибка при фильтрации просмотренных: {e}")
            return candidates
    
    def get_user_statistics(self, user_vk_id: int) -> Dict:
        """
        Получение статистики для пользователя.
        
        Args:
            user_vk_id: ID пользователя
            
        Returns:
            Dict: Статистика
        """
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(vk_id=user_vk_id).first()
                if not user:
                    return {}
                
                viewed_count = session.query(ViewedUser)\
                    .filter_by(user_vk_id=user_vk_id)\
                    .count()
                
                favorites_count = len(user.favorites)
                blacklist_count = len(user.blacklist)
                
                search_logs = session.query(SearchLog)\
                    .filter_by(user_vk_id=user_vk_id)\
                    .order_by(SearchLog.created_at.desc())\
                    .limit(10)\
                    .all()
                
                return {
                    'viewed_count': viewed_count,
                    'favorites_count': favorites_count,
                    'blacklist_count': blacklist_count,
                    'last_searches': [
                        {
                            'params': json.loads(log.search_params) if log.search_params else {},
                            'results': log.results_count,
                            'time': log.execution_time,
                            'created_at': log.created_at
                        }
                        for log in search_logs
                    ]
                }
        except Exception as e:
            print(f"❌ Ошибка при получении статистики: {e}")
            return {}
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self._engine:
            self._engine.dispose()
            print("🔌 Соединение с базой данных закрыто")