"""
QRes OS 4 - Dish Model
Модель блюда
"""
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal

from ..database import Base

if TYPE_CHECKING:
    from .category import Category
    from .order_item import OrderItem
    from .dish_variation import DishVariation


class Dish(Base):
    """Модель блюда"""
    
    __tablename__ = "dishes"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Изображения и наличие
    main_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Дополнительные поля согласно ТЗ
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Связи
    category_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("categories.id"), 
        nullable=False
    )
    
    # Дополнительная информация
    cooking_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # минуты
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # граммы
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # ккал
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    category_obj: Mapped["Category"] = relationship(
        "Category", 
        back_populates="dishes"
    )
    variations: Mapped[List["DishVariation"]] = relationship(
        "DishVariation", 
        back_populates="dish",
        cascade="all, delete-orphan"
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", 
        back_populates="dish"
    )
    
    def __repr__(self) -> str:
        return f"<Dish(id={self.id}, name='{self.name}', available={self.is_available})>"
