"""
CRUD операции для пользователей и кандидатов
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func

from app.database.models import User
from app.database.crud.viewed import get_viewed_ids, get_user_blacklist
from app.database.crud.criteria import get_criteria
import logging

logger = logging.getLogger(__name__)


def get_or_create_user(db: Session, vk, vk_id: int) -> User:
    """Создание или получение пользователя бота"""
    user = db.get(User, vk_id)
    if not user:
        user_info = vk.users.get(user_ids=vk_id)[0]
        user = User(
            vk_id=vk_id,
            first_name=user_info.get('first_name', 'Пользователь'),
            last_name=user_info.get('last_name', 'ВК'),
            state="idle",
            is_bot_user=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Создан новый пользователь бота: {vk_id}")
    return user


def register_candidate(db: Session, item: dict) -> User:
    """Сохранение кандидата в базу данных"""
    candidate = db.get(User, item['id'])
    if not candidate:
        # Парсим возраст
        age = None
        bdate = item.get('bdate')
        if bdate:
            parts = bdate.split('.')
            if len(parts) == 3:
                try:
                    year = int(parts[2])
                    age = datetime.now().year - year
                except (ValueError, IndexError):
                    logger.debug(f"Не удалось распарсить дату рождения: {bdate} для {item['id']}")
            else:
                logger.debug(f"Дата рождения без года: {bdate} для {item['id']}")
        
        # Город
        city = None
        if item.get('city'):
            city = item['city'].get('title')
        
        # Ссылка
        domain = item.get('domain')
        profile_url = f"https://vk.com/{domain}" if domain else f"https://vk.com/id{item['id']}"
        
        candidate = User(
            vk_id=item['id'],
            first_name=item.get('first_name', 'Имя'),
            last_name=item.get('last_name', 'Фамилия'),
            profile_url=profile_url,
            sex=item.get('sex'),
            age=age,
            city=city,
            is_active=True,
            is_bot_user=False
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        logger.info(f"Сохранен кандидат: {candidate.first_name} {candidate.last_name}")
    
    return candidate


def get_next_candidate(db: Session, user_id: int) -> User:
    """
    Подбор следующего кандидата с учетом:
    - Критериев поиска
    - Просмотренных (ViewedUser)
    - Черного списка (is_blocked в ViewedUser)
    """
    # Получаем ID просмотренных и заблокированных
    viewed_ids = get_viewed_ids(db, user_id)
    blocked_ids = get_user_blacklist(db, user_id)
    
    # Получаем критерии поиска
    criteria = get_criteria(db, user_id)
    
    # Формируем запрос
    query = select(User).where(
        User.vk_id != user_id,
        User.is_active == True,
        User.is_bot_user == False,
        User.sex.isnot(None)
    )
    
    # Исключаем просмотренных
    if viewed_ids:
        query = query.where(User.vk_id.not_in(viewed_ids))
    
    # Исключаем заблокированных
    if blocked_ids:
        query = query.where(User.vk_id.not_in(blocked_ids))
    
    # Применяем фильтры по критериям
    if criteria:
        if criteria.sex:
            query = query.where(User.sex == criteria.sex)
        if criteria.age_from:
            query = query.where(User.age >= criteria.age_from)
        if criteria.age_to:
            # ИСПРАВЛЕНО: используем <= для включения верхней границы
            query = query.where(User.age <= criteria.age_to)
        if criteria.city:
            # ИСПРАВЛЕНО: сравнение без учета регистра
            query = query.where(func.lower(User.city) == func.lower(criteria.city))
    
    
    query = query.order_by(func.random())
    
    candidate = db.execute(query.limit(1)).scalar_one_or_none()
    
    if candidate:
        logger.info(f"Найден кандидат: {candidate.first_name} {candidate.last_name}")
    else:
        logger.info("Кандидатов не найдено")
    
    return candidate


def update_user_state(db: Session, vk_id: int, state: str):
    """Обновление статуса пользователя"""
    db.execute(update(User).where(User.vk_id == vk_id).values(state=state))
    db.commit()
    logger.debug(f"Обновлен статус пользователя {vk_id}: {state}")
