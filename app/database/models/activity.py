from sqlalchemy import String, Integer, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.database.base import Base
import datetime

class UserActivity(Base):
    __tablename__ = "user_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    activity_type: Mapped[str] = mapped_column(String(50)) # 'search', 'view', etc.
    target_id: Mapped[str] = mapped_column(String(100), nullable=True)
    search_params: Mapped[dict] = mapped_column(JSON, nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    user = relationship("User", backref="activities")
    
    def __repr__(self):
        return f"<UserActivity(user={self.user_vk_id}, type='{self.activity_type}')>"