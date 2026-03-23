"""
Модели базы данных VKinder
"""

from .user import User, SearchCriteria
from .viewed import ViewedUser
from .content import Photo, Like, UserInterest

__all__ = [
    'User',
    'SearchCriteria',
    'ViewedUser',
    'Photo',
    'Like',
    'UserInterest',
]