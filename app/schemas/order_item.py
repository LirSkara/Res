"""
QRes OS 4 - OrderItem Schemas
Pydantic схемы для позиций заказов (отдельный файл согласно ТЗ)
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from ..models.order_item import OrderItemStatus


class OrderItemBase(BaseModel):
    """Базовая схема позиции заказа"""
    dish_id: int = Field(..., gt=0)
    dish_variation_id: Optional[int] = Field(None, gt=0)
    quantity: int = Field(..., gt=0, le=50)
    comment: Optional[str] = Field(None, max_length=500)


class OrderItemCreate(OrderItemBase):
    """Схема создания позиции заказа"""
    pass


class OrderItemUpdate(BaseModel):
    """Схема обновления позиции заказа"""
    dish_variation_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, gt=0, le=50)
    comment: Optional[str] = Field(None, max_length=500)
    status: Optional[OrderItemStatus] = None


class OrderItem(OrderItemBase):
    """Полная схема позиции заказа для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    order_id: int
    price: Decimal
    total: Decimal
    status: OrderItemStatus
    created_at: datetime
    updated_at: datetime


class OrderItemWithDish(OrderItem):
    """Схема позиции заказа с информацией о блюде"""
    dish_name: str
    dish_image_url: Optional[str] = None
    dish_cooking_time: Optional[int] = None


class OrderItemStatusUpdate(BaseModel):
    """Схема обновления статуса позиции заказа"""
    status: OrderItemStatus
