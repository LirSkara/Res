"""
QRes OS 4 - Order Models
Модели заказа и позиций заказа
"""
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Text, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import inspect
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
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"  # Добавили отсутствующий статус
    READY = "READY"
    SERVED = "SERVED"
    DINING = "DINING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    """Статусы оплаты"""
    UNPAID = "UNPAID"
    PAID = "PAID"
    REFUNDED = "REFUNDED"


class OrderType(str, enum.Enum):
    """Типы заказа"""
    DINE_IN = "DINE_IN"
    TAKEAWAY = "TAKEAWAY"
    DELIVERY = "DELIVERY"


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
        DateTime(timezone=True),
        nullable=False,
        server_default=func.datetime('now', '+3 hours')  # UTC + 3 часа для Москвы
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.datetime('now', '+3 hours'),  # UTC + 3 часа для Москвы
        onupdate=func.datetime('now', '+3 hours')
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
        # Безопасное получение атрибутов для объектов, не привязанных к сессии
        try:
            # Проверяем, привязан ли объект к сессии
            state = inspect(self)
            if hasattr(state, 'session') and state.session is not None:
                # Объект привязан к сессии, можем безопасно получить значения
                return f"<Order(id={self.id}, table_id={self.table_id}, status='{self.status}')>"
            else:
                # Объект не привязан к сессии, используем базовое представление
                return f"<Order object at {hex(id(self))}>"
        except Exception:
            # В случае любой ошибки возвращаем базовое представление
            return f"<Order object at {hex(id(self))}>"
    
    @property
    def table_number(self) -> Optional[int]:
        """Номер столика"""
        try:
            return self.table.number if self.table else None
        except Exception:
            return None
    
    @property
    def waiter_name(self) -> str:
        """Имя официанта"""
        try:
            return self.waiter.username if self.waiter else "Неизвестно"
        except Exception:
            return "Неизвестно"
    
    @property
    def payment_method_name(self) -> Optional[str]:
        """Название способа оплаты"""
        try:
            return self.payment_method.name if self.payment_method else None
        except Exception:
            return None
