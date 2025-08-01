"""
QRes OS 4 - Schemas Package
Централизованный импорт всех Pydantic схем
"""

# User schemas
from .user import (
    User, UserCreate, UserUpdate, UserChangePassword, UserList,
    UserLogin, UserLoginPIN, Token, TokenData, UserRole
)

# Location schemas
from .location import (
    Location, LocationCreate, LocationUpdate, LocationWithTables, LocationList
)

# Table schemas
from .table import (
    Table, TableCreate, TableUpdate, TableStatusUpdate,
    TableWithLocation, TableWithOrder, TableList, QRCodeResponse
)

# Category schemas
from .category import (
    Category, CategoryCreate, CategoryUpdate, CategoryWithDishes, CategoryList
)

# Dish schemas
from .dish import (
    Dish, DishCreate, DishUpdate, DishWithCategory,
    DishAvailabilityUpdate, DishList, MenuResponse
)

# Dish Variation schemas  
from .dish_variation import (
    DishVariation, DishVariationCreate, DishVariationUpdate, DishVariationWithDish,
    DishVariationList, DishVariationAvailabilityUpdate, DishVariationDefaultUpdate
)

# Order schemas
from .order import (
    Order, OrderCreate, OrderUpdate, OrderWithDetails,
    OrderStatusUpdate, OrderPaymentUpdate, OrderPaymentComplete, OrderList, OrderStats,
    OrderWebSocketMessage, DeliveryOrderCreate, DeliveryOrderResponse
)

# Order Item schemas  
from .order_item import (
    OrderItem, OrderItemCreate, OrderItemUpdate, OrderItemWithDish,
    OrderItemStatusUpdate
)

# Misc schemas
from .misc import (
    Ingredient, IngredientCreate, IngredientUpdate, IngredientList,
    PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodList
)

# Common schemas
from .common import APIResponse, ErrorResponse, HealthCheck

__all__ = [
    # User
    "User", "UserCreate", "UserUpdate", "UserChangePassword", "UserList",
    "UserLogin", "UserLoginPIN", "Token", "TokenData", "UserRole",
    
    # Location
    "Location", "LocationCreate", "LocationUpdate", "LocationWithTables", "LocationList",
    
    # Table
    "Table", "TableCreate", "TableUpdate", "TableStatusUpdate",
    "TableWithLocation", "TableWithOrder", "TableList", "QRCodeResponse",
    
    # Category
    "Category", "CategoryCreate", "CategoryUpdate", "CategoryWithDishes", "CategoryList",
    
    # Dish
    "Dish", "DishCreate", "DishUpdate", "DishWithCategory",
    "DishAvailabilityUpdate", "DishList", "MenuResponse",
    
    # Order
    "Order", "OrderCreate", "OrderUpdate", "OrderWithDetails",
    "OrderItem", "OrderItemCreate", "OrderItemUpdate", "OrderItemWithDish",
    "OrderStatusUpdate", "OrderPaymentUpdate", "OrderPaymentComplete", "OrderList", "OrderStats",
    "OrderWebSocketMessage", "DeliveryOrderCreate", "DeliveryOrderResponse",
    
    # Misc
    "Ingredient", "IngredientCreate", "IngredientUpdate", "IngredientList",
    "PaymentMethod", "PaymentMethodCreate", "PaymentMethodUpdate", "PaymentMethodList",
    
    # Common
    "APIResponse", "ErrorResponse", "HealthCheck",
]
