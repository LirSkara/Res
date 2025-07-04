"""
QRes OS 4 - Routers Package
Централизованный импорт всех роутеров
"""

from . import auth
from . import users
from . import tables
from . import locations
from . import categories
from . import dishes

__all__ = [
    "auth",
    "users",
    "tables",
    "locations", 
    "categories",
    "dishes",
]
