"""
QRes OS 4 - Location Schemas
Pydantic схемы для локаций/зон ресторана
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class LocationBase(BaseModel):
    """Базовая схема локации"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')  # HEX color
    is_active: bool = True


class LocationCreate(LocationBase):
    """Схема создания локации"""
    pass


class LocationUpdate(BaseModel):
    """Схема обновления локации"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_active: Optional[bool] = None


class Location(LocationBase):
    """Полная схема локации для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class LocationWithTables(Location):
    """Схема локации с привязанными столиками"""
    tables_count: int = 0


class LocationList(BaseModel):
    """Схема списка локаций"""
    locations: List[Location]
    total: int
