from sqlalchemy import Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.database.base import Base
import datetime

class Blacklist(Base):
    __tablename__ = "blacklist"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"), primary_key=True)
    blocked_user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    
    user = relationship("User", foreign_keys=[user_id], backref="blocked_users")
    
    def __repr__(self):
        return f"<Blacklist(user={self.user_id}, blocked={self.blocked_user_id})>"