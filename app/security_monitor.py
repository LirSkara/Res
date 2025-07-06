"""
QRes OS 4 - Security Monitoring
Мониторинг безопасности и детекция аномалий
"""
import time
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import Request, HTTPException
from .security_logger import security_logger


class SecurityMonitor:
    """Монитор безопасности для детекции аномалий"""
    
    def __init__(self):
        # Счетчики для разных типов активности
        self.failed_logins = defaultdict(deque)  # IP -> список времен неудачных входов
        self.request_counts = defaultdict(deque)  # IP -> список времен запросов
        self.suspicious_requests = defaultdict(int)  # IP -> количество подозрительных запросов
        self.blocked_ips = {}  # IP -> время блокировки
        
        # Настройки
        self.max_failed_logins = 5  # Максимум неудачных попыток входа
        self.login_window = 300  # Окно в секундах (5 минут)
        self.max_requests_per_minute = 60  # Максимум запросов в минуту
        self.block_duration = 3600  # Время блокировки в секундах (1 час)
        self.suspicious_threshold = 10  # Порог подозрительной активности
        
        # Паттерны подозрительной активности
        self.suspicious_patterns = [
            'admin', 'administrator', 'root', 'test', 'guest',
            '.env', '.git', 'config', 'backup', 'database',
            'phpmyadmin', 'wp-admin', 'wp-login',
            '../', '..\\', '/etc/', '/var/', '/usr/',
            '<script', 'javascript:', 'eval(', 'exec(',
            'union select', 'drop table', 'delete from'
        ]
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Проверка, заблокирован ли IP"""
        if ip in self.blocked_ips:
            if time.time() - self.blocked_ips[ip] < self.block_duration:
                return True
            else:
                # Снимаем блокировку
                del self.blocked_ips[ip]
        return False
    
    def record_failed_login(self, ip: str, username: str) -> bool:
        """Записывает неудачную попытку входа"""
        current_time = time.time()
        
        # Очищаем старые записи
        while (self.failed_logins[ip] and 
               current_time - self.failed_logins[ip][0] > self.login_window):
            self.failed_logins[ip].popleft()
        
        # Добавляем новую неудачную попытку
        self.failed_logins[ip].append(current_time)
        
        # Логируем событие
        security_logger.log_failed_login(ip, username)
        
        # Проверяем на превышение лимита
        if len(self.failed_logins[ip]) >= self.max_failed_logins:
            self.block_ip(ip, "Too many failed login attempts")
            return True
        
        return False
    
    def record_request(self, request: Request) -> bool:
        """Записывает запрос и проверяет на аномалии"""
        ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Проверяем, заблокирован ли IP
        if self.is_ip_blocked(ip):
            raise HTTPException(status_code=429, detail="IP temporarily blocked")
        
        # Очищаем старые записи запросов
        while (self.request_counts[ip] and 
               current_time - self.request_counts[ip][0] > 60):
            self.request_counts[ip].popleft()
        
        # Добавляем новый запрос
        self.request_counts[ip].append(current_time)
        
        # Проверяем превышение лимита запросов
        if len(self.request_counts[ip]) > self.max_requests_per_minute:
            self.block_ip(ip, "Too many requests per minute")
            security_logger.log_rate_limit_exceeded(ip, len(self.request_counts[ip]))
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Проверяем на подозрительную активность
        if self.is_suspicious_request(request):
            self.suspicious_requests[ip] += 1
            security_logger.log_suspicious_activity(ip, str(request.url), request.method)
            
            if self.suspicious_requests[ip] >= self.suspicious_threshold:
                self.block_ip(ip, "Suspicious activity detected")
                return True
        
        return False
    
    def is_suspicious_request(self, request: Request) -> bool:
        """Проверяет запрос на подозрительную активность"""
        url_path = str(request.url.path).lower()
        query_params = str(request.url.query).lower()
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Проверяем URL и параметры
        for pattern in self.suspicious_patterns:
            if pattern in url_path or pattern in query_params:
                return True
        
        # Проверяем подозрительные User-Agent
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zap',
            'burp', 'w3af', 'gobuster', 'dirb', 'dirbuster'
        ]
        
        for agent in suspicious_agents:
            if agent in user_agent:
                return True
        
        # Проверяем отсутствие User-Agent (боты)
        if not request.headers.get("user-agent"):
            return True
        
        return False
    
    def block_ip(self, ip: str, reason: str):
        """Блокирует IP адрес"""
        self.blocked_ips[ip] = time.time()
        security_logger.log_ip_blocked(ip, reason)
    
    def get_client_ip(self, request: Request) -> str:
        """Получает реальный IP клиента с учетом прокси"""
        # Проверяем заголовки от прокси/балансировщика
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Берем первый IP (реальный клиент)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback на стандартный способ
        return request.client.host if request.client else "unknown"
    
    def get_security_stats(self) -> Dict:
        """Возвращает статистику безопасности"""
        return {
            "blocked_ips": len(self.blocked_ips),
            "failed_login_attempts": sum(len(attempts) for attempts in self.failed_logins.values()),
            "suspicious_requests": sum(self.suspicious_requests.values()),
            "active_rate_limits": len([ip for ip, requests in self.request_counts.items() if len(requests) > 30])
        }
    
    def unblock_ip(self, ip: str) -> bool:
        """Разблокирует IP адрес (для административного интерфейса)"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            security_logger.log_ip_unblocked(ip)
            return True
        return False
    
    def cleanup_old_data(self):
        """Очистка старых данных (вызывается периодически)"""
        current_time = time.time()
        
        # Очищаем старые записи неудачных входов
        for ip in list(self.failed_logins.keys()):
            while (self.failed_logins[ip] and 
                   current_time - self.failed_logins[ip][0] > self.login_window):
                self.failed_logins[ip].popleft()
            
            if not self.failed_logins[ip]:
                del self.failed_logins[ip]
        
        # Очищаем старые записи запросов
        for ip in list(self.request_counts.keys()):
            while (self.request_counts[ip] and 
                   current_time - self.request_counts[ip][0] > 60):
                self.request_counts[ip].popleft()
            
            if not self.request_counts[ip]:
                del self.request_counts[ip]
        
        # Очищаем старые блокировки
        for ip in list(self.blocked_ips.keys()):
            if current_time - self.blocked_ips[ip] > self.block_duration:
                del self.blocked_ips[ip]
        
        # Сбрасываем счетчики подозрительных запросов (каждый час)
        if int(current_time) % 3600 == 0:
            self.suspicious_requests.clear()


# Глобальный экземпляр монитора
security_monitor = SecurityMonitor()


async def start_security_monitor_cleanup():
    """Запуск фоновой задачи очистки данных мониторинга"""
    while True:
        await asyncio.sleep(300)  # Каждые 5 минут
        security_monitor.cleanup_old_data()
