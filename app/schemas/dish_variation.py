"""
QRes OS 4 - Dish Variation Schemas
Pydantic схемы для вариаций блюд
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class DishVariationBase(BaseModel):
    """Базовая схема вариации блюда"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Decimal = Field(..., gt=0, le=999999.99)
    image_url: Optional[str] = Field(None, max_length=255)
    weight: Optional[float] = Field(None, gt=0, le=50000)  # граммы
    calories: Optional[int] = Field(None, gt=0, le=10000)  # ккал
    is_default: bool = Field(False)
    is_available: bool = Field(True)
    sort_order: int = Field(0, ge=0)
    sku: Optional[str] = Field(None, max_length=50)


class DishVariationCreate(DishVariationBase):
    """Схема создания вариации блюда"""
    pass


class DishVariationUpdate(BaseModel):
    """Схема обновления вариации блюда"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[Decimal] = Field(None, gt=0, le=999999.99)
    image_url: Optional[str] = Field(None, max_length=255)
    weight: Optional[float] = Field(None, gt=0, le=50000)
    calories: Optional[int] = Field(None, gt=0, le=10000)
    is_default: Optional[bool] = None
    is_available: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=50)


class DishVariation(DishVariationBase):
    """Полная схема вариации блюда для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    dish_id: int
    created_at: datetime
    updated_at: datetime


class DishVariationWithDish(DishVariation):
    """Схема вариации блюда с информацией о блюде"""
    dish_name: str
    dish_category_id: int


class DishVariationList(BaseModel):
    """Схема списка вариаций блюда"""
    variations: list[DishVariation]
    total: int


class DishVariationAvailabilityUpdate(BaseModel):
    """Схема обновления доступности вариации"""
    is_available: bool


class DishVariationDefaultUpdate(BaseModel):
    """Схема обновления статуса по умолчанию"""
    is_default: bool
