"""
Пакет с обработчиками сообщений бота
"""
from .router import router, RouteType
from .message import handle_message

__all__ = [
    'router',
    'RouteType',
    'handle_message',
]
