"""
Модель просмотренных пользователей.
Единая таблица для: истории просмотров, избранного, черного списка
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, Boolean, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from .user import User


class ViewedUser(Base):
    """
    Запись о просмотре кандидата пользователем.
    Одна таблица заменяет: viewed_users + favorites + blacklist
    """
    __tablename__ = "viewed_users"
    
    # Составной индекс для быстрого поиска по user_vk_id и viewed_user_vk_id
    __table_args__ = (
        Index('ix_viewed_user_user_target', 'user_vk_id', 'viewed_user_vk_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    viewed_user_vk_id: Mapped[int] = mapped_column(Integer)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Статусы (используются!)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Оценки совместимости (требование 12)
    compatibility_score: Mapped[int] = mapped_column(Integer, default=0)
    age_score: Mapped[int] = mapped_column(Integer, default=0)
    city_score: Mapped[int] = mapped_column(Integer, default=0)
    interests_score: Mapped[int] = mapped_column(Integer, default=0)
    friends_score: Mapped[int] = mapped_column(Integer, default=0)
    photos_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Используем строковую ссылку для избежания циклического импорта
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_vk_id], back_populates="viewed_users"
    )
    
    def __repr__(self):
        status = []
        if self.is_favorite:
            status.append("⭐")
        if self.is_blocked:
            status.append("🚫")
        status_str = " ".join(status) if status else "👁️"
        return f"<ViewedUser({self.user_vk_id}→{self.viewed_user_vk_id}) {status_str}>"