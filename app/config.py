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
    
    # Environment
    environment: str = "development"  # development, staging, production
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./app.db"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # JWT Security improvements
    jwt_issuer: str = "qres-os-4"
    jwt_audience: str = "qres-os-4-users"
    require_fresh_token_minutes: int = 15  # Время после которого требуется fresh token для критичных операций
    
    # CRITICAL: Валидация секретного ключа в продакшене
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if v == "your-super-secret-key-change-in-production":
            import os
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("🚨 КРИТИЧЕСКАЯ ОШИБКА: Измените secret_key в продакшене!")
            else:
                print("⚠️  ПРЕДУПРЕЖДЕНИЕ: Используется дефолтный SECRET_KEY. Измените его перед продакшеном!")
        if len(v) < 32:
            raise ValueError("🔒 Секретный ключ должен быть не менее 32 символов")
        if len(v) < 64:
            print("🔐 РЕКОМЕНДАЦИЯ: Используйте секретный ключ длиной 64+ символов для лучшей безопасности")
        return v
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    reload: bool = True
    
    # CORS - Конфигурируем origins в зависимости от окружения
    cors_origins: List[str] = [
        # Разработка (localhost)
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:4173", 
        "http://127.0.0.1:4173",
        "http://localhost:3002", 
        "http://127.0.0.1:3002",
        "http://localhost:5174", 
        "http://127.0.0.1:5174", 
        "http://localhost:5175", 
        "http://127.0.0.1:5175", 
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
        # WiFi подсеть 192.168.4.0/24 добавляется автоматически валидатором
    ]
    
    # Trusted Hosts - Разрешенные хосты для защиты от Host Header Injection
    allowed_hosts: List[str] = [
        "localhost",
        "127.0.0.1", 
        "0.0.0.0",           # Для разработки
        "192.168.1.100",     # Локальная сеть для QR кодов
        "*.localhost"        # Поддомены localhost
        # WiFi подсеть 192.168.4.0/24 добавляется автоматически валидатором
    ]
    
    # QR Code - URL для WiFi точки доступа
    qr_base_url: str = "http://192.168.4.1:8000/menu"
    
    # File Upload
    upload_dir: str = "./uploads"
    max_file_size: int = 5242880  # 5MB
    
    # Request size limits
    max_request_size: int = 10 * 1024 * 1024  # 10MB максимальный размер запроса
    max_json_size: int = 1024 * 1024  # 1MB для JSON запросов
    
    # Security - DDoS Protection
    rate_limit_max_requests: int = 10000  # Максимальное количество запросов
    rate_limit_window: int = 60  # Временное окно в секундах (1 минута)
    rate_limit_block_duration: int = 60  # Длительность блокировки (1 минута)
    disable_rate_limit_in_debug: bool = True  # Отключать ли ограничение в режиме разработки
    
    # Restaurant
    restaurant_name: str = "QRes OS 4 Restaurant"
    restaurant_timezone: str = "Europe/Moscow"
    
    @validator('allowed_hosts', allow_reuse=True)
    def expand_allowed_hosts(cls, v) -> List[str]:
        """Автоматически добавляем WiFi подсеть в allowed hosts"""
        # Добавляем все IP адреса WiFi подсети
        wifi_ips = [f"192.168.4.{i}" for i in range(1, 21)]
        expanded_hosts = list(v) + wifi_ips
        
        # Убираем дубликаты, сохраняя порядок
        seen = set()
        unique_hosts = []
        for host in expanded_hosts:
            if host not in seen:
                seen.add(host)
                unique_hosts.append(host)
        
        if os.getenv("DEBUG", "false").lower() == "true":
            print(f"🔧 Allowed Hosts расширены: {unique_hosts}")
        
        return unique_hosts

    @validator('cors_origins', pre=True, allow_reuse=True)
    def parse_cors_origins(cls, v) -> List[str]:
        """Парсинг CORS origins из переменной окружения или списка"""
        if isinstance(v, str):
            # Удаляем возможные JSON скобки и кавычки
            v = v.strip().strip('[]"\'')
            if not v:  # Если строка пустая, возвращаем значения по умолчанию
                return [
                    "http://localhost:5173", 
                    "http://127.0.0.1:5173", 
                    "http://localhost:3000", 
                    "http://127.0.0.1:3000",
                    "http://localhost:8080",
                    "http://127.0.0.1:8080"
                ]
            origins = [origin.strip().strip('"\'') for origin in v.split(",")]
            # Фильтруем пустые строки
            origins = [origin for origin in origins if origin]
            if os.getenv("DEBUG", "false").lower() == "true":
                print(f"🔧 CORS Origins загружены из строки: {origins}")
            return origins
        elif isinstance(v, list):
            # Добавляем автоматически всю подсеть WiFi точки доступа
            wifi_subnet_origins = []
            for i in range(1, 21):  # IP от 192.168.4.1 до 192.168.4.20
                ip = f"192.168.4.{i}"
                wifi_subnet_origins.extend([
                    f"http://{ip}:8000",
                    f"http://{ip}:3000", 
                    f"http://{ip}:5173",
                    f"http://{ip}"  # Без порта
                ])
            
            # Объединяем оригинальный список с WiFi подсетью
            final_origins = list(v) + wifi_subnet_origins
            
            if os.getenv("DEBUG", "false").lower() == "true":
                print(f"🔧 CORS Origins загружены как список: {final_origins}")
            return final_origins
        else:
            if os.getenv("DEBUG", "false").lower() == "true":
                print(f"⚠️ Неожиданный тип CORS Origins: {type(v)}, значение: {v}")
            return [str(v)] if v else []
    
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
