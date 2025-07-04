"""
QRes OS 4 - Table Schemas
Pydantic схемы для столиков
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class TableBase(BaseModel):
    """Базовая схема столика"""
    number: int = Field(..., gt=0)
    seats: int = Field(..., gt=0, le=20)
    location_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=255)
    is_active: bool = True


class TableCreate(TableBase):
    """Схема создания столика"""
    pass


class TableUpdate(BaseModel):
    """Схема обновления столика"""
    number: Optional[int] = Field(None, gt=0)
    seats: Optional[int] = Field(None, gt=0, le=20)
    location_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class TableStatusUpdate(BaseModel):
    """Схема обновления статуса занятости столика"""
    is_occupied: bool


class Table(TableBase):
    """Полная схема столика для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    qr_code: str
    is_occupied: bool = False
    current_order_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class TableWithLocation(Table):
    """Схема столика с информацией о локации"""
    location_name: Optional[str] = None
    location_color: Optional[str] = None


class TableWithOrder(Table):
    """Схема столика с информацией о текущем заказе"""
    current_order_total: Optional[float] = None
    current_order_status: Optional[str] = None


class TableList(BaseModel):
    """Схема списка столиков"""
    tables: List[Table]
    total: int


class QRCodeResponse(BaseModel):
    """Ответ с информацией о QR-коде"""
    qr_code: str
    qr_url: str
    menu_url: str
