"""
QRes OS 4 - Order Models
Модели заказа и позиций заказа
"""
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
import enum

from ..database import Base

if TYPE_CHECKING:
    from .table import Table
    from .user import User
    from .dish import Dish
    from .order_item import OrderItem
    from .paymentmethod import PaymentMethod


class OrderStatus(str, enum.Enum):
    """Статусы заказа"""
    PENDING = "pending"
    READY = "ready"
    SERVED = "served"
    DINING = "dining"
    COMPLETED = "completed"
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
    table_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("tables.id"), 
        nullable=True  # Для доставки столик не нужен
    )
    waiter_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False
    )
    payment_method_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("payment_methods.id"), 
        nullable=True  # Заказ можно создать без способа оплаты
    )
    
    # Поля для доставки
    customer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    delivery_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    delivery_notes: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    # Временные метки
    served_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_to_serve: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # минуты
    
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
    
    # Комментарии
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    table: Mapped[Optional["Table"]] = relationship(
        "Table", 
        back_populates="orders",
        foreign_keys=[table_id]
    )
    waiter: Mapped["User"] = relationship(
        "User", 
        back_populates="orders",
        foreign_keys=[waiter_id]
    )
    payment_method: Mapped[Optional["PaymentMethod"]] = relationship(
        "PaymentMethod",
        foreign_keys=[payment_method_id]
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", 
        back_populates="order",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, table_id={self.table_id}, status='{self.status}')>"
