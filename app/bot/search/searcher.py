"""
Основной класс для поиска кандидатов
"""
import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session

from app.database.crud import (
    register_candidate,
    get_viewed_ids,
    get_user_blacklist,
    get_criteria,
    save_search_offset,
    get_user_photos,
    save_candidate_photos,
    save_user_interests,
)
from app.bot.logic.photos import sort_photos
from app.bot.logic.interests import collect_user_interests

from .vk_client import VKClient
from .provider import HybridProvider, SearchContext

logger = logging.getLogger(__name__)


class CandidateSearcher:
    """Поиск кандидатов с гибридной стратегией"""
    
    def __init__(self, db: Session, user_token: str = None):
        self.db = db
        self.vk = VKClient(user_token)
        self.provider = HybridProvider(self.vk, db)
    
    def search_batch(
        self,
        user_id: int,
        criteria,
        batch_size: int = 10
    ) -> Tuple[List, int]:
        """Поиск партии кандидатов"""
        logger.info(f"Searching batch for user {user_id}, batch_size={batch_size}")
        
        viewed_ids = get_viewed_ids(self.db, user_id)
        blocked_ids = get_user_blacklist(self.db, user_id)
        
        context = SearchContext(
            user_id=user_id,
            criteria=criteria,
            city_id=getattr(criteria, "city_id", None),
            limit=batch_size * 3,
            offset=getattr(criteria, 'search_offset', 0)
        )
        
        candidates_data = self.provider.search(context)
        
        if not candidates_data:
            return [], 0
        
        saved_candidates = []
        for data in candidates_data:
            if data['id'] in viewed_ids or data['id'] in blocked_ids:
                continue
            
            candidate = self._save_candidate(data)
            if candidate:
                saved_candidates.append(candidate)
            
            if len(saved_candidates) >= batch_size:
                break
        
        # Сохраняем offset
        if hasattr(criteria, 'search_offset'):
            save_search_offset(self.db, user_id, context.offset + len(candidates_data))
        
        return saved_candidates, max(0, len(candidates_data) - len(saved_candidates))
    
    def _save_candidate(self, data: dict):
        """
        Сохранение кандидата и его данных.
        Один commit в конце для атомарности операции.
        """
        try:
            # Сохраняем основную информацию
            candidate = register_candidate(self.db, data)
            self.db.flush()
            
            # Собираем и сохраняем фото
            photos = self.vk.get_photos(data['id'])
            if photos:
                top_photos = sort_photos(photos)
                save_candidate_photos(self.db, data['id'], top_photos)
            
            # Собираем и сохраняем интересы
            interests = collect_user_interests(self.vk, data['id'])
            if any(interests.values()):
                save_user_interests(self.db, data['id'], interests)
            
            # Один commit в конце
            self.db.commit()
            
            return candidate
            
        except Exception as e:
            logger.error(f"Error saving candidate {data.get('id')}: {e}", exc_info=True)
            self.db.rollback()
            return None
    
    def get_candidate_photos(self, candidate_id: int) -> str:
        """Получить фото кандидата для отправки"""
        return get_user_photos(self.db, candidate_id)
