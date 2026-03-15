from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.database.base import Base

class UserInterest(Base):
    __tablename__ = "user_interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_vk_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.vk_id"))
    interest_type: Mapped[str] = mapped_column(String(20)) # 'music', 'books', 'groups'
    interest_value: Mapped[str] = mapped_column(String(200))
    interest_source_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    user = relationship("User", backref="interests")
    
    def __repr__(self):
        return f"<UserInterest(user={self.user_vk_id}, type='{self.interest_type}')>"