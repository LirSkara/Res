# КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ БЕЗОПАСНОСТИ

## 1. CORS - Исправление заголовков
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # ИСПРАВЛЕНО: Конкретные заголовки вместо wildcard
    allow_headers=[
        "Authorization",
        "Content-Type", 
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token"
    ],
    # ИСПРАВЛЕНО: Минимальный набор заголовков
    expose_headers=[
        "Content-Length",
        "X-Total-Count",
        "X-Page-Count"
    ]
)
```

## 2. TrustedHost - Конкретные хосты
```python
# В config.py
allowed_hosts: List[str] = ["localhost", "127.0.0.1", "yourdomain.com"]

# В main.py
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts  # Конкретные хосты
)
```

## 3. Безопасный секретный ключ
```python
# В .env
SECRET_KEY=generate-strong-256-bit-random-key-here
# Используйте: openssl rand -hex 32

# В config.py
@validator('secret_key')
def validate_secret_key(cls, v):
    if v == "your-super-secret-key-change-in-production":
        raise ValueError("🚨 ИЗМЕНИТЕ SECRET_KEY!")
    if len(v) < 64:  # Увеличено до 64 символов
        raise ValueError("Секретный ключ должен быть не менее 64 символов")
    return v
```

## 4. HTTPS для продакшена
```python
# В config.py для продакшена
cors_origins_production: List[str] = [
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]

qr_base_url_production: str = "https://yourdomain.com/menu"
```

## 5. Отключение отладки в продакшене
```python
@app.get("/debug/cors", tags=["Debug"])
async def debug_cors(request: Request):
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")
    # ... остальной код
```

## 6. Безопасность заголовков
```python
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Добавить middleware безопасности
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Защита от XSS
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HSTS для HTTPS
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # CSP
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response
```

## 7. Ограничение размера запросов
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# В config.py
max_request_size: int = 10 * 1024 * 1024  # 10MB
```

## 8. Логирование безопасности
```python
import logging

security_logger = logging.getLogger("security")

@app.middleware("http")
async def security_logging(request: Request, call_next):
    start_time = time.time()
    
    # Логирование подозрительных запросов
    if any(pattern in str(request.url) for pattern in [
        "wp-admin", "phpmyadmin", ".env", ".git"
    ]):
        security_logger.warning(f"Suspicious request: {request.url} from {request.client.host}")
    
    response = await call_next(request)
    return response
```
