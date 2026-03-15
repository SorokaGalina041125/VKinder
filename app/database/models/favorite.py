from sqlalchemy import Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.database.base import Base
import datetime

class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"), primary_key=True)
    favorite_user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    user = relationship("User", foreign_keys=[user_id], backref="favorites_added")
    
    def __repr__(self):
        return f"<Favorite(user={self.user_id}, favorite={self.favorite_user_id})>"