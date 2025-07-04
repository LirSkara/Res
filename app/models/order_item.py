"""
QRes OS 4 - OrderItem Model
Модель позиции заказа (отдельный файл согласно ТЗ)
"""
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
import enum

from ..database import Base

if TYPE_CHECKING:
    from .order import Order
    from .dish import Dish
    from .dish_variation import DishVariation


class OrderItemStatus(str, enum.Enum):
    """Статусы позиций заказа"""
    NEW = "new"
    COOKING = "cooking"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"


class OrderItem(Base):
    """Модель позиции заказа"""
    
    __tablename__ = "order_items"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Float(precision=2), nullable=False)  # цена на момент заказа
    total: Mapped[Decimal] = mapped_column(Float(precision=2), nullable=False)  # quantity * price
    
    # Статус
    status: Mapped[OrderItemStatus] = mapped_column(
        SQLEnum(OrderItemStatus), 
        default=OrderItemStatus.NEW, 
        nullable=False
    )
    
    # Связи
    order_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("orders.id"), 
        nullable=False
    )
    dish_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("dishes.id"), 
        nullable=False
    )
    dish_variation_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("dish_variations.id"), 
        nullable=True
    )
    
    # Комментарии
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    order: Mapped["Order"] = relationship(
        "Order", 
        back_populates="items"
    )
    dish: Mapped["Dish"] = relationship(
        "Dish", 
        back_populates="order_items"
    )
    dish_variation: Mapped[Optional["DishVariation"]] = relationship(
        "DishVariation", 
        back_populates="order_items"
    )
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, dish_id={self.dish_id}, quantity={self.quantity})>"
