"""
Модуль для ранжирования и взвешенной оценки кандидатов.
"""
import logging
from typing import List, Dict
from sqlalchemy.orm import Session

from app.config import settings
from app.database.crud.content import calculate_interest_overlap
from .interests import get_interest_weight

logger = logging.getLogger(__name__)

# Веса из конфига (требование 12)
WEIGHTS = {
    'age': settings.SCORE_AGE_WEIGHT,
    'interests': settings.SCORE_INTERESTS_WEIGHT,
    'city': settings.SCORE_CITY_WEIGHT,
    'friends': settings.SCORE_FRIENDS_WEIGHT,
}


def calculate_age_score(criteria, candidate_age: int) -> float:
    """Оценка соответствия возраста (0-1)"""
    if not criteria.age_from or not criteria.age_to or not candidate_age:
        return 0.0
    
    age_range = criteria.age_to - criteria.age_from
    if age_range == 0:
        return 1.0 if candidate_age == criteria.age_from else 0.0
    
    ideal_age = (criteria.age_from + criteria.age_to) / 2
    age_diff = abs(candidate_age - ideal_age)
    return max(0, 1 - (age_diff / age_range))


def calculate_city_score(criteria, candidate_city: str) -> float:
    """Оценка города (0 или 1)"""
    if not criteria.city or not candidate_city:
        return 0.0
    return 1.0 if candidate_city == criteria.city else 0.0


def calculate_interests_score(db: Session, user_id: int, candidate_id: int) -> float:
    """Оценка совпадения интересов (0-1)"""
    overlap = calculate_interest_overlap(db, user_id, candidate_id)
    
    if not overlap or overlap['total'] == 0:
        return 0.0
    
    total_score = 0.0
    max_possible = 0.0
    
    for interest_type in ['groups', 'music', 'books']:
        count = overlap.get(interest_type, 0)
        weight = get_interest_weight(interest_type)
        total_score += count * weight
        max_possible += 10 * weight
    
    return min(total_score / max_possible, 1.0) if max_possible > 0 else 0.0


def calculate_friends_score(db: Session, user_id: int, candidate_id: int) -> float:
    """Оценка общих друзей (заглушка)"""
    return 0.0


def calculate_candidate_score(db: Session, user_id: int, candidate, criteria) -> float:
    """Вычисление общего скора кандидата (0-1)"""
    total_score = 0.0
    
    age_score = calculate_age_score(criteria, candidate.age)
    total_score += age_score * WEIGHTS['age']
    
    city_score = calculate_city_score(criteria, candidate.city)
    total_score += city_score * WEIGHTS['city']
    
    interests_score = calculate_interests_score(db, user_id, candidate.vk_id)
    total_score += interests_score * WEIGHTS['interests']
    
    friends_score = calculate_friends_score(db, user_id, candidate.vk_id)
    total_score += friends_score * WEIGHTS['friends']
    
    return total_score


def rank_candidates(db: Session, user_id: int, candidates: List, criteria) -> List:
    """Ранжирование кандидатов по убыванию скора"""
    if not candidates:
        return []
    
    scored_candidates = []
    
    for candidate in candidates:
        try:
            score = calculate_candidate_score(db, user_id, candidate, criteria)
            scored_candidates.append((candidate, score))
        except Exception as e:
            logger.error(f"Ошибка расчета скора для {candidate.vk_id}: {e}")
            scored_candidates.append((candidate, 0.0))
    
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    for i, (cand, score) in enumerate(scored_candidates[:3], 1):
        logger.info(f"Топ-{i}: {cand.first_name} {cand.last_name} (скор: {score:.2f})")
    
    return [cand for cand, _ in scored_candidates]


def get_top_candidates(db: Session, user_id: int, candidates: List, criteria, limit: int = 10) -> List:
    """
    Обертка для совместимости с тестами и другими модулями.
    Возвращает топ-N кандидатов после ранжирования.
    """
    ranked = rank_candidates(db, user_id, candidates, criteria)
    return ranked[:limit]


def explain_score(db: Session, user_id: int, candidate, criteria) -> str:
    """
    Заглушка для описания того, почему кандидат подходит.
    Возвращает текстовое пояснение оценки совместимости.
    """
    try:
        score = calculate_candidate_score(db, user_id, candidate, criteria)
        
        # Разбиваем оценку по компонентам для пояснения
        age_score = calculate_age_score(criteria, candidate.age) if hasattr(candidate, 'age') else 0
        city_score = calculate_city_score(criteria, candidate.city) if hasattr(candidate, 'city') else 0
        interests_score = calculate_interests_score(db, user_id, candidate.vk_id)
        friends_score = calculate_friends_score(db, user_id, candidate.vk_id)
        
        parts = []
        if age_score > 0:
            parts.append(f"возраст подходит ({age_score:.0%})")
        if city_score > 0:
            parts.append(f"город совпадает")
        if interests_score > 0:
            parts.append(f"общие интересы ({interests_score:.0%})")
        if friends_score > 0:
            parts.append(f"общие друзья ({friends_score:.0%})")
        
        if parts:
            return f"✅ Кандидат хорошо подходит: {', '.join(parts)}"
        else:
            return "ℹ️ Кандидат подобран по основным критериям (пол, возраст, город)"
            
    except Exception as e:
        logger.error(f"Ошибка при формировании пояснения: {e}")
        return "⚠️ Оценка совместимости временно недоступна"