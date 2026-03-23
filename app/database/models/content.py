"""
Модели контента: фото, лайки, интересы
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Index

from app.database.base import Base

# Для избежания циклических импортов
if TYPE_CHECKING:
    from .user import User


class Photo(Base):
    """Фотографии пользователя"""
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    
    photo_id: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(Integer)
    photo_url: Mapped[str] = mapped_column(Text)  # Увеличено до Text для длинных URL
    
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    popularity_score: Mapped[int] = mapped_column(Integer, default=0)
    
    is_profile_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Используем строковую ссылку для избежания циклического импорта
    user: Mapped["User"] = relationship("User", back_populates="photos")
    
    def __repr__(self):
        return f"<Photo(owner={self.owner_id}, id={self.photo_id}, likes={self.likes_count})>"


class Like(Base):
    """Лайки пользователей на фото кандидатов"""
    __tablename__ = "likes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    photo_owner_id: Mapped[int] = mapped_column(Integer)
    photo_id: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    user: Mapped["User"] = relationship("User", back_populates="likes")
    
    def __repr__(self):
        return f"<Like(user={self.user_vk_id}, photo={self.photo_owner_id}_{self.photo_id})>"


class UserInterest(Base):
    """Интересы пользователя: музыка, книги, группы"""
    __tablename__ = "user_interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    interest_type: Mapped[str] = mapped_column(String(20))
    interest_value: Mapped[str] = mapped_column(Text)
    interest_source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="interests")
    
    def __repr__(self):
        return f"<UserInterest(user={self.user_vk_id}, type='{self.interest_type}')>"