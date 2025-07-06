"""
QRes OS 4 - Main Application
Точка входа в приложение FastAPI
"""
import time
import traceback
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import init_db, close_db
from .schemas import ErrorResponse, HealthCheck
from .logger import setup_request_logging  # Импорт логгера
from .security import setup_security  # Импорт компонентов безопасности

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
    print("🚀 QRes OS 4 starting up...")
    await init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("🛑 QRes OS 4 shutting down...")
    await close_db()
    print("✅ Database connection closed")


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Используем настройки из конфига
    # allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Ограничиваем методы
    allow_headers=["*"],  # Authorization, Content-Type, etc.
    expose_headers=["*"]  # Разрешаем доступ ко всем заголовкам ответа
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # В продакшене настроить конкретные хосты
)

# Подключение middleware логирования API-запросов
setup_request_logging(app)

# Подключение компонентов безопасности (защита от DDoS-атак)
setup_security(app)


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
