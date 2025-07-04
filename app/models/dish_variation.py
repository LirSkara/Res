"""
QRes OS 4 - DishVariation Model
Модель вариации блюда (размеры, добавки, варианты)
"""
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal

from ..database import Base

if TYPE_CHECKING:
    from .dish import Dish
    from .order_item import OrderItem


class DishVariation(Base):
    """Модель вариации блюда"""
    
    __tablename__ = "dish_variations"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Цена и изображение
    price: Mapped[Decimal] = mapped_column(Float(precision=2), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Характеристики
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # граммы
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # ккал
    
    # Настройки
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Учёт
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Связи
    dish_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("dishes.id"), 
        nullable=False
    )
    
    # Relationships
    dish: Mapped["Dish"] = relationship(
        "Dish", 
        back_populates="variations"
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", 
        back_populates="dish_variation"
    )
    
    def __repr__(self) -> str:
        return f"<DishVariation(id={self.id}, dish_id={self.dish_id}, name='{self.name}', price={self.price})>"
