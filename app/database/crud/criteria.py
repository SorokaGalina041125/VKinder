"""
CRUD операции для критериев поиска
"""
from sqlalchemy.orm import Session
from app.database.models import SearchCriteria
import logging

logger = logging.getLogger(__name__)


def get_criteria(db: Session, user_id: int) -> SearchCriteria:
    """Получение критериев поиска пользователя"""
    return db.query(SearchCriteria).filter_by(user_vk_id=user_id).first()


def update_criteria(db: Session, user_id: int, **kwargs) -> SearchCriteria:
    """
    Универсальное обновление критериев.
    
    Примеры:
        update_criteria(db, user_id, sex=1)
        update_criteria(db, user_id, age_from=18, age_to=35)
        update_criteria(db, user_id, city="Москва", city_id=1)
    """
    criteria = get_criteria(db, user_id)
    
    if not criteria:
        criteria = SearchCriteria(user_vk_id=user_id)
        db.add(criteria)
    
    for key, value in kwargs.items():
        if hasattr(criteria, key):
            setattr(criteria, key, value)
            logger.debug(f"Updated {key}={value} for user {user_id}")
    
    db.commit()
    db.refresh(criteria)
    return criteria


def reset_criteria(db: Session, user_id: int) -> None:
    """Сбросить все критерии"""
    criteria = get_criteria(db, user_id)
    if criteria:
        db.delete(criteria)
        db.commit()
        logger.info(f"Criteria reset for user {user_id}")


def get_search_offset(db: Session, user_id: int) -> int:
    """Получение позиции поиска для пагинации"""
    criteria = get_criteria(db, user_id)
    if criteria:
        return criteria.search_offset or 0
    return 0


def save_search_offset(db: Session, user_id: int, offset: int) -> None:
    """Сохранение позиции поиска для пагинации"""
    criteria = get_criteria(db, user_id)
    if criteria:
        criteria.search_offset = offset
        db.commit()
        logger.debug(f"Saved offset {offset} for user {user_id}")