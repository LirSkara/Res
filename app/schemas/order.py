"""
QRes OS 4 - Order Schemas
Pydantic схемы для заказов и позиций заказов
"""
from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from ..models.order import OrderStatus, PaymentStatus, OrderType
from .order_item import OrderItemWithDish, OrderItemCreate


class OrderBase(BaseModel):
    """Базовая схема заказа"""
    table_id: int = Field(..., gt=0)
    order_type: OrderType = OrderType.DINE_IN
    notes: Optional[str] = Field(None, max_length=1000)
    kitchen_notes: Optional[str] = Field(None, max_length=1000)


class OrderCreate(OrderBase):
    """Схема создания заказа"""
    items: List[OrderItemCreate] = Field(..., min_items=1)


class OrderUpdate(BaseModel):
    """Схема обновления заказа"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)
    kitchen_notes: Optional[str] = Field(None, max_length=1000)
    served_at: Optional[datetime] = None


class Order(OrderBase):
    """Полная схема заказа для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    waiter_id: int
    status: OrderStatus
    payment_status: PaymentStatus
    total_price: Decimal
    served_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    time_to_serve: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class OrderWithDetails(Order):
    """Схема заказа с детальной информацией"""
    table_number: int
    waiter_name: str
    items: List[OrderItemWithDish] = []


class OrderStatusUpdate(BaseModel):
    """Схема обновления статуса заказа"""
    status: OrderStatus


class OrderPaymentUpdate(BaseModel):
    """Схема обновления статуса оплаты"""
    payment_status: PaymentStatus


class OrderList(BaseModel):
    """Схема списка заказов"""
    orders: List[Order]
    total: int


class OrderStats(BaseModel):
    """Схема статистики заказов"""
    total_orders: int = 0
    pending_orders: int = 0
    in_progress_orders: int = 0
    ready_orders: int = 0
    served_orders: int = 0
    cancelled_orders: int = 0
    total_revenue: Decimal = Decimal('0.00')
    average_order_value: Decimal = Decimal('0.00')
    average_cooking_time: Optional[int] = None


# WebSocket схемы
class OrderWebSocketMessage(BaseModel):
    """Схема WebSocket сообщения о заказе"""
    type: str  # 'order_created', 'order_updated', 'item_status_changed'
    order_id: int
    data: dict
