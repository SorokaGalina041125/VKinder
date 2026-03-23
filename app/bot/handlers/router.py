"""
Маршрутизатор сообщений вместо огромного if-elif в message.py
"""
import logging
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum

from app.bot.utils import send_msg
from app.bot.handlers.unknown import handle_unknown

logger = logging.getLogger(__name__)


class RouteType(Enum):
    """Типы маршрутов"""
    TEXT = "text"          # Текстовые команды
    STATE = "state"        # Состояния FSM
    PAYLOAD = "payload"    # Payload из кнопок


@dataclass
class Route:
    """Маршрут для обработки сообщения"""
    name: str
    handler: Callable
    route_type: RouteType
    condition: str
    priority: int = 0
    description: str = ""
    exact_match: bool = True  # Для TEXT: True = точное совпадение, False = startswith


class Router:
    """
    Маршрутизатор сообщений.
    
    Регистрирует обработчики по типу (текст/состояние/payload)
    и вызывает подходящий при получении сообщения.
    """
    
    def __init__(self):
        self.routes: Dict[RouteType, list] = {
            RouteType.TEXT: [],
            RouteType.STATE: [],
            RouteType.PAYLOAD: [],
        }
    
    def register(
        self, 
        route_type: RouteType, 
        condition: str, 
        priority: int = 0, 
        description: str = "",
        exact_match: bool = True
    ):
        """
        Декоратор для регистрации обработчика.
        
        Args:
            route_type: тип маршрута (TEXT, STATE, PAYLOAD)
            condition: условие (текст команды, имя состояния, тип payload)
            priority: приоритет (чем выше, тем раньше проверяется)
            description: описание для отладки
            exact_match: для TEXT: True = точное совпадение, False = startswith
        """
        def decorator(handler):
            route = Route(
                name=handler.__name__,
                handler=handler,
                route_type=route_type,
                condition=condition,
                priority=priority,
                description=description or handler.__doc__ or handler.__name__,
                exact_match=exact_match
            )
            self.routes[route_type].append(route)
            self.routes[route_type].sort(key=lambda r: r.priority, reverse=True)
            logger.debug(f"Registered route: {route_type.value} -> '{condition}' -> {handler.__name__}")
            return handler
        return decorator
    
    def _match_text(self, text: str, condition: str, exact_match: bool) -> bool:
        """
        Проверка соответствия текста условию.
        
        Args:
            text: текст сообщения (уже в нижнем регистре)
            condition: условие для проверки
            exact_match: True = точное совпадение, False = startswith с проверкой границ
        
        Returns:
            bool: соответствует ли текст условию
        """
        if exact_match:
            return text == condition
        
        # Для startswith: проверяем, что текст начинается с условия
        # и после условия либо конец строки, либо пробел
        if text.startswith(condition):
            if len(text) > len(condition):
                return text[len(condition)] == ' '
            return True
        return False
    
    def handle(self, db, vk, user, text: str, state: str = None, payload: dict = None):
        """
        Найти и выполнить подходящий обработчик.
        
        Порядок проверки:
        1. Payload (самый точный)
        2. Состояние FSM
        3. Текстовые команды
        
        Все обработчики получают payload как именованный аргумент
        для унификации сигнатуры.
        
        Returns:
            результат выполнения обработчика или None
        """
        text_lower = text.lower().strip() if text else ""
        
        # 1. Сначала проверяем payload (самый точный)
        if payload and self.routes[RouteType.PAYLOAD]:
            payload_type = payload.get('type')
            for route in self.routes[RouteType.PAYLOAD]:
                if route.condition == payload_type:
                    logger.debug(f"Route matched: PAYLOAD -> '{payload_type}' -> {route.name}")
                    return route.handler(db, vk, user, text_lower, payload=payload)
        
        # 2. Затем проверяем состояние FSM
        if state and state != "idle" and self.routes[RouteType.STATE]:
            for route in self.routes[RouteType.STATE]:
                if route.condition == state:
                    logger.debug(f"Route matched: STATE -> '{state}' -> {route.name}")
                    return route.handler(db, vk, user, text_lower, payload=None)
        
        # 3. Проверяем текстовые команды
        if text_lower and self.routes[RouteType.TEXT]:
            for route in self.routes[RouteType.TEXT]:
                if self._match_text(text_lower, route.condition, route.exact_match):
                    logger.debug(f"Route matched: TEXT -> '{route.condition}' -> {route.name}")
                    return route.handler(db, vk, user, text_lower, payload=None)
        
        # 4. Нет подходящего обработчика
        logger.debug(f"No route found: text='{text_lower}', state='{state}', payload={payload}")
        return handle_unknown(vk, user.vk_id, send_msg)
    
    def list_routes(self) -> Dict[str, list]:
        """Отладочный метод для просмотра всех зарегистрированных маршрутов"""
        return {
            "text": [
                {
                    "condition": r.condition, 
                    "handler": r.name, 
                    "priority": r.priority, 
                    "exact_match": r.exact_match
                } 
                for r in self.routes[RouteType.TEXT]
            ],
            "state": [
                {"condition": r.condition, "handler": r.name, "priority": r.priority} 
                for r in self.routes[RouteType.STATE]
            ],
            "payload": [
                {"condition": r.condition, "handler": r.name, "priority": r.priority} 
                for r in self.routes[RouteType.PAYLOAD]
            ],
        }


# Глобальный экземпляр роутера
router = Router()