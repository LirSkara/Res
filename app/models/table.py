"""
QRes OS 4 - Table Model
Модель столика ресторана
"""
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import uuid

from ..database import Base

if TYPE_CHECKING:
    from .location import Location
    from .order import Order


class Table(Base):
    """Модель столика ресторана"""
    
    __tablename__ = "tables"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    qr_code: Mapped[str] = mapped_column(
        String(36), 
        unique=True, 
        nullable=False, 
        default=lambda: str(uuid.uuid4())
    )
    seats: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Статус
    is_occupied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Дополнительная информация
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Связи
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("locations.id"), 
        nullable=True
    )
    current_order_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("orders.id"), 
        nullable=True
    )
    
    # Временные метки
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
    location_obj: Mapped[Optional["Location"]] = relationship(
        "Location", 
        back_populates="tables"
    )
    current_order: Mapped[Optional["Order"]] = relationship(
        "Order", 
        foreign_keys=[current_order_id],
        post_update=True
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", 
        back_populates="table",
        foreign_keys="Order.table_id"
    )
    
    def __repr__(self) -> str:
        return f"<Table(id={self.id}, number={self.number}, qr_code='{self.qr_code}')>"
