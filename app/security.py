"""
QRes OS 4 - Security Module
Модуль безопасности и защиты API
"""
import time
from typing import Dict, Optional, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import settings


class RateLimitExceeded(Exception):
    """Исключение, вызываемое при превышении лимита запросов"""
    pass


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware для защиты от DDoS-атак путем ограничения скорости запросов"""
    
    def __init__(
        self, 
        app: ASGIApp, 
        requests_limit: int = 100,
        time_window: int = 60,
        block_duration: int = 600,
        whitelist: Optional[list] = None
    ):
        """
        Инициализация middleware ограничения скорости запросов
        
        Args:
            app: ASGI-приложение
            requests_limit: Максимальное количество запросов в указанное время
            time_window: Временное окно в секундах (период отслеживания запросов)
            block_duration: Длительность блокировки в секундах при превышении лимита
            whitelist: Список IP-адресов, для которых ограничение не действует
        """
        super().__init__(app)
        self.requests_limit = requests_limit
        self.time_window = time_window
        self.block_duration = block_duration
        self.whitelist = whitelist or ["127.0.0.1", "::1", "localhost"]
        
        # Хранилище IP адресов и их запросов {ip: [(timestamp1, path1), (timestamp2, path2), ...]}
        self.request_records: Dict[str, list] = {}
        
        # Хранилище заблокированных IP {ip: block_until_timestamp}
        self.blocked_ips: Dict[str, float] = {}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Проверка и ограничение запросов от одного IP"""
        # Пропускаем проверку в режиме разработки, если настроено
        if settings.debug and settings.disable_rate_limit_in_debug:
            return await call_next(request)
            
        # Получаем IP-адрес клиента
        client_ip = request.client.host if request.client else "unknown"
        
        # Пропускаем доверенные IP-адреса
        if client_ip in self.whitelist:
            return await call_next(request)
            
        # Проверяем, заблокирован ли IP
        now = time.time()
        if client_ip in self.blocked_ips:
            # Если время блокировки истекло, разблокируем IP
            if now > self.blocked_ips[client_ip]:
                del self.blocked_ips[client_ip]
            else:
                # Возвращаем ошибку 429 Too Many Requests
                return Response(
                    content="Превышен лимит запросов. Попробуйте позже.",
                    status_code=429,
                    media_type="text/plain",
                    headers={"Retry-After": str(int(self.blocked_ips[client_ip] - now))}
                )
        
        # Обновляем и проверяем статистику запросов
        is_rate_limited, retry_after = self._update_request_counts(client_ip, request.url.path)
        
        if is_rate_limited:
            # Возвращаем ошибку 429 Too Many Requests
            return Response(
                content="Превышен лимит запросов. Попробуйте позже.",
                status_code=429,
                media_type="text/plain",
                headers={"Retry-After": str(retry_after)}
            )
            
        # Пропускаем запрос к следующему middleware или обработчику
        return await call_next(request)
    
    def _update_request_counts(self, client_ip: str, path: str) -> Tuple[bool, int]:
        """
        Обновляет счетчик запросов для IP и проверяет превышение лимита
        
        Args:
            client_ip: IP-адрес клиента
            path: Запрашиваемый путь
            
        Returns:
            Tuple[bool, int]: (превышен_ли_лимит, время_до_снятия_блокировки_в_секундах)
        """
        now = time.time()
        
        # Если IP нет в записях, добавляем его
        if client_ip not in self.request_records:
            self.request_records[client_ip] = []
            
        # Добавляем текущий запрос в историю запросов IP
        self.request_records[client_ip].append((now, path))
        
        # Удаляем старые записи, выходящие за временное окно
        time_limit = now - self.time_window
        self.request_records[client_ip] = [
            (t, p) for t, p in self.request_records[client_ip] if t >= time_limit
        ]
        
        # Проверяем количество запросов
        if len(self.request_records[client_ip]) > self.requests_limit:
            # Блокируем IP на указанное время
            block_until = now + self.block_duration
            self.blocked_ips[client_ip] = block_until
            
            # Очищаем записи запросов для этого IP
            self.request_records[client_ip] = []
            
            # Возвращаем информацию о блокировке
            return True, self.block_duration
            
        return False, 0
            

class SuspiciousRequestFilterMiddleware(BaseHTTPMiddleware):
    """Middleware для фильтрации подозрительных запросов"""
    
    # Подозрительные паттерны в URL и юзер-агентах
    SUSPICIOUS_URL_PATTERNS = [
        "/wp-", "/wordpress", "/wp-admin", "/wp-login", "/phpMyAdmin", 
        "/admin", "/administrator", "/login.php", "/.git", "/.env",
        "/config", "/backup", "/dump", "/db", "/database",
        "/shell", "/cmd", "/command", "/sql", "/phpmyadmin"
    ]
    
    SUSPICIOUS_USER_AGENTS = [
        "zgrab", "gobuster", "nikto", "nmap", "masscan", "python-requests/",
        "sqlmap", "scanbot", "bot", "crawler", "spider", "dirbuster", "dirb",
        "wpscan", "joomla", "drupal"
    ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Проверяет запрос на подозрительные признаки"""
        # Получаем путь запроса и юзер-агент
        path = request.url.path.lower()
        user_agent = request.headers.get("user-agent", "").lower()
        client_ip = request.client.host if request.client else "unknown"
        
        # Проверяем путь на подозрительные паттерны
        for pattern in self.SUSPICIOUS_URL_PATTERNS:
            if pattern in path:
                # Логируем подозрительный запрос
                self._log_suspicious_request(client_ip, path, user_agent, "suspicious_path")
                # Возвращаем ошибку 404
                return Response(
                    content="Не найдено",
                    status_code=404,
                    media_type="text/plain"
                )
        
        # Проверяем юзер-агент на подозрительные паттерны
        for agent in self.SUSPICIOUS_USER_AGENTS:
            if agent in user_agent:
                # Логируем подозрительный запрос
                self._log_suspicious_request(client_ip, path, user_agent, "suspicious_agent")
                # Возвращаем ошибку 403
                return Response(
                    content="Запрещено",
                    status_code=403,
                    media_type="text/plain"
                )
                
        # Если проверки пройдены, пропускаем запрос дальше
        return await call_next(request)
    
    def _log_suspicious_request(self, ip: str, path: str, user_agent: str, reason: str) -> None:
        """Логирование подозрительных запросов"""
        from .logger import api_logger
        import logging
        
        message = f"⚠️ SUSPICIOUS REQUEST | {reason} | IP: {ip} | PATH: {path} | AGENT: {user_agent}"
        api_logger.log(logging.WARNING, message)


def setup_security(app: ASGIApp) -> None:
    """
    Настройка всех компонентов безопасности для приложения
    
    Args:
        app: FastAPI приложение
    """
    # Сначала добавляем фильтрацию подозрительных запросов
    app.add_middleware(SuspiciousRequestFilterMiddleware)
    
    # Затем добавляем middleware для защиты от DDoS-атак
    app.add_middleware(
        RateLimiterMiddleware,
        requests_limit=settings.rate_limit_max_requests,  # Максимальное количество запросов
        time_window=settings.rate_limit_window,           # Временное окно в секундах
        block_duration=settings.rate_limit_block_duration # Длительность блокировки в секундах
    )
