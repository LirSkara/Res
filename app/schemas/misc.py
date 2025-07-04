"""
QRes OS 4 - Ingredient and Payment Method Schemas
Pydantic схемы для ингредиентов и способов оплаты
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# Ingredient Schemas
class IngredientBase(BaseModel):
    """Базовая схема ингредиента"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_allergen: bool = False


class IngredientCreate(IngredientBase):
    """Схема создания ингредиента"""
    pass


class IngredientUpdate(BaseModel):
    """Схема обновления ингредиента"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_allergen: Optional[bool] = None


class Ingredient(IngredientBase):
    """Полная схема ингредиента для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class IngredientList(BaseModel):
    """Схема списка ингредиентов"""
    ingredients: List[Ingredient]
    total: int


# Payment Method Schemas
class PaymentMethodBase(BaseModel):
    """Базовая схема способа оплаты"""
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True


class PaymentMethodCreate(PaymentMethodBase):
    """Схема создания способа оплаты"""
    pass


class PaymentMethodUpdate(BaseModel):
    """Схема обновления способа оплаты"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class PaymentMethod(PaymentMethodBase):
    """Полная схема способа оплаты для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class PaymentMethodList(BaseModel):
    """Схема списка способов оплаты"""
    payment_methods: List[PaymentMethod]
    total: int
