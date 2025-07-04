"""
QRes OS 4 - Order Models
Модели заказа и позиций заказа
"""
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from decimal import Decimal
import enum

from ..database import Base


class OrderStatus(str, enum.Enum):
    """Статусы заказа"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    """Статусы оплаты"""
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"


class OrderType(str, enum.Enum):
    """Типы заказа"""
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"


class OrderItemStatus(str, enum.Enum):
    """Статусы позиций заказа"""
    NEW = "new"
    COOKING = "cooking"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"


class Order(Base):
    """Модель заказа"""
    
    __tablename__ = "orders"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    total_price: Mapped[Decimal] = mapped_column(Float(precision=2), default=0.0, nullable=False)
    
    # Статусы
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), 
        default=OrderStatus.PENDING, 
        nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), 
        default=PaymentStatus.UNPAID, 
        nullable=False
    )
    order_type: Mapped[OrderType] = mapped_column(
        SQLEnum(OrderType), 
        default=OrderType.DINE_IN, 
        nullable=False
    )
    
    # Связи
    table_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tables.id"), 
        nullable=False
    )
    waiter_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False
    )
    
    # Временные метки
    served_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_to_serve: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # минуты
    
    # Комментарии
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    table: Mapped["Table"] = relationship(
        "Table", 
        back_populates="orders",
        foreign_keys=[table_id]
    )
    waiter: Mapped["User"] = relationship(
        "User", 
        back_populates="orders",
        foreign_keys=[waiter_id]
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", 
        back_populates="order",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, table_id={self.table_id}, status='{self.status}')>"


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
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, dish_id={self.dish_id}, quantity={self.quantity})>"
