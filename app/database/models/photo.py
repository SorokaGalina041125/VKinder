from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.database.base import Base
import datetime

class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    photo_id: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(Integer)
    photo_url: Mapped[str] = mapped_column(String(500))
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    is_profile_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    popularity_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    user = relationship("User", backref="photos")
    
    def __repr__(self):
        return f"<Photo(id={self.photo_id}, likes={self.likes_count})>"