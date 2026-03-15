from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    vk_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    sex: Mapped[int] = mapped_column(Integer, nullable=True) # пол (1 - женский, 2 - мужской)
    profile_url: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    last_search_offset: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<User(vk_id={self.vk_id}, name='{self.first_name}')>"
    