"""
QRes OS 4 - Category Model
Модель категории блюд
"""
from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from ..database import Base

if TYPE_CHECKING:
    from .dish import Dish


class Category(Base):
    """Модель категории блюд"""
    
    __tablename__ = "categories"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Цвет категории (например, #e74c3c)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Отмечена ли категория как особая
    
    # Стандартные временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
    
    # Relationships
    dishes: Mapped[List["Dish"]] = relationship(
        "Dish", 
        back_populates="category_obj",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"
