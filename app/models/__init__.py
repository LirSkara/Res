"""
QRes OS 4 - Models Package
Централизованный импорт всех моделей для правильной работы SQLAlchemy relationships
"""

# Импортируем все модели в правильном порядке для установки связей
from .user import User, UserRole
from .location import Location
from .table import Table
from .category import Category
from .dish import Dish
from .ingredient import Ingredient
from .paymentmethod import PaymentMethod
from .order import Order, OrderStatus, PaymentStatus, OrderType
from .order_item import OrderItem, OrderItemStatus

# Экспортируем все модели
__all__ = [
    # Models
    "User",
    "Location", 
    "Table",
    "Category",
    "Dish",
    "Ingredient",
    "PaymentMethod",
    "Order",
    "OrderItem",
    
    # Enums
    "UserRole",
    "OrderStatus",
    "PaymentStatus", 
    "OrderType",
    "OrderItemStatus",
]
