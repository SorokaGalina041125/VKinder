from sqlalchemy import Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.database.base import Base
import datetime

class ViewedUser(Base):
    __tablename__ = "viewed_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    viewed_user_vk_id: Mapped[int] = mapped_column(Integer)
    viewed_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Оценки совместимости
    compatibility_score: Mapped[int] = mapped_column(Integer, default=0)
    age_score: Mapped[int] = mapped_column(Integer, default=0)
    city_score: Mapped[int] = mapped_column(Integer, default=0)
    interests_score: Mapped[int] = mapped_column(Integer, default=0)
    friends_score: Mapped[int] = mapped_column(Integer, default=0)
    photos_score: Mapped[int] = mapped_column(Integer, default=0)
    
    user = relationship("User", foreign_keys=[user_vk_id], backref="viewed_users")
    
    def __repr__(self):
        return f"<ViewedUser(user={self.user_vk_id}, viewed={self.viewed_user_vk_id})>"