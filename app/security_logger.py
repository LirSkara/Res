"""
QRes OS 4 - Security Logger
Специализированный логгер для событий безопасности
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Создаем директорию для логов безопасности
SECURITY_LOGS_DIR = Path(__file__).resolve().parent.parent / "logs" / "security"
SECURITY_LOGS_DIR.mkdir(parents=True, exist_ok=True)


class SecurityLogger:
    """Класс для логирования событий безопасности"""
    
    def __init__(self):
        # Настройка логгера безопасности
        self.logger = logging.getLogger("qres_security")
        self.logger.setLevel(logging.INFO)
        
        # Предотвращаем дублирование обработчиков
        if not self.logger.handlers:
            # Файловый хендлер для событий безопасности
            security_file_handler = logging.FileHandler(
                SECURITY_LOGS_DIR / "security_events.log", 
                encoding='utf-8'
            )
            
            security_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] SECURITY: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            security_file_handler.setFormatter(security_formatter)
            self.logger.addHandler(security_file_handler)
            
            # JSON хендлер для структурированных логов
            json_handler = logging.FileHandler(
                SECURITY_LOGS_DIR / "security_events.json", 
                encoding='utf-8'
            )
            json_handler.setFormatter(logging.Formatter('%(message)s'))
            
            # Создаем отдельный логгер для JSON
            self.json_logger = logging.getLogger("qres_security_json")
            self.json_logger.setLevel(logging.INFO)
            if not self.json_logger.handlers:
                self.json_logger.addHandler(json_handler)
        else:
            # Если логгер уже настроен, находим JSON логгер
            self.json_logger = logging.getLogger("qres_security_json")
    
    def _log_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None, level: int = logging.INFO):
        """Внутренний метод для логирования событий"""
        # Логируем в обычный лог
        self.logger.log(level, message)
        
        # Создаем структурированную запись для JSON
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "details": details or {}
        }
        
        # Логируем в JSON формат
        try:
            self.json_logger.info(json.dumps(event_data, ensure_ascii=False, default=str))
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении события в JSON: {e}")
    
    def log_failed_login(self, ip: str, username: str, user_agent: str = "unknown"):
        """Логирование неудачной попытки входа"""
        message = f"Failed login attempt - IP: {ip}, Username: {username}"
        details = {
            "ip": ip,
            "username": username,
            "user_agent": user_agent,
            "action": "failed_login"
        }
        self._log_event("FAILED_LOGIN", message, details, logging.WARNING)
    
    def log_successful_login(self, ip: str, username: str, role: str, user_agent: str = "unknown"):
        """Логирование успешного входа"""
        message = f"Successful login - IP: {ip}, Username: {username}, Role: {role}"
        details = {
            "ip": ip,
            "username": username,
            "role": role,
            "user_agent": user_agent,
            "action": "successful_login"
        }
        self._log_event("SUCCESSFUL_LOGIN", message, details, logging.INFO)
    
    def log_logout(self, ip: str, username: str, user_agent: str = "unknown"):
        """Логирование выхода из системы"""
        message = f"User logout - IP: {ip}, Username: {username}"
        details = {
            "ip": ip,
            "username": username,
            "user_agent": user_agent,
            "action": "logout"
        }
        self._log_event("LOGOUT", message, details, logging.INFO)
    
    def log_suspicious_activity(self, ip: str, url: str, method: str, user_agent: str = "unknown"):
        """Логирование подозрительной активности"""
        message = f"Suspicious activity detected - IP: {ip}, URL: {url}, Method: {method}"
        details = {
            "ip": ip,
            "url": url,
            "method": method,
            "user_agent": user_agent,
            "action": "suspicious_activity"
        }
        self._log_event("SUSPICIOUS_ACTIVITY", message, details, logging.WARNING)
    
    def log_rate_limit_exceeded(self, ip: str, request_count: int, user_agent: str = "unknown"):
        """Логирование превышения лимита запросов"""
        message = f"Rate limit exceeded - IP: {ip}, Requests: {request_count}"
        details = {
            "ip": ip,
            "request_count": request_count,
            "user_agent": user_agent,
            "action": "rate_limit_exceeded"
        }
        self._log_event("RATE_LIMIT_EXCEEDED", message, details, logging.WARNING)
    
    def log_ip_blocked(self, ip: str, reason: str, duration: int = 3600):
        """Логирование блокировки IP"""
        message = f"IP blocked - IP: {ip}, Reason: {reason}, Duration: {duration}s"
        details = {
            "ip": ip,
            "reason": reason,
            "duration": duration,
            "action": "ip_blocked"
        }
        self._log_event("IP_BLOCKED", message, details, logging.WARNING)
    
    def log_ip_unblocked(self, ip: str, reason: str = "manual"):
        """Логирование разблокировки IP"""
        message = f"IP unblocked - IP: {ip}, Reason: {reason}"
        details = {
            "ip": ip,
            "reason": reason,
            "action": "ip_unblocked"
        }
        self._log_event("IP_UNBLOCKED", message, details, logging.INFO)
    
    def log_security_violation(self, ip: str, violation_type: str, details: Dict[str, Any]):
        """Логирование нарушения безопасности"""
        message = f"Security violation - IP: {ip}, Type: {violation_type}"
        violation_details = {
            "ip": ip,
            "violation_type": violation_type,
            "action": "security_violation",
            **details
        }
        self._log_event("SECURITY_VIOLATION", message, violation_details, logging.ERROR)


# Глобальный экземпляр логгера
security_logger = SecurityLogger()
