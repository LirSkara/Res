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
    payment_method_id: Optional[int] = None
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
    payment_method_id: Optional[int] = None
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
    payment_method_name: Optional[str] = None
    items: List[OrderItemWithDish] = []


class OrderStatusUpdate(BaseModel):
    """Схема обновления статуса заказа"""
    status: OrderStatus


class OrderPaymentUpdate(BaseModel):
    """Схема обновления статуса оплаты"""
    payment_status: PaymentStatus
    payment_method_id: Optional[int] = None


class OrderPaymentComplete(BaseModel):
    """Схема завершения оплаты заказа"""
    payment_method_id: int = Field(..., gt=0)
    payment_status: PaymentStatus = PaymentStatus.PAID


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


# Схемы для доставки
class DeliveryOrderBase(BaseModel):
    """Базовая схема заказа с доставкой"""
    order_type: OrderType = OrderType.DELIVERY
    notes: Optional[str] = Field(None, max_length=1000)
    kitchen_notes: Optional[str] = Field(None, max_length=1000)
    
    # Данные клиента для доставки
    customer_name: str = Field(..., min_length=2, max_length=100)
    customer_phone: str = Field(..., min_length=10, max_length=20)
    delivery_address: str = Field(..., min_length=10, max_length=500)
    delivery_notes: Optional[str] = Field(None, max_length=300)


class DeliveryOrderCreate(DeliveryOrderBase):
    """Схема создания заказа с доставкой"""
    items: List[OrderItemCreate] = Field(..., min_items=1)


class DeliveryOrderResponse(BaseModel):
    """Схема ответа для заказа с доставкой"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    waiter_id: int
    order_type: OrderType
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method_id: Optional[int] = None
    total_price: Decimal
    notes: Optional[str] = None
    kitchen_notes: Optional[str] = None
    
    # Данные клиента
    customer_name: str
    customer_phone: str
    delivery_address: str
    delivery_notes: Optional[str] = None
    
    # Служебные поля
    served_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    time_to_serve: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    # Детали заказа
    waiter_name: str
    payment_method_name: Optional[str] = None
    items: List[OrderItemWithDish] = []
