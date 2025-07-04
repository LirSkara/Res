"""
QRes OS 4 - Main Application
Точка входа в приложение FastAPI
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .database import init_db, close_db
from .schemas import ErrorResponse, HealthCheck

# Импорт роутеров
from .routers import (
    auth, users, tables, locations, categories, dishes, 
    orders, order_items, ingredients, 
    paymentmethod, websocket
)


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
    allow_origins=["*"],  # Разрешаем все origins для разработки
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],  # Authorization, Content-Type, etc.
    expose_headers=["*"]  # Разрешаем доступ ко всем заголовкам ответа
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # В продакшене настроить конкретные хосты
)


# Обработчики ошибок
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Обработка HTTP ошибок"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}"
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Обработка ошибок валидации"""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            message="Ошибка валидации данных",
            error_code="VALIDATION_ERROR",
            details={"errors": exc.errors()}
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработка общих ошибок"""
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
