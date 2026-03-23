"""
Провайдеры кандидатов для гибридного поиска
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from app.config import settings
from .vk_client import VKClient

logger = logging.getLogger(__name__)


class SearchMethod(Enum):
    API_FAST = "api_fast"
    API_DEEP = "api_deep"
    GROUPS = "groups"
    HYBRID = "hybrid"


@dataclass
class SearchContext:
    """Контекст поиска"""
    user_id: int
    criteria: any
    limit: int = 100
    exclude_viewed: bool = True
    exclude_blocked: bool = True


class BaseProvider(ABC):
    """Базовый класс для провайдеров кандидатов"""
    
    def __init__(self, vk_client: VKClient):
        self.vk = vk_client
    
    @abstractmethod
    def search(self, context: SearchContext) -> List[Dict]:
        pass
    
    @abstractmethod
    def get_method_name(self) -> str:
        pass


class ApiFastProvider(BaseProvider):
    """Быстрый поиск через users.search"""
    
    def search(self, context: SearchContext) -> List[Dict]:
        params = self._build_params(context)
        params['count'] = min(context.limit * 2, 100)
        
        try:
            result = self.vk.users_search(**params)
            return result.get('items', [])
        except Exception as e:
            logger.error(f"ApiFastProvider error: {e}")
            return []
    
    def get_method_name(self) -> str:
        return "API (быстрый)"
    
    def _build_params(self, context) -> Dict:
        params = {'has_photo': 1, 'fields': 'domain, bdate, city, sex'}
        
        if context.criteria.sex:
            params['sex'] = context.criteria.sex
        if context.criteria.age_from:
            params['age_from'] = context.criteria.age_from
        if context.criteria.age_to:
            params['age_to'] = context.criteria.age_to
        if context.criteria.city_id:
            params['city'] = context.criteria.city_id
        elif context.criteria.city:
            city_id = self.vk.get_city_id(context.criteria.city)
            if city_id:
                params['city'] = city_id
        
        return params


class ApiDeepProvider(BaseProvider):
    """Глубокий поиск через execute (ускорение в 25 раз)"""
    
    def search(self, context: SearchContext) -> List[Dict]:
        params = self._build_params(context)
        return self.vk.search_bulk(params, context.limit)
    
    def get_method_name(self) -> str:
        return "API (глубокий, execute)"
    
    def _build_params(self, context) -> Dict:
        params = {
            'has_photo': 1,
            'fields': 'domain, bdate, city, sex, books, interests, music',
        }
        
        if context.criteria.sex:
            params['sex'] = context.criteria.sex
        if context.criteria.age_from:
            params['age_from'] = context.criteria.age_from
        if context.criteria.age_to:
            params['age_to'] = context.criteria.age_to
        if context.criteria.city_id:
            params['city'] = context.criteria.city_id
        elif context.criteria.city:
            city_id = self.vk.get_city_id(context.criteria.city)
            if city_id:
                params['city'] = city_id
        
        return params


class GroupsProvider(BaseProvider):
    """Поиск через группы (обход лимита 1000)"""
    
    DATING_GROUPS = ['dating', 'znakomstva', 'love', 'relationship', 'vstrechi', 'newpeople']
    
    def __init__(self, vk_client: VKClient, db_session=None):
        super().__init__(vk_client)
        self.db = db_session
    
    def search(self, context: SearchContext) -> List[Dict]:
        logger.info(f"GroupsProvider: searching for user {context.user_id}")
        
        groups = self._get_target_groups(context)
        if not groups:
            return []
        
        members = self._collect_members(groups, context.limit)
        if not members:
            return []
        
        return self._get_candidates_data(members, context)
    
    def get_method_name(self) -> str:
        return "Группы"
    
    def _get_target_groups(self, context) -> List[int]:
        target_groups = set()
        
        # Группы пользователя
        for group in self.vk.get_groups(context.user_id):
            if group.get('members_count', 0) > 1000:
                target_groups.add(group['id'])
        
        # Популярные группы знакомств
        for group_name in self.DATING_GROUPS:
            try:
                search = self.vk.api.groups.search(
                    q=group_name,
                    type='group',
                    count=3
                )
                for group in search.get('items', []):
                    target_groups.add(group['id'])
            except Exception:
                pass
        
        return list(target_groups)[:10]
    
    def _collect_members(self, group_ids: List[int], limit: int) -> Set[int]:
        members = set()
        
        for group_id in group_ids:
            group_members = self.vk.get_group_members(group_id, min(1000, limit * 2))
            for member_id in group_members:
                members.add(member_id)
                if len(members) >= limit * 2:
                    break
            if len(members) >= limit * 2:
                break
        
        return members
    
    def _get_candidates_data(self, member_ids: Set[int], context) -> List[Dict]:
        candidates = []
        member_list = list(member_ids)
        
        for i in range(0, len(member_list), 1000):
            batch = member_list[i:i + 1000]
            users = self.vk.users_get(batch, 'domain, bdate, city, sex, is_closed')
            
            for user in users:
                if user.get('is_closed') or user['id'] == context.user_id:
                    continue
                if not self._matches_criteria(user, context):
                    continue
                candidates.append(user)
        
        return candidates
    
    def _matches_criteria(self, user: Dict, context) -> bool:
        if context.criteria.sex and user.get('sex') != context.criteria.sex:
            return False
        
        if context.criteria.age_from or context.criteria.age_to:
            age = self._parse_age(user.get('bdate'))
            if age is not None:
                if context.criteria.age_from and age < context.criteria.age_from:
                    return False
                if context.criteria.age_to and age > context.criteria.age_to:
                    return False
            # Если возраст не указан, пропускаем кандидата (можно изменить логику)
            else:
                return False
        
        if context.criteria.city:
            user_city = user.get('city', {}).get('title') if user.get('city') else None
            if user_city != context.criteria.city:
                return False
        
        return True
    
    def _parse_age(self, bdate: str) -> Optional[int]:
        """
        Парсинг возраста из даты рождения.
        Возвращает None, если возраст не может быть определен.
        """
        if not bdate:
            return None
        parts = bdate.split('.')
        if len(parts) == 3:
            try:
                year = int(parts[2])
                return datetime.now().year - year
            except (ValueError, IndexError):
                pass
        return None


class HybridProvider(BaseProvider):
    """Гибридный провайдер: комбинирует несколько методов"""
    
    def __init__(self, vk_client: VKClient, db_session=None):
        super().__init__(vk_client)
        self.providers = {
            SearchMethod.API_FAST: ApiFastProvider(vk_client),
            SearchMethod.API_DEEP: ApiDeepProvider(vk_client),
            SearchMethod.GROUPS: GroupsProvider(vk_client, db_session),
        }
    
    def search(self, context: SearchContext) -> List[Dict]:
        all_candidates = []
        seen_ids = set()
        
        # Стратегия в зависимости от нужного количества
        if context.limit <= 100:
            methods = [SearchMethod.API_FAST]
        elif context.limit <= 500:
            methods = [SearchMethod.API_FAST, SearchMethod.API_DEEP]
        else:
            methods = [SearchMethod.API_FAST, SearchMethod.API_DEEP, SearchMethod.GROUPS]
        
        for method in methods:
            if len(all_candidates) >= context.limit:
                break
            
            provider = self.providers[method]
            logger.info(f"Using {provider.get_method_name()}")
            
            remaining = context.limit - len(all_candidates)
            context_copy = SearchContext(
                user_id=context.user_id,
                criteria=context.criteria,
                limit=remaining * 2
            )
            
            candidates = provider.search(context_copy)
            
            for candidate in candidates:
                if candidate['id'] not in seen_ids:
                    seen_ids.add(candidate['id'])
                    all_candidates.append(candidate)
            
            logger.info(f"Added {len(candidates)} from {provider.get_method_name()}")
        
        return all_candidates[:context.limit]
    
    def get_method_name(self) -> str:
        return "Гибридный поиск"