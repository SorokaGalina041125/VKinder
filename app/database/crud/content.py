"""
CRUD операции для контента: фото, лайки, интересы
"""
from sqlalchemy.orm import Session
from app.database.models.content import Photo, Like, UserInterest
import logging

logger = logging.getLogger(__name__)


# ========== ФОТО ==========

def save_candidate_photos(db: Session, owner_id: int, top_photos: list):
    """Сохранение топ-3 фотографий кандидата (bulk insert)"""
    db.query(Photo).filter(Photo.owner_id == owner_id).delete()
    
    photos_to_add = []
    for photo in top_photos:
        likes = photo.get('likes', {}).get('count', 0)
        comments = photo.get('comments', {}).get('count', 0)
        photo_url = f"https://vk.com/photo{owner_id}_{photo['id']}"
        
        new_photo = Photo(
            user_vk_id=owner_id,
            photo_id=str(photo['id']),
            owner_id=owner_id,
            photo_url=photo_url,
            likes_count=likes,
            comments_count=comments,
            is_profile_photo=True,
            popularity_score=likes + comments
        )
        photos_to_add.append(new_photo)
    
    if photos_to_add:
        db.add_all(photos_to_add)
        db.commit()
        logger.debug(f"Сохранено {len(photos_to_add)} фото для {owner_id}")


def get_user_photos(db: Session, target_vk_id: int) -> str:
    """Формирование строки вложений для отправки в ВК"""
    photos = db.query(Photo).filter(Photo.owner_id == target_vk_id).all()
    if photos:
        return ",".join([f"photo{p.owner_id}_{p.photo_id}" for p in photos])
    return ""


# ========== ЛАЙКИ ==========

def add_like(db: Session, user_id: int, photo_owner_id: int, photo_id: str) -> bool:
    """Добавление лайка на фото"""
    existing = db.query(Like).filter_by(
        user_vk_id=user_id,
        photo_owner_id=photo_owner_id,
        photo_id=photo_id
    ).first()
    
    if not existing:
        like = Like(
            user_vk_id=user_id,
            photo_owner_id=photo_owner_id,
            photo_id=photo_id
        )
        db.add(like)
        db.commit()
        logger.info(f"Пользователь {user_id} лайкнул фото {photo_owner_id}_{photo_id}")
        return True
    return False


def remove_like(db: Session, user_id: int, photo_owner_id: int, photo_id: str) -> bool:
    """Удаление лайка с фото"""
    like = db.query(Like).filter_by(
        user_vk_id=user_id,
        photo_owner_id=photo_owner_id,
        photo_id=photo_id
    ).first()
    
    if like:
        db.delete(like)
        db.commit()
        logger.info(f"Пользователь {user_id} убрал лайк с фото {photo_owner_id}_{photo_id}")
        return True
    return False


def has_liked(db: Session, user_id: int, photo_owner_id: int, photo_id: str) -> bool:
    """Проверка, лайкнул ли пользователь фото"""
    like = db.query(Like).filter_by(
        user_vk_id=user_id,
        photo_owner_id=photo_owner_id,
        photo_id=photo_id
    ).first()
    return like is not None


# ========== ИНТЕРЕСЫ ==========

def save_user_interests(db: Session, user_vk_id: int, interests: dict):
    """Сохранение интересов пользователя (bulk insert)"""
    # Удаляем старые интересы
    db.query(UserInterest).filter(UserInterest.user_vk_id == user_vk_id).delete()
    
    interests_to_add = []
    
    for music in interests.get('music', []):
        interest = UserInterest(
            user_vk_id=user_vk_id,
            interest_type='music',
            interest_value=music
        )
        interests_to_add.append(interest)
    
    for book in interests.get('books', []):
        interest = UserInterest(
            user_vk_id=user_vk_id,
            interest_type='books',
            interest_value=book
        )
        interests_to_add.append(interest)
    
    for group in interests.get('groups', []):
        if isinstance(group, dict):
            group_name = group.get('name', '')
            group_id = str(group.get('id', ''))
        else:
            group_name = str(group)
            group_id = None
        
        interest = UserInterest(
            user_vk_id=user_vk_id,
            interest_type='groups',
            interest_value=group_name,
            interest_source_id=group_id
        )
        interests_to_add.append(interest)
    
    if interests_to_add:
        db.add_all(interests_to_add)
        db.commit()
        logger.info(f"Сохранены интересы для пользователя {user_vk_id}")


def get_user_interests(db: Session, user_vk_id: int) -> dict:
    """Получение интересов пользователя"""
    interests = db.query(UserInterest).filter(
        UserInterest.user_vk_id == user_vk_id
    ).all()
    
    result = {'music': [], 'books': [], 'groups': []}
    for interest in interests:
        result[interest.interest_type].append(interest.interest_value)
    
    return result


def calculate_interest_overlap(db: Session, user_id: int, candidate_id: int) -> dict:
    """Вычисление пересечений по интересам"""
    user_interests = get_user_interests(db, user_id)
    candidate_interests = get_user_interests(db, candidate_id)
    
    overlap = {'music': 0, 'books': 0, 'groups': 0, 'total': 0}
    
    user_music = set(user_interests['music'])
    candidate_music = set(candidate_interests['music'])
    overlap['music'] = len(user_music & candidate_music)
    
    user_books = set(user_interests['books'])
    candidate_books = set(candidate_interests['books'])
    overlap['books'] = len(user_books & candidate_books)
    
    user_groups = set(user_interests['groups'])
    candidate_groups = set(candidate_interests['groups'])
    overlap['groups'] = len(user_groups & candidate_groups)
    
    overlap['total'] = overlap['music'] + overlap['books'] + overlap['groups']
    
    return overlap