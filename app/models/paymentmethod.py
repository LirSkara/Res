"""
QRes OS 4 - PaymentMethod Model
Модель способа оплаты
"""
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class PaymentMethod(Base):
    """Модель способа оплаты"""
    
    __tablename__ = "payment_methods"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<PaymentMethod(id={self.id}, name='{self.name}')>"
