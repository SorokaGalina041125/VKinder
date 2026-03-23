"""
Модели пользователей и критериев поиска
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Для избежания циклических импортов
if TYPE_CHECKING:
    from .viewed import ViewedUser
    from .content import Photo, UserInterest, Like  # ← ДОБАВИТЬ Like


class User(Base):
    """
    Пользователь бота или кандидат.
    is_bot_user = True → пользователь, который взаимодействует с ботом
    is_bot_user = False → кандидат (найденный в VK)
    """
    __tablename__ = "users"

    vk_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    sex: Mapped[Optional[int]] = mapped_column(Integer)
    profile_url: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Тип пользователя
    is_bot_user: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # FSM (только для is_bot_user=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), default="idle")
    
    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Связи (используем строковые ссылки для избежания циклических импортов)
    viewed_users: Mapped[List["ViewedUser"]] = relationship(
        "ViewedUser", foreign_keys="ViewedUser.user_vk_id", back_populates="user"
    )
    photos: Mapped[List["Photo"]] = relationship("Photo", back_populates="user")
    interests: Mapped[List["UserInterest"]] = relationship("UserInterest", back_populates="user")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="user")  # ← ДОБАВИТЬ
    search_criteria: Mapped[Optional["SearchCriteria"]] = relationship(
        "SearchCriteria", back_populates="user", uselist=False
    )
    
    def __repr__(self) -> str:
        return f"<User({self.vk_id}, {self.first_name}, bot={self.is_bot_user})>"


class SearchCriteria(Base):
    """
    Критерии поиска для пользователя.
    One-to-One с User (один пользователь → одни критерии)
    """
    __tablename__ = "search_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    
    age_from: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    age_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    city_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sex: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_photos: Mapped[bool] = mapped_column(Boolean, default=True)
    relation_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    search_offset: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship("User", back_populates="search_criteria")
    
    def __repr__(self):
        return (f"<SearchCriteria(user={self.user_vk_id}, "
                f"age={self.age_from}-{self.age_to}, city={self.city})>")