"""
CRUD операции для работы с базой данных.
"""

# Пользователи
from .user import (
    get_or_create_user,
    register_candidate,
    update_user_state
)

# Просмотры, избранное, черный список
from .viewed import (
    mark_as_viewed,
    add_to_favorites,
    remove_from_favorites,
    get_user_favorites,
    is_favorite,
    add_to_blacklist,
    remove_from_blacklist,
    get_user_blacklist,
    is_blocked,
    get_viewed_ids
)

# Контент: фото, лайки, интересы
from .content import (
    save_candidate_photos,
    get_user_photos,
    add_like,
    remove_like,
    has_liked,
    save_user_interests,
    get_user_interests,
    calculate_interest_overlap
)

# Критерии поиска
from .criteria import (
    get_criteria,
    update_criteria,
    reset_criteria,
    get_search_offset,
    save_search_offset
)

__all__ = [
    # User
    'get_or_create_user',
    'register_candidate',
    'update_user_state',
    
    # Viewed
    'mark_as_viewed',
    'add_to_favorites',
    'remove_from_favorites',
    'get_user_favorites',
    'is_favorite',
    'add_to_blacklist',
    'remove_from_blacklist',
    'get_user_blacklist',
    'is_blocked',
    'get_viewed_ids',
    
    # Content
    'save_candidate_photos',
    'get_user_photos',
    'add_like',
    'remove_like',
    'has_liked',
    'save_user_interests',
    'get_user_interests',
    'calculate_interest_overlap',
    
    # Criteria
    'get_criteria',
    'update_criteria',
    'reset_criteria',
    'get_search_offset',
    'save_search_offset',
]