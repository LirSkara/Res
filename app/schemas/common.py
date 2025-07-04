"""
QRes OS 4 - Common Schemas
Общие схемы для API ответов
"""
from pydantic import BaseModel
from typing import Optional, Any


class APIResponse(BaseModel):
    """Стандартный ответ API"""
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Схема ошибки"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


class HealthCheck(BaseModel):
    """Схема проверки состояния сервиса"""
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
    uptime: float
