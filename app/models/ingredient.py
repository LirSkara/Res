"""
QRes OS 4 - Ingredient Model
Модель ингредиента
"""
from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from ..database import Base


class Ingredient(Base):
    """Модель ингредиента"""
    
    __tablename__ = "ingredients"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_allergen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Ingredient(id={self.id}, name='{self.name}', is_allergen={self.is_allergen})>"
