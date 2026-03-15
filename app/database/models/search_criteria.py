from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.database.base import Base
import datetime

class SearchCriteria(Base):
    __tablename__ = "search_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    age_from: Mapped[int] = mapped_column(Integer, nullable=True)
    age_to: Mapped[int] = mapped_column(Integer, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    sex: Mapped[int] = mapped_column(Integer, nullable=True)
    has_photos: Mapped[bool] = mapped_column(Boolean, default=True)
    relation_status: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", backref="search_criteria")
    
    def __repr__(self):
        return f"<SearchCriteria(user_id={self.user_vk_id}, age={self.age_from}-{self.age_to})>"