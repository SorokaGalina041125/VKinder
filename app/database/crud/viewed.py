# app/database/crud/viewed.py
"""
CRUD операции для просмотренных пользователей (включая избранное и ЧС)
"""
from sqlalchemy.orm import Session
from app.database.models import ViewedUser
import logging

logger = logging.getLogger(__name__)


def mark_as_viewed(db: Session, user_id: int, target_id: int) -> bool:
    """Отметка о просмотре анкеты"""
    existing = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        viewed_user_vk_id=target_id
    ).first()
    
    if not existing:
        viewed = ViewedUser(
            user_vk_id=user_id,
            viewed_user_vk_id=target_id
        )
        db.add(viewed)
        db.commit()
        logger.debug(f"Отмечен просмотр: {user_id} -> {target_id}")
        return True
    return False


# ========== ИЗБРАННОЕ ==========

def add_to_favorites(db: Session, user_id: int, candidate_id: int) -> bool:
    """Добавление кандидата в избранное"""
    viewed = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        viewed_user_vk_id=candidate_id
    ).first()
    
    if viewed:
        if viewed.is_favorite:
            return False
        viewed.is_favorite = True
    else:
        viewed = ViewedUser(
            user_vk_id=user_id,
            viewed_user_vk_id=candidate_id,
            is_favorite=True
        )
        db.add(viewed)
    
    db.commit()
    logger.info(f"Пользователь {user_id} добавил {candidate_id} в избранное")
    return True


def remove_from_favorites(db: Session, user_id: int, candidate_id: int) -> bool:
    """Удаление кандидата из избранного"""
    viewed = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        viewed_user_vk_id=candidate_id,
        is_favorite=True
    ).first()
    
    if viewed:
        viewed.is_favorite = False
        db.commit()
        logger.info(f"Пользователь {user_id} удалил {candidate_id} из избранного")
        return True
    return False


def get_user_favorites(db: Session, user_id: int) -> list:
    """Получение списка избранных кандидатов"""
    favorites = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        is_favorite=True
    ).all()
    return [f.viewed_user_vk_id for f in favorites]


def is_favorite(db: Session, user_id: int, candidate_id: int) -> bool:
    """Проверка, находится ли кандидат в избранном"""
    viewed = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        viewed_user_vk_id=candidate_id,
        is_favorite=True
    ).first()
    return viewed is not None


# ========== ЧЕРНЫЙ СПИСОК ==========

def add_to_blacklist(db: Session, user_id: int, candidate_id: int) -> bool:
    """Добавление кандидата в черный список"""
    viewed = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        viewed_user_vk_id=candidate_id
    ).first()
    
    if viewed:
        if viewed.is_blocked:
            return False
        viewed.is_blocked = True
    else:
        viewed = ViewedUser(
            user_vk_id=user_id,
            viewed_user_vk_id=candidate_id,
            is_blocked=True
        )
        db.add(viewed)
    
    db.commit()
    logger.info(f"Пользователь {user_id} добавил {candidate_id} в черный список")
    return True


def remove_from_blacklist(db: Session, user_id: int, candidate_id: int) -> bool:
    """Удаление кандидата из черного списка"""
    viewed = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        viewed_user_vk_id=candidate_id,
        is_blocked=True
    ).first()
    
    if viewed:
        viewed.is_blocked = False
        db.commit()
        logger.info(f"Пользователь {user_id} удалил {candidate_id} из черного списка")
        return True
    return False


def get_user_blacklist(db: Session, user_id: int) -> list:
    """Получение списка заблокированных кандидатов"""
    blacklist = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        is_blocked=True
    ).all()
    return [b.viewed_user_vk_id for b in blacklist]


def is_blocked(db: Session, user_id: int, candidate_id: int) -> bool:
    """Проверка, находится ли кандидат в черном списке"""
    viewed = db.query(ViewedUser).filter_by(
        user_vk_id=user_id,
        viewed_user_vk_id=candidate_id,
        is_blocked=True
    ).first()
    return viewed is not None


def get_viewed_ids(db: Session, user_id: int) -> set:
    """Получение ID всех просмотренных кандидатов"""
    viewed = db.query(ViewedUser.viewed_user_vk_id).filter_by(
        user_vk_id=user_id
    ).all()
    return {v[0] for v in viewed}