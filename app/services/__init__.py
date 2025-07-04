"""
QRes OS 4 - Services Package
Централизованный импорт всех сервисов
"""

from . import auth
from .orders import OrderService
from .dishes import DishService
from .utils import (
    generate_qr_code, generate_unique_code, format_price,
    calculate_cooking_time, validate_phone_number,
    TableStatusManager, OrderStatusManager
)

__all__ = [
    "auth",
    "OrderService", 
    "DishService",
    "generate_qr_code",
    "generate_unique_code",
    "format_price",
    "calculate_cooking_time",
    "validate_phone_number",
    "TableStatusManager",
    "OrderStatusManager"
]
