"""
QRes OS 4 - Location Model
Модель локации/зоны ресторана
"""
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

from ..database import Base


class Location(Base):
    """Модель локации/зоны ресторана"""
    
    __tablename__ = "locations"
    
    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # HEX color
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    tables: Mapped[List["Table"]] = relationship(
        "Table", 
        back_populates="location_obj",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Location(id={self.id}, name='{self.name}')>"
