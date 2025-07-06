"""
QRes OS 4 - Main Application
Точка входа в приложение FastAPI
"""
import time
import traceback
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import init_db, close_db
from .schemas import ErrorResponse, HealthCheck
from .logger import setup_request_logging  # Импорт логгера
from .security import setup_security  # Импорт компонентов безопасности
from .security_monitor import security_monitor, start_security_monitor_cleanup  # Импорт монитора безопасности
from .input_validation import InputSanitizer  # Импорт санитизатора

# Импорт роутеров
from .routers import (
    auth, users, tables, locations, categories, dishes, 
    orders, order_items, ingredients, 
    paymentmethod, websocket
)

# Настройка логгера для ошибок
error_logger = logging.getLogger("qres_errors")
error_logger.setLevel(logging.WARNING)  # Изменено с ERROR на WARNING

# Создаем хендлер для ошибок если он еще не создан
if not error_logger.handlers:
    from pathlib import Path
    LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Файловый хендлер для ошибок
    error_file_handler = logging.FileHandler(LOGS_DIR / "errors.log", encoding='utf-8')
    error_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_file_handler.setFormatter(error_formatter)
    error_logger.addHandler(error_file_handler)
    
    # Консольный хендлер для разработки
    if settings.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(error_formatter)
        error_logger.addHandler(console_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    # Startup
    print("🚀 QRes OS 4 запускается...")
    await init_db()
    print("✅ База данных инициализирована")
    
    # Запускаем фоновую задачу очистки данных мониторинга безопасности
    cleanup_task = asyncio.create_task(start_security_monitor_cleanup())
    print("🔒 Монитор безопасности запущен")
    
    yield
    
    # Shutdown
    print("🛑 QRes OS 4 завершает работу...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    print("🔒 Монитор безопасности остановлен")
    await close_db()
    print("✅ Соединение с базой данных закрыто")


# Создание FastAPI приложения
app = FastAPI(
    title="QRes OS 4",
    description="Система управления рестораном нового поколения",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Время запуска для uptime
start_time = time.time()


# CORS Middleware - настроен для разработки фронтенда
if settings.debug:
    print(f"🚀 Настройка CORS для origins: {settings.cors_origins}")
    print(f"🔧 Debug режим: {settings.debug}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Используем настройки из конфига
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Ограничиваем методы
    # ИСПРАВЛЕНО: Конкретные заголовки вместо wildcard для безопасности
    allow_headers=[
        "Authorization",      # Токены авторизации
        "Content-Type",       # Тип контента
        "Accept",            # Accept заголовок
        "Origin",            # CORS origin
        "X-Requested-With",  # AJAX запросы
        "X-CSRF-Token"       # CSRF защита
    ],
    # ИСПРАВЛЕНО: Минимальный набор заголовков ответа
    expose_headers=[
        "Content-Length",    # Размер контента
        "X-Total-Count",     # Общее количество (для пагинации)
        "X-Page-Count"       # Количество страниц
    ]
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts  # Используем конкретные хосты для безопасности
)

# Подключение middleware логирования API-запросов
setup_request_logging(app)

# Подключение компонентов безопасности (защита от DDoS-атак)
setup_security(app)

# Middleware для мониторинга безопасности
@app.middleware("http")
async def security_monitoring_middleware(request: Request, call_next):
    """Мониторинг безопасности запросов"""
    try:
        # Записываем запрос в монитор безопасности
        security_monitor.record_request(request)
        
        # Проверяем на подозрительные паттерны в URL
        url_path = str(request.url.path).lower()
        if any(pattern in url_path for pattern in ['.env', '.git', 'admin', 'phpmyadmin']):
            # Логируем подозрительный запрос
            from .security_logger import security_logger
            security_logger.log_suspicious_activity(
                security_monitor.get_client_ip(request),
                str(request.url),
                request.method
            )
        
        response = await call_next(request)
        return response
        
    except HTTPException as e:
        # Если IP заблокирован или превышен лимит запросов
        raise e
    except Exception as e:
        # Логируемunexpected ошибки в мониторе безопасности
        error_logger.error(f"Security monitoring error: {str(e)}")
        # Продолжаем обработку запроса
        response = await call_next(request)
        return response

# Middleware для ограничения размера запросов
@app.middleware("http")
async def request_size_limit_middleware(request: Request, call_next):
    """Ограничивает размер входящих запросов"""
    content_length = request.headers.get("content-length")
    
    if content_length:
        content_length = int(content_length)
        
        # Проверяем общий размер запроса
        if content_length > settings.max_request_size:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Размер запроса превышает лимит {settings.max_request_size // (1024*1024)}MB",
                    "error_code": "REQUEST_TOO_LARGE"
                }
            )
        
        # Дополнительная проверка для JSON запросов
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type and content_length > settings.max_json_size:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Размер JSON запроса превышает лимит {settings.max_json_size // 1024}KB",
                    "error_code": "JSON_TOO_LARGE"
                }
            )
    
    return await call_next(request)

# Middleware для базовых заголовков безопасности
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Добавляет базовые заголовки безопасности"""
    response = await call_next(request)
    
    # Защита от XSS
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"  
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Referrer Policy для приватности
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy (CSP)
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    
    # Permissions Policy для отключения ненужных APIs
    permissions = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "accelerometer=(), "
        "gyroscope=()"
    )
    response.headers["Permissions-Policy"] = permissions
    
    # HSTS для HTTPS (когда будет включен)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # В разработке показываем, что это dev режим
    if settings.debug:
        response.headers["X-Environment"] = "development"
        response.headers["X-Debug-Mode"] = "enabled"
    else:
        # В продакшене скрываем версию сервера
        response.headers.pop("server", None)
    
    return response


# Обработчики ошибок
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Обработка HTTP ошибок"""
    # Логируем только серьезные ошибки (4xx и 5xx)
    if exc.status_code >= 400:
        error_logger.warning(
            f"HTTP ошибка {exc.status_code}: {exc.detail} | "
            f"{request.method} {request.url} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}"
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработка ошибок валидации"""
    error_details = exc.errors()
    
    # Логируем ошибки валидации для анализа
    error_logger.warning(
        f"Ошибка валидации: {request.method} {request.url} | "
        f"Client: {request.client.host if request.client else 'unknown'} | "
        f"Errors: {error_details}"
    )
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            message="Ошибка валидации данных",
            error_code="VALIDATION_ERROR",
            details={"errors": error_details}
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработка общих ошибок"""
    
    # Получаем детальную информацию об ошибке
    error_traceback = traceback.format_exc()
    
    # Информация о запросе
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "headers": dict(request.headers) if settings.debug else {}
    }
    
    # Логируем с максимальной детализацией
    error_message = (
        f"Необработанная ошибка: {type(exc).__name__}: {str(exc)}\n"
        f"Запрос: {request.method} {request.url}\n"
        f"Клиент: {request_info['client']}\n"
        f"User-Agent: {request_info['user_agent']}\n"
        f"Traceback:\n{error_traceback}"
    )
    
    error_logger.error(error_message)
    
    # В режиме разработки возвращаем детальную информацию
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message=f"Внутренняя ошибка сервера: {str(exc)}",
                error_code="INTERNAL_SERVER_ERROR",
                details={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "request_info": request_info
                }
            ).model_dump()
        )
    else:
        # В продакшене не раскрываем детали ошибки
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message="Внутренняя ошибка сервера",
                error_code="INTERNAL_SERVER_ERROR"
            ).model_dump()
        )


# Основные роуты
@app.get("/", include_in_schema=False)
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "🍽️ QRes OS 4 - Restaurant Management System",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Проверка состояния системы"""
    uptime = time.time() - start_time
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        database="connected",
        uptime=round(uptime, 2)
    )


@app.get("/debug/cors", tags=["Debug"])
async def debug_cors(request: Request):
    """Отладочный эндпоинт для проверки CORS настроек (только в dev режиме)"""
    # Защита: доступ только в режиме разработки
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")
    
    origin = request.headers.get("origin", "Не указан")
    
    return {
        "message": "Информация отладки CORS",
        "configured_origins": settings.cors_origins,
        "allowed_hosts": settings.allowed_hosts,
        "request_origin": origin,
        "origin_allowed": origin in settings.cors_origins,
        "cors_config": {
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Authorization", "Content-Type", "Accept", 
                "Origin", "X-Requested-With", "X-CSRF-Token"
            ],
            "expose_headers": ["Content-Length", "X-Total-Count", "X-Page-Count"]
        },
        "environment": settings.environment,
        "debug": settings.debug,
        "security_note": "⚠️ Этот эндпоинт доступен только в режиме разработки"
    }


@app.get("/debug/security", tags=["Debug"])
async def debug_security_stats(request: Request):
    """Отладочный эндпоинт для проверки статистики безопасности (только в dev режиме)"""
    # Защита: доступ только в режиме разработки
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")
    
    from .security_monitor import security_monitor
    
    stats = security_monitor.get_security_stats()
    
    return {
        "message": "Статистика безопасности",
        "stats": stats,
        "blocked_ips": list(security_monitor.blocked_ips.keys()) if security_monitor.blocked_ips else [],
        "suspicious_requests_count": sum(security_monitor.suspicious_requests.values()),
        "environment": settings.environment,
        "debug": settings.debug,
        "security_note": "⚠️ Этот эндпоинт доступен только в режиме разработки"
    }


# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(tables.router, prefix="/tables", tags=["Tables"])
app.include_router(locations.router, prefix="/locations", tags=["Locations"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(dishes.router, prefix="/dishes", tags=["Dishes"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(order_items.router, prefix="/orders", tags=["Order Items"])
app.include_router(ingredients.router, prefix="/ingredients", tags=["Ingredients"])
app.include_router(paymentmethod.router, prefix="/payment-methods", tags=["Payment Methods"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info"
    )
