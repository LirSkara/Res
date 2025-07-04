"""
QRes OS 4 - User Model
Модель пользователя системы (сотрудники ресторана)
"""
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
import enum

from ..database import Base

if TYPE_CHECKING:
    from .order import Order


class UserRole(str, enum.Enum):
    """Роли пользователей в системе"""
    ADMIN = "admin"
    WAITER = "waiter"
    KITCHEN = "kitchen"


class User(Base):
    """Модель пользователя (сотрудника ресторана)"""
    
    __tablename__ = "users"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    
    # Статус и настройки
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    shift_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Дополнительная информация
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    passport: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pin_code: Mapped[Optional[str]] = mapped_column(String(6), nullable=True)
    
    # Связи
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=True
    )
    
    # Временные метки
    last_login: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship(
        "User", 
        remote_side=[id], 
        back_populates="created_users"
    )
    created_users: Mapped[List["User"]] = relationship(
        "User", 
        back_populates="created_by"
    )
    
    # Заказы этого официанта
    orders: Mapped[List["Order"]] = relationship(
        "Order", 
        back_populates="waiter",
        foreign_keys="Order.waiter_id"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
