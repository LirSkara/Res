"""
QRes OS 4 - API Request Logger
Модуль для логирования всех API запросов
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message

from .config import settings
from .services.auth import AuthService

# Создаем папку для логов, если ее нет
BASE_DIR = Path(__file__).resolve().parent.parent  # Путь к корню проекта
LOGS_DIR = BASE_DIR / "logs"  # Абсолютный путь к директории с логами
LOGS_DIR.mkdir(exist_ok=True)

# Настраиваем логгер для API запросов
api_logger = logging.getLogger("api_requests")
api_logger.setLevel(logging.INFO)

# Форматтер для красивого отображения логов
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Хендлер для записи в файл
log_file = LOGS_DIR / f"api_requests.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(formatter)
api_logger.addHandler(file_handler)

# Хендлер для отображения в консоли при разработке
if settings.debug:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    api_logger.addHandler(console_handler)


# CRUD операции для более понятной маркировки в логах
CRUD_OPERATIONS = {
    "GET": "🔍 READ",
    "POST": "➕ CREATE",
    "PUT": "🔄 UPDATE",
    "PATCH": "🔧 PARTIAL_UPDATE",
    "DELETE": "❌ DELETE",
    "OPTIONS": "📋 OPTIONS",
    "HEAD": "📝 HEAD"
}

# Цвета для консоли для разных методов (не влияют на файл логов)
METHOD_COLORS = {
    "GET": "\033[94m",     # Blue
    "POST": "\033[92m",    # Green
    "PUT": "\033[93m",     # Yellow
    "PATCH": "\033[96m",   # Cyan
    "DELETE": "\033[91m",  # Red
    "OPTIONS": "\033[95m", # Purple
    "HEAD": "\033[97m",    # White
    "RESET": "\033[0m"     # Reset
}


class APIRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования всех API запросов"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Обработка запроса и логирование"""
        # Получаем время начала запроса
        request_time = datetime.now()
        
        # Получаем информацию о запросе
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Выполняем запрос без попыток считать тело запроса
        response = await call_next(request)
        
        # Вычисляем время выполнения запроса
        response_time = (datetime.now() - request_time).total_seconds() * 1000
        
        # Получаем информацию о текущем пользователе из запроса
        # По JWT токену можно определить пользователя
        user_info = "Анонимный"
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                token_data = AuthService.verify_token(token)
                if token_data:
                    user_info = f"{token_data.sub} (ID: {token_data.user_id}, роль: {token_data.role})"
            except Exception:
                pass
        
        # Формируем строку лога
        operation = CRUD_OPERATIONS.get(method, method)
        
        # Добавляем цвет для консоли
        color_start = METHOD_COLORS.get(method, "")
        color_reset = METHOD_COLORS["RESET"]
        
        # Основная информация для лога
        log_info = {
            "timestamp": request_time.isoformat(),
            "operation": operation,
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "response_time_ms": round(response_time, 2),
            "user": user_info,
            "client_ip": client_ip,
            "query_params": query_params if query_params else None,
            "request_body": None,  # Убрали чтение тела запроса
            "user_agent": user_agent
        }
        
        # Определяем уровень логирования в зависимости от кода ответа
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Создаем сообщение для лога
        log_message = f"{color_start}{operation} | {method} {path} | {response.status_code} | {round(response_time, 2)}ms | {user_info}{color_reset}"
        
        # Логируем информацию о запросе
        api_logger.log(log_level, log_message, extra={"api_request": log_info})
        
        # Также сохраняем более подробную информацию в JSON-лог
        self._log_to_json(log_info)
        
        return response
    
    def _log_to_json(self, log_info: Dict[str, Any]) -> None:
        """Логирование в JSON-файл для более удобного анализа"""
        try:
            # Получаем дату для организации логов по дням
            today = datetime.now().strftime("%Y-%m-%d")
            json_log_file = LOGS_DIR / f"api_requests_{today}.json"
            
            # Создаем файл, если его нет
            if not json_log_file.exists():
                with open(json_log_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
            
            # Загружаем текущие логи
            with open(json_log_file, "r", encoding="utf-8") as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
            
            # Добавляем новый лог
            logs.append(log_info)
            
            # Сохраняем обновленные логи
            with open(json_log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            api_logger.error(f"Ошибка при записи JSON-лога: {e}")


def setup_request_logging(app: ASGIApp) -> None:
    """Добавление middleware логирования к приложению FastAPI
    
    Добавляет APIRequestLoggingMiddleware к приложению FastAPI.
    Все запросы будут логироваться в файлы:
    - logs/api_requests.log - общий лог всех запросов
    - logs/api_requests_YYYY-MM-DD.json - детальный лог запросов по дням
    """
    app.add_middleware(APIRequestLoggingMiddleware)
    api_logger.info("🔄 API Request Logging Middleware активирован")
