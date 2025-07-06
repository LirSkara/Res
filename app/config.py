"""
QRes OS 4 - Configuration Management
Загрузка и валидация настроек приложения
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    """Настройки приложения с валидацией"""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./app.db"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    reload: bool = True
    
    # CORS - Разрешаем все origins для разработки
    cors_origins: List[str] = ["*"]
    
    # QR Code
    qr_base_url: str = "http://192.168.1.100:8000/menu"
    
    # File Upload
    upload_dir: str = "./uploads"
    max_file_size: int = 5242880  # 5MB
    
    # Security - DDoS Protection
    rate_limit_max_requests: int = 100  # Максимальное количество запросов
    rate_limit_window: int = 60  # Временное окно в секундах (1 минута)
    rate_limit_block_duration: int = 600  # Длительность блокировки (10 минут)
    disable_rate_limit_in_debug: bool = True  # Отключать ли ограничение в режиме разработки
    
    # Restaurant
    restaurant_name: str = "QRes OS 4 Restaurant"
    restaurant_timezone: str = "Europe/Moscow"
    
    @validator('cors_origins', pre=True)
    def assemble_cors_origins(cls, v):
        """Парсинг CORS origins из строки"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator('upload_dir')
    def create_upload_dir(cls, v):
        """Создание директории для загрузок"""
        os.makedirs(v, exist_ok=True)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Singleton для настроек приложения"""
    return Settings()


# Экспорт настроек
settings = get_settings()
