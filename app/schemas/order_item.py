"""
QRes OS 4 - OrderItem Schemas
Pydantic схемы для позиций заказов (отдельный файл согласно ТЗ)
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from ..models.order_item import OrderItemStatus, KitchenDepartment


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
    department: KitchenDepartment
    
    # Временные метки
    sent_to_kitchen_at: Optional[datetime] = None
    preparation_started_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    served_at: Optional[datetime] = None
    
    # Время приготовления
    estimated_preparation_time: Optional[int] = None
    actual_preparation_time: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime


class OrderItemWithDish(OrderItem):
    """Схема позиции заказа с информацией о блюде"""
    dish_name: str
    dish_image_url: Optional[str] = None
    dish_cooking_time: Optional[int] = None
    dish_department: KitchenDepartment


class OrderItemStatusUpdate(BaseModel):
    """Схема обновления статуса позиции заказа"""
    status: OrderItemStatus


class KitchenOrderItem(BaseModel):
    """Схема позиции заказа для кухни"""
    id: int
    order_id: int
    table_number: Optional[int] = None
    dish_name: str
    dish_image_url: Optional[str] = None
    quantity: int
    comment: Optional[str] = None
    status: OrderItemStatus
    department: KitchenDepartment
    estimated_preparation_time: Optional[int] = None
    sent_to_kitchen_at: Optional[datetime] = None
    created_at: datetime


class OrderItemStatusUpdate(BaseModel):
    """Схема обновления статуса позиции заказа"""
    status: OrderItemStatus
