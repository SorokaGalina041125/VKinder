"""
Модуль с моделями базы данных для SQLAlchemy.
Вынесен в отдельный файл для использования Alembic.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    ForeignKey, Table, Text, Float, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Создаем базовый класс для моделей
Base = declarative_base()

# Промежуточная таблица для связи пользователей и черного списка
blacklist_table = Table(
    'blacklist',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), primary_key=True),
    Column('blocked_user_id', Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now)
)

# Промежуточная таблица для связи пользователей и избранных
favorites_table = Table(
    'favorites',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), primary_key=True),
    Column('favorite_user_id', Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now)
)


class User(Base):
    """
    Модель пользователя VK.
    Хранит информацию о пользователе и его настройках.
    """
    __tablename__ = 'users'

    vk_id = Column(Integer, primary_key=True)  # ID пользователя ВКонтакте
    first_name = Column(String(100), nullable=False)  # Имя
    last_name = Column(String(100), nullable=False)  # Фамилия
    age = Column(Integer, nullable=True)  # Возраст
    city = Column(String(100), nullable=True)  # Город
    sex = Column(Integer, nullable=True)  # Пол (1 - женский, 2 - мужской)
    profile_url = Column(String(200), nullable=True)  # Ссылка на профиль
    created_at = Column(DateTime, default=datetime.now)  # Дата добавления в БД
    last_search_offset = Column(Integer, default=0)  # Смещение для пагинации при поиске
    is_active = Column(Boolean, default=True)  # Активен ли пользователь
    compatibility_rating = Column(Float, default=0.0)  # Средний рейтинг совместимости

    # Связи с другими таблицами
    search_criteria = relationship("SearchCriteria", back_populates="user", cascade="all, delete-orphan")
    viewed_users = relationship("ViewedUser", back_populates="user", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")
    search_logs = relationship("SearchLog", back_populates="user", cascade="all, delete-orphan")
    interests = relationship("UserInterest", back_populates="user", cascade="all, delete-orphan")
    
    # Черный список и избранное (многие ко многим)
    blacklist = relationship(
        "User", 
        secondary=blacklist_table,
        primaryjoin=vk_id == blacklist_table.c.user_id,
        secondaryjoin=vk_id == blacklist_table.c.blocked_user_id,
        backref="blocked_by"
    )
    
    favorites = relationship(
        "User", 
        secondary=favorites_table,
        primaryjoin=vk_id == favorites_table.c.user_id,
        secondaryjoin=vk_id == favorites_table.c.favorite_user_id,
        backref="favorited_by"
    )

    # Индексы для оптимизации поиска
    __table_args__ = (
        Index('idx_users_age', 'age'),
        Index('idx_users_city', 'city'),
        Index('idx_users_sex', 'sex'),
        Index('idx_users_active', 'is_active'),
    )


class SearchCriteria(Base):
    """
    Модель критериев поиска пользователя.
    Позволяет настраивать параметры для каждого пользователя индивидуально.
    """
    __tablename__ = 'search_criteria'

    id = Column(Integer, primary_key=True)
    user_vk_id = Column(Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Критерии поиска
    age_from = Column(Integer, default=18)  # Возраст от
    age_to = Column(Integer, default=45)  # Возраст до
    city = Column(String(100), nullable=True)  # Город для поиска
    sex = Column(Integer, nullable=True)  # Пол для поиска
    interests = Column(Text, nullable=True)  # Интересы (музыка, книги, группы)
    has_photos = Column(Boolean, default=True)  # Только с фото
    relation_status = Column(String(50), nullable=True)  # Статус отношений
    
    # Веса критериев (для рейтинга совместимости)
    age_weight = Column(Integer, default=10)  # Вес возраста
    city_weight = Column(Integer, default=8)  # Вес города
    interests_weight = Column(Integer, default=5)  # Вес интересов
    friends_weight = Column(Integer, default=3)  # Вес общих друзей
    photos_weight = Column(Integer, default=4)  # Вес фотографий
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="search_criteria")

    __table_args__ = (
        Index('idx_search_criteria_user', 'user_vk_id'),
        Index('idx_search_criteria_age', 'age_from', 'age_to'),
        Index('idx_search_criteria_city', 'city'),
    )


class ViewedUser(Base):
    """
    Модель для отслеживания просмотренных пользователей.
    Предотвращает повторный показ одних и тех же людей.
    """
    __tablename__ = 'viewed_users'

    id = Column(Integer, primary_key=True)
    user_vk_id = Column(Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), nullable=False)
    viewed_user_vk_id = Column(Integer, nullable=False)  # ID просмотренного пользователя
    viewed_at = Column(DateTime, default=datetime.now)  # Дата просмотра
    is_liked = Column(Boolean, default=False)  # Поставлен ли лайк
    is_favorite = Column(Boolean, default=False)  # В избранном
    is_blocked = Column(Boolean, default=False)  # В черном списке
    compatibility_score = Column(Integer, default=0)  # Оценка совместимости
    interaction_count = Column(Integer, default=1)  # Количество взаимодействий

    user = relationship("User", back_populates="viewed_users")
    
    # Составной индекс для быстрого поиска
    __table_args__ = (
        Index('idx_viewed_users_composite', 'user_vk_id', 'viewed_user_vk_id', unique=True),
        Index('idx_viewed_users_date', 'viewed_at'),
        Index('idx_viewed_users_favorite', 'user_vk_id', 'is_favorite'),
    )


class Photo(Base):
    """
    Модель для хранения информации о фотографиях пользователей.
    """
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True)
    user_vk_id = Column(Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), nullable=False)
    photo_id = Column(String(100), nullable=False)  # ID фото в VK
    owner_id = Column(Integer, nullable=False)  # ID владельца фото
    photo_url = Column(String(500), nullable=False)  # URL фото
    likes_count = Column(Integer, default=0)  # Количество лайков
    comments_count = Column(Integer, default=0)  # Количество комментариев
    reposts_count = Column(Integer, default=0)  # Количество репостов
    is_profile_photo = Column(Boolean, default=False)  # Аватарка или нет
    popularity_score = Column(Integer, default=0)  # Оценка популярности
    created_at = Column(DateTime, default=datetime.now)  # Дата загрузки фото
    
    user = relationship("User", back_populates="photos")
    
    # Индекс для быстрой сортировки по популярности
    __table_args__ = (
        Index('idx_photos_user', 'user_vk_id'),
        Index('idx_photos_popularity', 'user_vk_id', 'popularity_score'),
        Index('idx_photos_likes', 'likes_count'),
    )


class SearchLog(Base):
    """
    Модель для логирования поисковых запросов.
    Помогает анализировать эффективность поиска.
    """
    __tablename__ = 'search_logs'

    id = Column(Integer, primary_key=True)
    user_vk_id = Column(Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), nullable=False)
    search_params = Column(Text, nullable=True)  # Параметры поиска в JSON
    results_count = Column(Integer, default=0)  # Количество результатов
    execution_time = Column(Float, default=0.0)  # Время выполнения (сек)
    created_at = Column(DateTime, default=datetime.now)  # Дата поиска
    
    user = relationship("User", back_populates="search_logs")

    __table_args__ = (
        Index('idx_search_logs_user', 'user_vk_id'),
        Index('idx_search_logs_date', 'created_at'),
    )


class UserInterest(Base):
    """
    Модель для хранения интересов пользователя.
    Используется для анализа совместимости.
    """
    __tablename__ = 'user_interests'

    id = Column(Integer, primary_key=True)
    user_vk_id = Column(Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), nullable=False)
    interest_type = Column(String(50), nullable=False)  # music, books, movies, groups
    interest_value = Column(String(500), nullable=False)  # Название интереса
    weight = Column(Integer, default=1)  # Вес интереса
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="interests")
    
    # Индекс для быстрого поиска по интересам
    __table_args__ = (
        Index('idx_interests_user', 'user_vk_id'),
        Index('idx_interests_type', 'interest_type'),
        Index('idx_interests_value', 'interest_value'),
        Index('idx_interests_composite', 'interest_type', 'interest_value'),
    )


class CompatibilityScore(Base):
    """
    Модель для хранения оценок совместимости между пользователями.
    Позволяет быстро получать наиболее подходящих кандидатов.
    """
    __tablename__ = 'compatibility_scores'

    id = Column(Integer, primary_key=True)
    user_vk_id = Column(Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), nullable=False)
    candidate_vk_id = Column(Integer, nullable=False)
    score = Column(Integer, default=0)  # Общая оценка совместимости
    age_score = Column(Integer, default=0)  # Оценка по возрасту
    city_score = Column(Integer, default=0)  # Оценка по городу
    interests_score = Column(Integer, default=0)  # Оценка по интересам
    friends_score = Column(Integer, default=0)  # Оценка по общим друзьям
    photos_score = Column(Integer, default=0)  # Оценка по фотографиям
    calculated_at = Column(DateTime, default=datetime.now)  # Дата расчета
    
    __table_args__ = (
        Index('idx_compatibility_user', 'user_vk_id'),
        Index('idx_compatibility_score', 'user_vk_id', 'score'),
        Index('idx_compatibility_candidate', 'user_vk_id', 'candidate_vk_id', unique=True),
    )


class UserActivity(Base):
    """
    Модель для отслеживания активности пользователя в боте.
    """
    __tablename__ = 'user_activities'

    id = Column(Integer, primary_key=True)
    user_vk_id = Column(Integer, ForeignKey('users.vk_id', ondelete='CASCADE'), nullable=False)
    action_type = Column(String(50), nullable=False)  # search, view, favorite, blacklist, like
    target_id = Column(Integer, nullable=True)  # ID целевого пользователя (если применимо)
    action_data = Column(Text, nullable=True)  # Дополнительные данные в JSON
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index('idx_activity_user', 'user_vk_id'),
        Index('idx_activity_type', 'action_type'),
        Index('idx_activity_date', 'created_at'),
    )


class BotStatistics(Base):
    """
    Модель для хранения общей статистики бота.
    """
    __tablename__ = 'bot_statistics'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now, unique=True)  # Дата статистики
    total_users = Column(Integer, default=0)  # Всего пользователей
    active_users = Column(Integer, default=0)  # Активных пользователей
    total_searches = Column(Integer, default=0)  # Всего поисков
    total_views = Column(Integer, default=0)  # Всего просмотров
    total_favorites = Column(Integer, default=0)  # Всего добавлений в избранное
    total_blacklists = Column(Integer, default=0)  # Всего добавлений в черный список
    total_likes = Column(Integer, default=0)  # Всего лайков
    avg_compatibility = Column(Float, default=0.0)  # Средняя совместимость
    
    __table_args__ = (
        Index('idx_statistics_date', 'date'),
    )