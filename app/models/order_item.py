"""
QRes OS 4 - OrderItem Model
Модель позиции заказа (отдельный файл согласно ТЗ)
"""
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
import enum

from ..database import Base

if TYPE_CHECKING:
    from .order import Order
    from .dish import Dish
    from .dish_variation import DishVariation


class OrderItemStatus(str, enum.Enum):
    """Статусы позиций заказа"""
    NEW = "new"                      # DEPRECATED: Не используется в новой логике
    SENT_TO_KITCHEN = "sent_to_kitchen"  # DEPRECATED: Не используется в новой логике
    IN_PREPARATION = "in_preparation"    # Готовится (статус по умолчанию)
    READY = "ready"                  # Готова к подаче
    SERVED = "served"                # Подана
    CANCELLED = "cancelled"          # Отменена


class KitchenDepartment(str, enum.Enum):
    """Кухонные цехи"""
    BAR = "bar"              # Бар (напитки)
    COLD_KITCHEN = "cold"    # Холодный цех (салаты, закуски)
    HOT_KITCHEN = "hot"      # Горячий цех (основные блюда)
    DESSERT = "dessert"      # Кондитерский цех
    GRILL = "grill"          # Гриль
    BAKERY = "bakery"        # Выпечка


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
        default=OrderItemStatus.IN_PREPARATION, 
        nullable=False
    )
    
    # Кухонный цех
    department: Mapped[KitchenDepartment] = mapped_column(
        SQLEnum(KitchenDepartment), 
        nullable=False
    )
    
    # Временные метки
    sent_to_kitchen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    preparation_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    served_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Время приготовления (минуты)
    estimated_preparation_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_preparation_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # рассчитывается автоматически
    
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
