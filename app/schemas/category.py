"""
QRes OS 4 - Category Schemas
Pydantic схемы для категорий блюд
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    """Базовая схема категории"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    image_url: Optional[str] = Field(None, max_length=255)
    sort_order: int = Field(0, ge=0)
    is_active: bool = True


class CategoryCreate(CategoryBase):
    """Схема создания категории"""
    pass


class CategoryUpdate(BaseModel):
    """Схема обновления категории"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    image_url: Optional[str] = Field(None, max_length=255)
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class Category(CategoryBase):
    """Полная схема категории для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class CategoryWithDishes(Category):
    """Схема категории с количеством блюд"""
    dishes_count: int = 0
    active_dishes_count: int = 0


class CategoryList(BaseModel):
    """Схема списка категорий"""
    categories: List[Category]
    total: int
