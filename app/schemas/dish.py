"""
QRes OS 4 - Dish Schemas
Pydantic схемы для блюд
"""
from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class DishBase(BaseModel):
    """Базовая схема блюда"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    category_id: int = Field(..., gt=0)
    code: Optional[str] = Field(None, max_length=50)
    main_image_url: Optional[str] = Field(None, max_length=255)
    cooking_time: Optional[int] = Field(None, gt=0, le=240)  # до 4 часов
    weight: Optional[float] = Field(None, gt=0)
    calories: Optional[int] = Field(None, gt=0)
    ingredients: Optional[str] = None
    sort_order: int = Field(default=0)
    is_popular: bool = Field(default=False)
    is_available: bool = True


class DishCreate(DishBase):
    """Схема создания блюда"""
    pass


class DishUpdate(BaseModel):
    """Схема обновления блюда"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = Field(None, gt=0)
    code: Optional[str] = Field(None, max_length=50)
    main_image_url: Optional[str] = Field(None, max_length=255)
    cooking_time: Optional[int] = Field(None, gt=0, le=240)
    weight: Optional[float] = Field(None, gt=0)
    calories: Optional[int] = Field(None, gt=0)
    ingredients: Optional[str] = None
    sort_order: Optional[int] = None
    is_popular: Optional[bool] = None
    is_available: Optional[bool] = None


class Dish(DishBase):
    """Полная схема блюда для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class DishWithCategory(Dish):
    """Схема блюда с информацией о категории"""
    category_name: str
    category_sort_order: int = 0


class DishAvailabilityUpdate(BaseModel):
    """Схема обновления доступности блюда"""
    is_available: bool


class DishList(BaseModel):
    """Схема списка блюд"""
    dishes: List[Dish]
    total: int


class MenuResponse(BaseModel):
    """Схема меню для клиентов (группировка по категориям)"""
    categories: List[dict]  # Структура: {category: Category, dishes: List[Dish]}
